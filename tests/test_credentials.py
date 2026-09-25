import re

from unittest import TestCase

import click
import responses
from click.testing import CliRunner

from tarentula.cli import cli
from tarentula.datashare_client import (
    DATASHARE_CSRF_COOKIE_NAME,
    DATASHARE_CSRF_HEADER_NAME,
    DatashareClient,
    parse_cookies,
)

DATASHARE_URL = 'http://datashare.test'
ELASTICSEARCH_URL = 'http://elasticsearch.test'
PROJECT = 'test-project'
APIKEY = 'secret-apikey'
SESSION = 'secret-session'


def add_csrf_handshake(resp, token='csrf-token'):
    resp.add(responses.GET, f'{DATASHARE_URL}/api/users/me', body='{}', status=200,
             headers={'Set-Cookie': f'{DATASHARE_CSRF_COOKIE_NAME}={token}; Path=/'})


class TestCredentialsAreNotSentToElasticsearch(TestCase):
    """Datashare credentials must stay on the Datashare host."""

    def _make_client(self, **kwargs):
        return DatashareClient(datashare_url=DATASHARE_URL, elasticsearch_url=ELASTICSEARCH_URL,
                               datashare_project=PROJECT, **kwargs)

    @responses.activate
    def test_apikey_and_session_cookie_are_not_sent_to_the_elasticsearch_host(self):
        responses.add(responses.POST, re.compile(f'^{ELASTICSEARCH_URL}/{PROJECT}/_count$'), json={'count': 0})

        self._make_client(cookies=f'_ds_session_id={SESSION}', apikey=APIKEY).count(index=PROJECT)

        request = responses.calls[0].request
        self.assertIsNone(request.headers.get('Authorization'))
        self.assertNotIn(SESSION, request.headers.get('Cookie', ''))

    @responses.activate
    def test_csrf_token_is_not_replayed_to_the_elasticsearch_host(self):
        responses.add(responses.PUT, f'{DATASHARE_URL}/api/index/{PROJECT}', status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.PUT, f'{DATASHARE_URL}/api/index/{PROJECT}', status=200, body='')
        responses.add(responses.POST, re.compile(f'^{ELASTICSEARCH_URL}/{PROJECT}/_count$'), json={'count': 0})

        client = self._make_client()
        client.create(PROJECT)
        client.count(index=PROJECT)

        request = responses.calls[-1].request
        self.assertIsNone(request.headers.get(DATASHARE_CSRF_HEADER_NAME))
        self.assertNotIn(DATASHARE_CSRF_COOKIE_NAME, request.headers.get('Cookie', ''))

    @responses.activate
    def test_an_elasticsearch_403_does_not_send_credentials_to_the_datashare_url(self):
        responses.add(responses.POST, re.compile(f'^{ELASTICSEARCH_URL}/{PROJECT}/_count$'), status=403, body='no')
        add_csrf_handshake(responses)

        client = DatashareClient(elasticsearch_url=ELASTICSEARCH_URL, datashare_project=PROJECT,
                                 cookies=f'_ds_session_id={SESSION}', apikey=APIKEY)
        with self.assertRaises(Exception):
            client.count(index=PROJECT)

        self.assertEqual([call for call in responses.calls if '/api/users/me' in call.request.url], [])


class TestCsrfRetryBehaviour(TestCase):
    def _make_client(self, **kwargs):
        return DatashareClient(datashare_url=DATASHARE_URL, elasticsearch_url=None,
                               datashare_project=PROJECT, **kwargs)

    @responses.activate
    def test_refreshed_csrf_token_overrides_a_stale_user_supplied_cookie(self):
        endpoint = f'{DATASHARE_URL}/api/index/{PROJECT}'
        responses.add(responses.PUT, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses, token='FRESH')
        responses.add(responses.PUT, endpoint, status=200, body='')

        client = self._make_client(cookies=f'_ds_session_id=abc; {DATASHARE_CSRF_COOKIE_NAME}=STALE')
        client.create(PROJECT)

        retry = responses.calls[-1].request
        self.assertEqual(retry.headers.get(DATASHARE_CSRF_HEADER_NAME), 'FRESH')
        self.assertIn(f'{DATASHARE_CSRF_COOKIE_NAME}=FRESH', retry.headers.get('Cookie', ''))
        self.assertNotIn('STALE', retry.headers.get('Cookie', ''))

    @responses.activate
    def test_a_403_is_not_retried_when_the_csrf_token_did_not_change(self):
        endpoint = f'{DATASHARE_URL}/api/index/{PROJECT}'
        responses.add(responses.PUT, endpoint, status=403, body='Forbidden')
        add_csrf_handshake(responses)
        responses.add(responses.PUT, endpoint, status=200, body='')
        responses.add(responses.PUT, endpoint, status=403, json={'error': 'user is not allowed'})
        add_csrf_handshake(responses)

        client = self._make_client()
        client.create(PROJECT)
        client.create(PROJECT)

        puts = [call for call in responses.calls if call.request.method == 'PUT']
        self.assertEqual(len(puts), 3)


class TestCookieParsing(TestCase):
    def test_an_empty_cookie_string_yields_no_cookie(self):
        self.assertEqual(parse_cookies(''), {})

    def test_semicolon_separated_pairs_are_parsed(self):
        self.assertEqual(parse_cookies('_ds_session_id=abc; other=def'),
                         {'_ds_session_id': 'abc', 'other': 'def'})

    def test_comma_separated_pairs_do_not_corrupt_the_session_value(self):
        self.assertEqual(parse_cookies('_ds_session_id=abc, other=def'),
                         {'_ds_session_id': 'abc', 'other': 'def'})

    def test_a_quoted_value_containing_commas_is_kept_whole_and_unquoted(self):
        session = r'_ds_session_id="{\"login\":\"\",\"roles\":[],\"sessionId\":\"dq18s0kj\"}"'

        self.assertEqual(parse_cookies(session),
                         {'_ds_session_id': '{"login":"","roles":[],"sessionId":"dq18s0kj"}'})

    def test_a_pasted_header_line_is_rejected(self):
        with self.assertRaises(click.BadParameter):
            parse_cookies('Cookie: _ds_session_id=abc')

    def test_an_invalid_pair_is_rejected_instead_of_dropping_the_others(self):
        with self.assertRaises(click.BadParameter):
            parse_cookies('_ds_session_id=abc; display name=bob')

    def test_client_cookies_use_the_shared_parser(self):
        self.assertEqual(DatashareClient(cookies='_ds_session_id=abc').cookies, {'_ds_session_id': 'abc'})

    def test_a_malformed_cookie_string_fails_the_command_loudly(self):
        result = CliRunner().invoke(cli, ['count', '--elasticsearch-url', ELASTICSEARCH_URL,
                                          '--datashare-project', PROJECT,
                                          '--cookies', 'Cookie: _ds_session_id=abc'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('cannot parse cookie', result.output)
