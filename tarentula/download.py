import json
import shutil
import sys
from os import makedirs
from os.path import join, dirname, basename, exists
from time import sleep
from requests.exceptions import HTTPError, ConnectionError
from rich.progress import Progress
from urllib3.exceptions import ProtocolError

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
                 sort_by: str = '_id',
                 order_by: str = 'asc',
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
            sys.exit()

    @property
    def no_progressbar(self):
        return not self.progressbar

    def sleep(self):
        sleep(self.throttle / 1000)

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

    def download_raw_file(self, document):
        id = document.get('_id')
        routing = document.get('_routing', id)
        # Skip raw file
        if not self.raw_file:
            return None
        # Skip existing
        if self.once and self.raw_file_exists(document):
            logger.info('Skipping existing document %s', document.get('_id'))
            return None
        # Skip non-downloadable file
        if document.get('_source', {}).get('type', None) != 'Document':
            logger.warning('Not a raw document. Skipping %s', id)
            return None
        logger.info('Downloading raw file %s', id)
        document_file_stream = self.datashare_client.download(self.datashare_project, id, routing)
        document_file_stream.raw.decode_content = True
        document_file_stream.raise_for_status()
        self.save_raw_file(document, document_file_stream)
        return None

    def raw_file_exists(self, document):
        raw_file_path = self.raw_file_path(document)
        return exists(raw_file_path)

    def save_raw_file(self, document, document_file_stream):
        file_path = self.raw_file_path(document)
        with open(file_path, 'wb') as file:
            shutil.copyfileobj(document_file_stream.raw, file)

    def save_indexed_document(self, indexed_document):
        file_path = self.indexed_document_path(indexed_document)
        with open(file_path, 'w') as file:
            json.dump(indexed_document, file)

    def start(self):
        count = self.log_matches()
        desc = f'Downloading {count} document(s)'
        source = ["path", "parentDocument", "type"] + str(self.source).split(',')
        try:
            with Progress(disable=self.no_progressbar) as progress:
                task = progress.add_task(desc, total=count)
                for document in self.datashare_client.scan_or_query_all(self.datashare_project, source, self.sort_by,
                                                                        self.order_by, self.scroll, self.query_body,
                                                                        self.from_, self.limit, self.size):
                    try:
                        self.download_raw_file(document)
                        self.save_indexed_document(document)
                        logger.info('Processed document %s', document.get('_id'))
                    except HTTPError:
                        logger.error('Unable to download document %s', document.get('_id'), exc_info=self.traceback)
                    progress.advance(task)
                    self.sleep()
        except ProtocolError:
            logger.error('Exception while downloading documents', exc_info=self.traceback)
