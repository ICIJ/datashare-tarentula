import re

from unittest import TestCase

import responses

from tarentula.datashare_client import (
    DATASHARE_CSRF_COOKIE_NAME,
    DATASHARE_CSRF_HEADER_NAME,
    DatashareClient,
)
from tarentula.tagging import Tagger


DATASHARE_URL = 'http://datashare.test'
PROJECT = 'test-project'
CSRF_TOKEN = 'csrf-token-value'


def add_csrf_handshake(resp, token=CSRF_TOKEN):
    resp.add(
        responses.GET,
        f'{DATASHARE_URL}/api/users/me',
        body='{}',
        status=200,
        headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={token}; Path=/'},
    )


class TestCsrfRetry(TestCase):
    """Verify Datashare-routed requests refresh the CSRF token on 403 and retry."""

    def _make_client(self, elasticsearch_url=None):
        return DatashareClient(
            datashare_url=DATASHARE_URL,
            elasticsearch_url=elasticsearch_url,
            datashare_project=PROJECT,
        )

    def _assert_csrf_sent(self, request):
        self.assertEqual(request.headers.get(DATASHARE_CSRF_HEADER_NAME), CSRF_TOKEN)
        self.assertIn(f'{DATASHARE_CSRF_COOKIE_NAME}={CSRF_TOKEN}', request.headers.get('Cookie', ''))

    @responses.activate
    def test_count_retries_with_csrf_on_403(self):
        endpoint = re.compile(r'^%s/api/index/search/%s/_count$' % (DATASHARE_URL, PROJECT))
        responses.add(responses.POST, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.POST, endpoint, status=200, json={'count': 42})

        result = self._make_client().count(index=PROJECT)

        self.assertEqual(result['count'], 42)
        self.assertEqual(len(responses.calls), 3)
        self._assert_csrf_sent(responses.calls[2].request)

    @responses.activate
    def test_query_retries_with_csrf_on_403(self):
        endpoint = re.compile(r'^%s/api/index/search/%s/_search' % (DATASHARE_URL, PROJECT))
        responses.add(responses.POST, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.POST, endpoint, status=200,
                      json={'hits': {'hits': [], 'total': {'value': 0}}})

        result = self._make_client().query(index=PROJECT)

        self.assertIn('hits', result)
        self.assertEqual(len(responses.calls), 3)
        self._assert_csrf_sent(responses.calls[2].request)

    @responses.activate
    def test_scroll_retries_with_csrf_on_403(self):
        endpoint = f'{DATASHARE_URL}/api/index/search/_search/scroll'
        responses.add(responses.POST, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.POST, endpoint, status=200,
                      json={'hits': {'hits': []}})

        self._make_client().scroll('scroll-id')

        self.assertEqual(len(responses.calls), 3)
        self._assert_csrf_sent(responses.calls[2].request)

    @responses.activate
    def test_create_retries_with_csrf_on_403(self):
        endpoint = f'{DATASHARE_URL}/api/index/{PROJECT}'
        responses.add(responses.PUT, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.PUT, endpoint, status=200, body='')

        result = self._make_client().create(PROJECT)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(responses.calls), 3)
        self._assert_csrf_sent(responses.calls[2].request)

    @responses.activate
    def test_csrf_token_is_cached_for_subsequent_requests(self):
        endpoint = re.compile(r'^%s/api/index/search/%s/_count$' % (DATASHARE_URL, PROJECT))
        responses.add(responses.POST, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.POST, endpoint, status=200, json={'count': 1})
        responses.add(responses.POST, endpoint, status=200, json={'count': 2})

        client = self._make_client()
        first = client.count(index=PROJECT)
        second = client.count(index=PROJECT)

        self.assertEqual(first['count'], 1)
        self.assertEqual(second['count'], 2)
        # Second call must NOT trigger another CSRF handshake.
        self.assertEqual(len(responses.calls), 4)
        self._assert_csrf_sent(responses.calls[3].request)

    @responses.activate
    def test_count_does_not_fetch_csrf_when_request_succeeds(self):
        endpoint = re.compile(r'^%s/api/index/search/%s/_count$' % (DATASHARE_URL, PROJECT))
        responses.add(responses.POST, endpoint, status=200, json={'count': 0})

        self._make_client().count(index=PROJECT)

        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_count_skips_csrf_when_elasticsearch_url_set(self):
        es_url = 'http://elasticsearch.test'
        endpoint = re.compile(r'^%s/%s/_count$' % (es_url, PROJECT))
        responses.add(responses.POST, endpoint, status=200, json={'count': 0})

        self._make_client(elasticsearch_url=es_url).count(index=PROJECT)

        # Direct ES path stays a single request — no /api/users/me handshake.
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_tagger_retries_with_csrf_on_403(self):
        endpoint = re.compile(r'^%s/api/%s/documents/tags/' % (DATASHARE_URL, PROJECT))
        responses.add(responses.PUT, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.PUT, endpoint, status=201, body='')

        tagger = Tagger(DATASHARE_URL, PROJECT, 0, csv_path='', progressbar=False)
        tagger.csv_rows = [{'tag': 'mygalomorph', 'documentId': 'doc-1', 'routing': 'doc-1'}]
        tagger.start()

        self.assertEqual(len(responses.calls), 3)
        self._assert_csrf_sent(responses.calls[2].request)
