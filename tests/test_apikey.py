import json
import re
import responses

from aioresponses import aioresponses
from click.testing import CliRunner
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestApikey(TestAbstract):

    @contextmanager
    def mock_tagging_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/%s/documents/tags/" % (self.datashare_url, self.datashare_project)
            resp.add(responses.PUT, re.compile(tagging_endpoint_re), body='', status=201)
            yield resp

    @contextmanager
    def mock_tagging_by_query_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/%s\/_update_by_query" % (self.elasticsearch_url, self.datashare_project)
            resp.add(responses.POST, re.compile(tagging_endpoint_re), body='', status=201)
            yield resp

    @contextmanager
    def mock_download_endpoint(self):
        # Raw file downloads go through AsyncDatashareClient.stream_download (aiohttp), not the
        # `requests`-based sync client, so they must be intercepted with aioresponses instead of
        # `responses`. Unmatched calls (e.g. search_after_scan's ES queries) pass through to the
        # real devenv Elasticsearch instance, but they still get recorded in `resp.requests`
        # alongside the download call, so callers must filter by URL (see
        # `downloaded_request_headers`).
        self.download_endpoint_re = re.compile(
            r"^%s/api/%s/documents/src/" % (re.escape(self.datashare_url), re.escape(self.datashare_project)))
        with aioresponses(passthrough_unmatched=True) as resp:
            resp.get(self.download_endpoint_re, body='', status=201)
            yield resp

    def downloaded_request_headers(self, resp):
        calls = [call for (method, url), calls in resp.requests.items()
                 if method.lower() == 'get' and self.download_endpoint_re.match(str(url))
                 for call in calls]
        self.assertEqual(1, len(calls))
        return calls[0].kwargs.get('headers') or {}

    def test_apikey_header_is_NOT_sent_while_tagging_with_cli(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\ndocumentTag,documentId,documentRouting')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                    self.datashare_project, file.name])
                self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tagging_with_cli(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\ndocumentTag,documentId,documentRouting')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                    self.datashare_project, '--apikey',
                                    'my_api_key', file.name])
                self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')

    def test_apikey_header_is_NOT_sent_while_tagging_by_query_with_cli(self):
        with NamedTemporaryFile(mode='w+') as file:
            json.dump({"tag-name": {"query": {"match_all": {}}}}, file)
            file.flush()
            file.seek(0)
            with self.mock_tagging_by_query_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                    '--datashare-project', self.datashare_project, file.name])
                self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tagging_by_query_with_cli(self):
        with NamedTemporaryFile(mode='w+') as file:
            json.dump({"tag-name": {"query": {"match_all": {}}}}, file)
            file.flush()
            file.seek(0)
            with self.mock_tagging_by_query_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                    '--datashare-project', self.datashare_project, '--apikey', 'my_api_key',
                                    file.name])
                self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')

    def test_apikey_header_is_NOT_sent_while_tag_cleaning_by_query_with_cli(self):
        with NamedTemporaryFile() as file:
            file.write(b'{"query": {"match_all": {}}}')
            file.flush()
            file.seek(0)
            with self.mock_tagging_by_query_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['clean-tags-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                    '--datashare-project', self.datashare_project, '--query',
                                    '@' + file.name])
                self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tag_cleaning_by_query_with_cli(self):
        self.datashare_client.index(index=self.datashare_project, document={'content': 'content', 'tags': ['tag']},
                                    id='id')
        with self.mock_tagging_by_query_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['clean-tags-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                '--datashare-project', self.datashare_project, '--apikey', 'my_api_key', '--query',
                                '{"query": {"ids": {"values": ["id"]}}}'])
            self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')

    def test_apikey_header_is_NOT_sent_while_downloading_with_cli(self):
        self.datashare_client.index(index=self.datashare_project, document={'type': 'Document', 'content': 'content',
                                                                            'tags': ['tag']}, id='id')
        with self.mock_download_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--elasticsearch-url', self.elasticsearch_url, '--datashare-url',
                                self.datashare_url, '--datashare-project',
                                self.datashare_project, '--query', '*'])
            headers = self.downloaded_request_headers(resp)
            self.assertIsNone(headers.get('Authorization'))

    def test_apikey_header_is_sent_while_downloading_with_cli(self):
        self.datashare_client.index(index=self.datashare_project, document={'type': 'Document', 'content': 'content',
                                                                            'tags': ['tag']}, id='id')
        with self.mock_download_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--elasticsearch-url', self.elasticsearch_url, '--datashare-url',
                                self.datashare_url, '--datashare-project',
                                self.datashare_project, '--apikey', 'my_api_key', '--query', '*'])
            headers = self.downloaded_request_headers(resp)
            self.assertEqual(headers.get('Authorization'), 'bearer my_api_key')
