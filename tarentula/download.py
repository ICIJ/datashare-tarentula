import asyncio
import json
import sys
from os import makedirs
from os.path import join, dirname, basename, exists

import click
from requests.exceptions import ConnectionError
from rich.progress import Progress

from tarentula.async_client import AsyncDatashareClient
from tarentula.command import Command
from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class Download(Command):
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 destination_directory: str = './tmp',
                 query: str = '*',
                 throttle: int = 0,
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 path_format: str = '{id_2b}/{id_4b}/{id}',
                 scroll: str = None,
                 source: str = None,
                 limit: int = 0,
                 from_: int = 0,
                 size: int = 0,
                 sort_by: str = '_score',
                 order_by: str = 'desc',
                 concurrency: int = 5,
                 once: bool = False,
                 traceback: bool = False,
                 progressbar: bool = True,
                 raw_file: bool = True,
                 type: str = 'Document'):
        super().__init__(query, type)
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.destination_directory = destination_directory
        self.throttle = throttle
        self.cookies_string = cookies
        self.apikey = apikey
        self.path_format = path_format
        self.concurrency = concurrency
        self.once = once
        self.traceback = traceback
        self.progressbar = progressbar
        self.raw_file = raw_file
        self.source = source
        self.scroll = scroll
        self.limit = limit
        self.from_ = from_
        self.size = size
        self.sort_by = sort_by
        self.order_by = order_by
        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            sys.exit(1)

    @property
    def no_progressbar(self):
        return not self.progressbar

    def document_file_options(self, document):
        return {
            "id": document.get('_id'),
            "id_2b": document.get('_id')[0:2],
            "id_4b": document.get('_id')[2:4],
            "project": self.datashare_project,
            "basename": basename(document.get('_source', {}).get("path", '')),
            "parentDocument": document.get('_source', {}).get('parentDocument', None)
        }

    def raw_file_path(self, document, parents=True):
        formatted_path = self.path_format.format(**self.document_file_options(document))
        file_path = join(self.destination_directory, formatted_path)
        if parents:
            parents_path = dirname(file_path)
            makedirs(parents_path, exist_ok=True)
        return file_path

    def indexed_document_path(self, document, parents=True):
        formatted_path = self.path_format.format(**self.document_file_options(document))
        formatted_path = '.'.join((formatted_path, 'json'))
        file_path = join(self.destination_directory, formatted_path)
        if parents:
            parents_path = dirname(file_path)
            makedirs(parents_path, exist_ok=True)
        return file_path

    def count_matches(self):
        index = self.datashare_project
        total_matched = self.datashare_client \
            .count(index=index, query=self.query_body) \
            .get('count')
        total_matched = total_matched - self.from_ if total_matched >= self.from_ \
            else total_matched
        total_matched = total_matched if (self.limit == 0) or \
                                         (self.limit > total_matched) \
            else self.limit
        return total_matched

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s', count, index)
        return count

    def raw_file_exists(self, document):
        raw_file_path = self.raw_file_path(document)
        return exists(raw_file_path)

    def save_indexed_document(self, indexed_document):
        file_path = self.indexed_document_path(indexed_document)
        with open(file_path, 'w') as file:
            json.dump(indexed_document, file)

    def start(self):
        if self.scroll is not None:
            message = '--scroll is deprecated and ignored; pagination uses search_after.'
            logger.warning(message)
            # The stdout log handler defaults to ERROR level, which would swallow this
            # WARNING-level message. Deprecation notices are user-facing regardless of
            # the configured log verbosity, so also echo it directly to stderr (it is a
            # diagnostic notice, not primary output).
            click.echo(f'Warning: {message}', err=True)
        asyncio.run(self._run())

    async def _run(self):
        count = self.log_matches()
        desc = f'Downloading {count} document(s)'
        extra = self.source.split(',') if self.source else []
        source = ["path", "parentDocument", "type"] + extra
        queue = asyncio.Queue(maxsize=self.concurrency * 2)
        async with AsyncDatashareClient(self.datashare_client, concurrency=self.concurrency) as client:
            with Progress(disable=self.no_progressbar) as progress:
                task = progress.add_task(desc, total=count)

                async def worker():
                    while True:
                        document = await queue.get()
                        if document is None:
                            queue.task_done()
                            return
                        try:
                            await self._download_raw_file(client, document)
                            self.save_indexed_document(document)
                            logger.info('Processed document %s', document.get('_id'))
                        # Catch Exception (not BaseException) so any per-document failure logs and
                        # continues without killing the worker: a dead worker would let the producer
                        # block forever on the bounded queue. asyncio.CancelledError (a BaseException)
                        # still propagates, so the producer-error cancellation path below keeps working.
                        except Exception:
                            logger.error('Unable to download document %s',
                                         document.get('_id'), exc_info=self.traceback)
                        finally:
                            progress.advance(task)
                            if self.throttle:
                                await asyncio.sleep(self.throttle / 1000)
                            queue.task_done()

                workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]
                try:
                    async for document in client.search_after_scan(
                            index=self.datashare_project, query=self.query_body,
                            source=source, sort_by=self.sort_by, order_by=self.order_by,
                            size=self.size or 1000, limit=self.limit, from_=self.from_):
                        await queue.put(document)
                    for _ in workers:
                        await queue.put(None)
                    await asyncio.gather(*workers)
                except BaseException:
                    for w in workers:
                        w.cancel()
                    await asyncio.gather(*workers, return_exceptions=True)
                    raise

    async def _download_raw_file(self, client, document):
        doc_id = document.get('_id')
        routing = document.get('_routing', doc_id)
        if not self.raw_file:
            return
        if self.once and self.raw_file_exists(document):
            logger.info('Skipping existing document %s', doc_id)
            return
        if document.get('_source', {}).get('type', None) != self.type:
            logger.warning('Not a raw document. Skipping %s', doc_id)
            return
        logger.info('Downloading raw file %s', doc_id)
        dest_path = self.raw_file_path(document)
        await client.stream_download(self.datashare_project, doc_id, routing, dest_path)
