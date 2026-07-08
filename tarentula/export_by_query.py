import asyncio
import csv
import sys
from collections import OrderedDict
from contextlib import contextmanager

import aiohttp
import click
from rich.progress import Progress

from tarentula.async_client import AsyncDatashareClient
from tarentula.command import Command
from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class ExportByQuery(Command):
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 output_file: str = 'tarentula_documents.csv',
                 query: str = '*',
                 throttle: int = 0,
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 scroll: str = None,
                 source: str = 'contentType,contentLength:0,extractionDate,path',
                 size: int = 1000,
                 from_: int = 0,
                 limit: int = 0,
                 sort_by: str = '_score',
                 order_by: str = 'desc',
                 traceback: bool = False,
                 progressbar: bool = True,
                 type: str = 'Document',
                 query_field: bool = True):
        super().__init__(query, type)
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.output_file = output_file
        self.throttle = throttle
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.progressbar = progressbar
        self.scroll = scroll
        self.source = source
        self.size = size
        self.from_ = from_
        self.limit = limit
        self.sort_by = sort_by
        self.order_by = order_by
        self.query_field = query_field
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

    @property
    def source_fields(self):
        return [self.source_field_params(f) for f in self.source.split(',')]

    @property
    def source_fields_names(self):
        return [field.pop(0) for field in self.source_fields]

    @property
    def csv_fields_names(self):
        names = self.default_csv_fields_names
        names += self.source_fields_names
        # Remove duplicated values while preserving order
        return list(OrderedDict.fromkeys(names))

    @property
    def default_csv_fields_names(self):
        names = ['documentUrl', 'documentId', 'rootId', 'documentNumber']
        if self.query_field:
            names.insert(0, 'query')
        return names

    def source_field_params(self, field):
        field_params = field.strip().split(':')
        field_name = field_params[0]
        field_default = field_params[1] if len(field_params) > 1 else ''
        return [field_name, field_default]

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

    def document_default_values(self, document, number):
        index = self.datashare_project
        id = document.get('_id')
        routing = document.get('_routing', id)
        url = self.datashare_client.document_url(index, id, routing)
        values = {'documentUrl': url, 'documentId': id, 'rootId': routing, 'documentNumber': number}
        if self.query_field:
            return {'query': self.query, **values}
        return values

    def document_source_values(self, document):
        source_values = {}
        source = document.get('_source', {})
        for [name, default] in self.source_fields:
            # Get the nested value for `name` (it can be a path, ie: metadata.tika_metadata_author)
            source_values[name] = source
            for key in name.split('.'):
                try:
                    source_values[name] = source_values[name][key]
                except (KeyError, TypeError):
                    source_values[name] = default
        return source_values

    def save_indexed_document(self, csvwriter, document, document_number):
        default_values = self.document_default_values(document, document_number)
        source_values = self.document_source_values(document)
        csvwriter.writerow({**default_values, **source_values})

    @contextmanager
    def create_csv_file(self):
        with open(self.output_file, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file,
                                    fieldnames=self.csv_fields_names,
                                    quoting=csv.QUOTE_ALL)
            writer.writeheader()
            yield writer

    def start(self):
        if self.scroll is not None:
            message = '--scroll is deprecated and ignored; pagination uses search_after.'
            logger.warning(message)
            # The stdout log handler defaults to ERROR level, which would swallow this
            # WARNING-level message. Deprecation notices are user-facing regardless of
            # the configured log verbosity, so also echo it directly to stderr (it is a
            # diagnostic notice, not primary output).
            click.echo(f'Warning: {message}', err=True)
        try:
            asyncio.run(self._run())
        # KeyboardInterrupt/SystemExit are BaseException, not Exception, so they are never
        # caught here and always propagate. RuntimeError is raised by search_after_scan on a
        # non-2xx status; aiohttp.ClientError covers connection/timeout failures that exhaust
        # their retries. Either way, log cleanly instead of letting a raw traceback escape.
        except (RuntimeError, aiohttp.ClientError) as exc:
            logger.error('Export failed: %s', exc, exc_info=self.traceback)
            sys.exit(1)

    async def _run(self):
        count = self.log_matches()
        desc = f'Exporting {count} document(s)'
        async with AsyncDatashareClient(self.datashare_client) as client:
            with Progress(disable=self.no_progressbar) as progress:
                task = progress.add_task(desc, total=count)
                with self.create_csv_file() as csvwriter:
                    number = 0
                    async for document in client.search_after_scan(
                            index=self.datashare_project, query=self.query_body,
                            source=self.source_fields_names, sort_by=self.sort_by,
                            order_by=self.order_by, size=self.size or 1000, limit=self.limit,
                            from_=self.from_, use_pit=True):
                        try:
                            self.save_indexed_document(csvwriter, document, number)
                            logger.info('Saved document %s', document.get('_id', None))
                        # Export makes no per-document HTTP call (unlike download's raw-file
                        # fetch), so a narrow HTTPError catch would be dead code. Broadly
                        # catch Exception (not BaseException) so a bad document logs and the
                        # export continues; a search/producer error (e.g. RuntimeError from
                        # search_after_scan) is raised by the async for itself, outside this
                        # try, and correctly aborts the export.
                        except Exception:
                            logger.error('Unable to export document %s',
                                         document.get('_id', None), exc_info=self.traceback)
                        number += 1
                        progress.advance(task)
                logger.info('Written documents metadata in %s', self.output_file)
