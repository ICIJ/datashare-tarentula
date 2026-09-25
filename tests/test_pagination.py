import os

from unittest import TestCase

import requests

from tarentula.datashare_client import DatashareClient

ELASTICSEARCH_URL = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')
INDEX = 'test-tarentula-pagination'
CONTENT_TYPES = ['audio/mpeg', 'text/plain', 'application/pdf', 'image/png']
MAX_RESULT_WINDOW = 10
DOCUMENT_COUNT = 20


class TestPagination(TestCase):
    """Regression tests for the document loss and duplication of `query_all`."""

    @classmethod
    def setUpClass(cls):
        requests.delete(f'{ELASTICSEARCH_URL}/{INDEX}')
        requests.put(f'{ELASTICSEARCH_URL}/{INDEX}',
                     json={'settings': {'index.max_result_window': MAX_RESULT_WINDOW},
                           'mappings': {'properties': {'name': {'type': 'keyword'},
                                                       'type': {'type': 'keyword'},
                                                       'contentType': {'type': 'keyword'}}}})
        for number in range(DOCUMENT_COUNT):
            requests.put(f'{ELASTICSEARCH_URL}/{INDEX}/_doc/doc{number:02d}',
                         json={'type': 'Document',
                               'name': f'name{number:02d}',
                               'contentType': CONTENT_TYPES[number % len(CONTENT_TYPES)]})
        requests.post(f'{ELASTICSEARCH_URL}/{INDEX}/_refresh')
        cls.datashare_client = DatashareClient(elasticsearch_url=ELASTICSEARCH_URL, datashare_project=INDEX)

    @classmethod
    def tearDownClass(cls):
        requests.delete(f'{ELASTICSEARCH_URL}/{INDEX}')

    def scan_or_query_all(self, sort_by='_score', order_by='desc', scroll=None, limit=0, size=5):
        return self.datashare_client.scan_or_query_all(INDEX, None, sort_by, order_by, scroll,
                                                       {'query': {'match_all': {}}}, 0, limit, size)

    def test_query_all_does_not_duplicate_documents_when_limit_shrinks_the_page(self):
        documents = self.datashare_client.query_all(index=INDEX, query={'query': {'match_all': {}}},
                                                    size=4, limit=6)
        ids = [document['_id'] for document in documents]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)

    def test_sorting_by_a_non_unique_field_exports_every_document(self):
        ids = [document['_id'] for document in self.scan_or_query_all(sort_by='contentType', order_by='asc', size=2)]
        self.assertEqual(len(set(ids)), DOCUMENT_COUNT)

    def test_sorting_by_score_pages_beyond_the_max_result_window(self):
        ids = [document['_id'] for document in self.scan_or_query_all(size=5)]
        self.assertEqual(len(set(ids)), DOCUMENT_COUNT)

    def test_limit_yields_exactly_that_many_distinct_documents(self):
        ids = [document['_id'] for document in self.scan_or_query_all(size=5, limit=7)]
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(set(ids)), 7)

    def test_limit_yields_exactly_that_many_distinct_documents_while_scrolling(self):
        ids = [document['_id'] for document in self.scan_or_query_all(size=5, limit=7, scroll='1m')]
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(set(ids)), 7)
