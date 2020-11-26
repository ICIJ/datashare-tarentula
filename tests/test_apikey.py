import json
import re
import responses

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
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/%s/documents/src" % (self.datashare_url, self.datashare_project)
            resp.add(responses.GET, re.compile(tagging_endpoint_re), body='', status=201)
            resp.add_passthru(self.datashare_url)
            resp.add_passthru(self.elasticsearch_url)
            yield resp

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
            self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_downloading_with_cli(self):
        self.datashare_client.index(index=self.datashare_project, document={'type': 'Document', 'content': 'content',
                                                                            'tags': ['tag']}, id='id')
        with self.mock_download_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--elasticsearch-url', self.elasticsearch_url, '--datashare-url',
                                self.datashare_url, '--datashare-project',
                                self.datashare_project, '--apikey', 'my_api_key', '--query', '*'])
            self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')
