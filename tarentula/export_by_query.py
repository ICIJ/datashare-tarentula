import csv
import json
import sys

from contextlib import contextmanager
from requests.exceptions import HTTPError
from urllib3.exceptions import ProtocolError
from tqdm import tqdm
from time import sleep

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class ExportByQuery:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 output_file: str = 'tarentula_documents.csv',
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
        self.output_file = output_file
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
        if self.scroll is None:
            logger.info('Searching document(s) metadata in %s' % index)
            return self.datashare_client.query_all(index=index, query=self.query_body)
        else:
            logger.info('Scrolling over document(s) metadata in %s' % index)
            return self.datashare_client.scan_all(index=index, query=self.query_body, scroll=self.scroll)

    def save_indexed_document(self, csvwriter, document, index):
        document_id = document.get('_id')
        document_routing = document.get('_routing', document_id)
        document_url = self.datashare_url + '/#/d/' + self.datashare_project + '/' + document_id + '/' + \
                       document_routing
        source = document.get('_source', {})
        content_type = source.get('contentType', '')
        content_length = source.get('contentLength', 0)
        document_path = source.get('path', '')
        creation_date = source.get('extractionDate', '')
        document_number = index
        document_as_dict = {'query': self.query, 'documentUrl': document_url, 'documentId': document_id,
                            'rootId': document_routing, 'contentType': content_type, 'contentLength': content_length,
                            'documentPath': document_path, 'creationDate': creation_date,
                            'documentNumber': document_number}
        csvwriter.writerow(document_as_dict)

    @contextmanager
    def create_csv_file(self):
        with open(self.output_file, 'w', newline='') as csv_file:
            fieldnames = ['query', 'documentUrl', 'documentId', 'rootId', 'contentType', 'contentLength',
                          'documentPath', 'creationDate', 'documentNumber']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            yield writer

    def start(self):
        logger.info('START')
        count = self.log_matches()
        try:
            documents = self.scan_or_query_all()
            pbar = tqdm(documents, total=count, desc='Downloading %s document(s)' % count, file=sys.stdout,
                        disable=self.no_progressbar)
            print(pbar)
            with self.create_csv_file() as csvwriter:
                for index, document in enumerate(pbar):
                    try:
                        self.save_indexed_document(csvwriter, document, index)
                        logger.info('Processed document %s' % document.get('_id', None))
                        self.sleep()
                    except HTTPError:
                        logger.error('Unable to export document %s' % document.get('_id', None),
                                     exc_info=self.traceback)
        except ProtocolError:
            logger.error('Exception while exporting documents', exc_info=self.traceback)
