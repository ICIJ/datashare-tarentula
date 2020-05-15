import json
import requests
import shutil
import sys
from tqdm import tqdm

from os import makedirs
from os.path import join, dirname, basename, exists
from time import sleep

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger
from elasticsearch.exceptions import ElasticsearchException, ConnectionTimeout, NotFoundError
from requests.exceptions import HTTPError, ConnectionError
from urllib3.exceptions import ProtocolError

class Download:
    def __init__(self, datashare_url, datashare_project, destination_directory, query = '*', throttle = 0, cookies = '', elasticsearch_url =  None, path_format = '{id_2b}/{id_4b}/{id}', scroll = '10m', once = False, traceback = False, progressbar = True):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
        self.destination_directory = destination_directory
        self.throttle = throttle
        self.cookies_string = cookies
        self.path_format = path_format
        self.once = once
        self.traceback = traceback
        self.progressbar = progressbar
        try:
            self.datashare_client = DatashareClient(datashare_url, elasticsearch_url, cookies, scroll)
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
                                "type": "Document"
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
            "basename": basename(document.get('_source').get("path")),
            "parentDocument": document.get('_source').get('parentDocument')
        }

    def document_file_path(self, document, parents = True):
        formatted_path = self.path_format.format(**self.document_file_options(document))
        file_path = join(self.destination_directory, formatted_path)
        if parents:
            parents_path = dirname(file_path)
            makedirs(parents_path, exist_ok=True)
        return file_path

    def count_matches(self):
        index = self.datashare_project
        return self.datashare_client.count(index = index, query = self.query_body).get('count')

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s' % (count, index))
        return count

    def scan_or_query_all(self):
        index = self.datashare_project
        self.log_matches()
        logger.info('Searching document(s) metadata in %s' % index)
        return self.datashare_client.scan_or_query_all(index = index, query = self.query_body, _source_includes = ["path", "parentDocument"])

    def download(self, document):
        id = document.get('_id')
        routing = document.get('_routing', id)
        logger.info('Downloading document %s' % id)
        document_file_stream = self.datashare_client.download(self.datashare_project, id, routing)
        document_file_stream.raw.decode_content = True
        document_file_stream.raise_for_status()
        self.save(document, document_file_stream)

    def exists(self, document):
        file_path = self.document_file_path(document)
        return exists(file_path)

    def save(self, document, document_file_stream):
        file_path = self.document_file_path(document)
        with open(file_path, 'wb') as file:
            shutil.copyfileobj(document_file_stream.raw, file)

    def start(self):
        count = self.log_matches()
        try:
            documents = self.scan_or_query_all()
            pbar = tqdm(documents, total=count, desc="Downloading %s document(s)" % count, file=sys.stdout, disable=self.no_progressbar)
            for document in pbar:
                try:
                    if not self.once or not self.exists(document):
                        self.download(document)
                        logger.info('Saved document %s' % document.get('_id'))
                        self.sleep()
                    else:
                        logger.info('Skipping document %s' % document.get('_id'))
                except (ElasticsearchException, HTTPError):
                    logger.error('Unable to download document %s' % document.get('_id'), exc_info=self.traceback)
        except (ProtocolError, ConnectionTimeout, NotFoundError):
            logger.error('Exception while searching documents', exc_info=self.traceback)
