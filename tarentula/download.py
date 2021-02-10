import json
import shutil
import sys
from os import makedirs
from os.path import join, dirname, basename, exists
from time import sleep

from requests.exceptions import HTTPError, ConnectionError
from tqdm import tqdm
from urllib3.exceptions import ProtocolError

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class Download:
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
                 once: bool = False,
                 traceback: bool = False,
                 progressbar: bool = True,
                 raw_file: bool = True,
                 source: str = None,
                 type: str = 'Document'):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
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
        self.type = type
        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            exit()

    @property
    def query_body(self):
        if self.query.startswith('@'):
            return self.query_body_from_file
        else:
            return self.query_body_from_string

    @property
    def query_body_from_string(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "type": self.type
                            }
                        },
                        {
                            "query_string": {
                                "query": self.query
                            }
                        }
                    ]
                }
            }
        }

    @property
    def query_body_from_file(self):
        with open(self.query[1:]) as json_file:
            query_body = json.load(json_file)
        return query_body

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
        return self.datashare_client.count(index=index, query=self.query_body).get('count')

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s' % (count, index))
        return count

    def scan_or_query_all(self):
        index = self.datashare_project
        source = ["path", "parentDocument", "type"] + str(self.source).split(',')
        if self.scroll is None:
            logger.info('Searching document(s) metadata in %s' % index)
            return self.datashare_client.query_all(index=index, query=self.query_body, source=source)
        else:
            logger.info('Scrolling over document(s) metadata in %s' % index)
            return self.datashare_client.scan_all(index=index, query=self.query_body, source=source, scroll=self.scroll)

    def download_raw_file(self, document):
        id = document.get('_id')
        routing = document.get('_routing', id)
        # Skip raw file
        if not self.raw_file:
            return
        # Skip existing
        if self.once and self.raw_file_exists(document):
            return logger.info('Skipping existing document %s' % document.get('_id'))
        # Skip non-downloadable file
        if document.get('_source', {}).get('type', None) != 'Document':
            return logger.warning('Not a raw document. Skipping %s' % id)
        logger.info('Downloading raw file %s' % id)
        document_file_stream = self.datashare_client.download(self.datashare_project, id, routing)
        document_file_stream.raw.decode_content = True
        document_file_stream.raise_for_status()
        self.save_raw_file(document, document_file_stream)

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
        try:
            documents = self.scan_or_query_all()
            pbar = tqdm(documents, total=count, desc="Downloading %s document(s)" % count, file=sys.stdout,
                        disable=self.no_progressbar)
            for document in pbar:
                try:
                    self.download_raw_file(document)
                    self.save_indexed_document(document)
                    logger.info('Processed document %s' % document.get('_id'))
                    self.sleep()
                except HTTPError:
                    logger.error('Unable to download document %s' % document.get('_id'), exc_info=self.traceback)
        except ProtocolError:
            logger.error('Exception while downloading documents', exc_info=self.traceback)
