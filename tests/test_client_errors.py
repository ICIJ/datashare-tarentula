import json
import os
import re

from unittest import TestCase

import requests
import responses

from tarentula.datashare_client import DatashareClient, urljoin

ELASTICSEARCH_URL = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')
ES = 'http://elasticsearch.test'
PROJECT = 'test-project'


def client():
    return DatashareClient(elasticsearch_url=ES, datashare_project=PROJECT)


class TestClientErrors(TestCase):
    """Elasticsearch errors must surface as HTTPError, not as None or a JSON parse error."""

    @responses.activate
    def test_count_raises_on_elasticsearch_error(self):
        responses.add(responses.POST, re.compile(f'^{ES}/{PROJECT}/_count$'), status=400,
                      json={'error': {'reason': 'Failed to parse query'}})

        with self.assertRaises(requests.exceptions.HTTPError):
            client().count(index=PROJECT)

    @responses.activate
    def test_mappings_raises_on_elasticsearch_error(self):
        responses.add(responses.GET, re.compile(f'^{ES}/{PROJECT}/_mappings$'), status=404,
                      body='no such index')

        with self.assertRaises(requests.exceptions.HTTPError):
            client().mappings(index=PROJECT)

    @responses.activate
    def test_document_raises_on_elasticsearch_error(self):
        responses.add(responses.GET, re.compile(f'^{ES}/{PROJECT}/_doc/unknown'), status=404,
                      body='no such index')

        with self.assertRaises(requests.exceptions.HTTPError):
            client().document(index=PROJECT, id='unknown')

    @responses.activate
    def test_count_accepts_a_bare_query_fragment(self):
        responses.add(responses.POST, re.compile(f'^{ES}/{PROJECT}/_count$'), json={'count': 3})

        result = client().count(index=PROJECT, query={'match_all': {}})

        self.assertEqual(result['count'], 3)
        self.assertEqual(json.loads(responses.calls[0].request.body), {'query': {'match_all': {}}})

    @responses.activate
    def test_scroll_does_not_send_a_null_scroll_duration(self):
        responses.add(responses.POST, f'{ES}/_search/scroll', json={'hits': {'hits': []}})

        client().scroll('scroll-id')

        self.assertEqual(json.loads(responses.calls[0].request.body), {'scroll_id': 'scroll-id'})

    def test_urljoin_accepts_non_string_arguments(self):
        self.assertEqual(urljoin(ES, PROJECT, '/_doc/', 1234), f'{ES}/{PROJECT}/_doc/1234')


class TestIndexedContentLength(TestCase):
    index_name = 'test-tarentula-content-length'

    def setUp(self):
        requests.put(f'{ELASTICSEARCH_URL}/{self.index_name}')

    def tearDown(self):
        requests.delete(f'{ELASTICSEARCH_URL}/{self.index_name}')

    def test_content_length_is_a_byte_length(self):
        content = 'héllo'
        datashare_client = DatashareClient(elasticsearch_url=ELASTICSEARCH_URL)
        datashare_client.index(self.index_name, {'content': content}, id='utf8')
        document = requests.get(f'{ELASTICSEARCH_URL}/{self.index_name}/_doc/utf8').json()

        self.assertEqual(document['_source']['contentLength'], len(content.encode('utf-8')))
