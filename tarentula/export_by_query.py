import csv
import json
import operator
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
                 scroll: str = None,
                 source: str = 'contentType,contentLength:0,extractionDate,path',
                 once: bool = False,
                 traceback: bool = False,
                 progressbar: bool = True,
                 type: str = 'Document'):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
        self.output_file = output_file
        self.throttle = throttle
        self.cookies_string = cookies
        self.apikey = apikey
        self.once = once
        self.traceback = traceback
        self.progressbar = progressbar
        self.scroll = scroll
        self.source = source
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

    @property
    def source_fields(self):
        return [ self.source_field_params(f) for f in self.source.split(',') ]

    @property
    def source_fields_names(self):
        return [ field.pop(0) for field in self.source_fields ]

    def source_field_params(self, field):
        field_params = field.strip().split(':')
        field_name = field_params[0]
        field_default = field_params[1] if len(field_params) > 1 else ''
        return [field_name, field_default]

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
        source = ["path"] + self.source_fields_names
        if self.scroll is None:
            logger.info('Searching document(s) metadata in %s' % index)
            return self.datashare_client.query_all(index=index, query=self.query_body, source=source)
        else:
            logger.info('Scrolling over document(s) metadata in %s' % index)
            return self.datashare_client.scan_all(index=index, query=self.query_body, source=source, scroll=self.scroll)

    def document_default_values(self, document, number):
        index = self.datashare_project
        id = document.get('_id')
        routing = document.get('_routing', id)
        url = self.datashare_client.document_url(index, id, routing)
        return { 'query': self.query, 'documentUrl': url, 'documentId': id,
                 'rootId': routing, 'documentNumber': number }

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
        csvwriter.writerow({ **default_values, **source_values })

    @contextmanager
    def create_csv_file(self):
        with open(self.output_file, 'w', newline='') as csv_file:
            fieldnames = ['query', 'documentUrl', 'documentId', 'rootId', 'documentNumber']
            fieldnames += self.source_fields_names
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            yield writer

    def start(self):
        count = self.log_matches()
        try:
            documents = self.scan_or_query_all()
            pbar = tqdm(documents, total=count, desc='Exporting %s document(s)' % count,
                        file=sys.stdout, disable=self.no_progressbar)
            with self.create_csv_file() as csvwriter:
                for index, document in enumerate(pbar):
                    try:
                        self.save_indexed_document(csvwriter, document, index)
                        logger.info('Saved document %s' % document.get('_id', None))
                        self.sleep()
                    except HTTPError:
                        logger.error('Unable to export document %s' % document.get('_id', None),
                                        exc_info=self.traceback)
                logger.info('Written documents metadata in %s' % self.output_file)
        except ProtocolError:
            logger.error('Exception while exporting documents', exc_info=self.traceback)
