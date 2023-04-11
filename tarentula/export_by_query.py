import csv
import sys

from collections import OrderedDict
from contextlib import contextmanager
from time import sleep
from requests.exceptions import HTTPError
from rich.progress import Progress
from urllib3.exceptions import ProtocolError

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
                 sort_by: str = '_id',
                 order_by: str = 'asc',
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
            sys.exit()

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

    def sleep(self):
        sleep(self.throttle / 1000)

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
        return {'query': self.query, 'documentUrl': url, 'documentId': id,
                'rootId': routing, 'documentNumber': number}

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
                                    escapechar='\\')
            writer.writeheader()
            yield writer

    def start(self):
        count = self.log_matches()
        desc = f'Exporting {count} document(s)'
        try:
            with Progress(disable=self.no_progressbar) as progress:
                task = progress.add_task(desc, total=count)
                documents = self.datashare_client.scan_or_query_all(self.datashare_project, self.source_fields_names,
                                                                    self.sort_by,
                                                                    self.order_by, self.scroll, self.query_body,
                                                                    self.from_, self.limit, self.size)
                with self.create_csv_file() as csvwriter:
                    for index, document in enumerate(documents):
                        try:
                            self.save_indexed_document(csvwriter, document, index)
                            logger.info('Saved document %s', document.get('_id', None))
                        except HTTPError:
                            logger.error('Unable to export document %s', document.get('_id', None),
                                         exc_info=self.traceback)
                        progress.advance(task)
                        self.sleep()
                logger.info('Written documents metadata in %s', self.output_file)
        except ProtocolError:
            logger.error('Exception while exporting documents', exc_info=self.traceback)
