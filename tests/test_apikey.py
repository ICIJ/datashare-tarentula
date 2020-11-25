import re
import responses

from click.testing import CliRunner
from contextlib import contextmanager

from tarentula.cli import cli
from .test_abstract import TestAbstract, absolute_path

class TestApikey(TestAbstract):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.json_tags_path = absolute_path('tests/fixtures/tags-by-content-type.json')
        cls.csv_with_ids_path = absolute_path('tests/fixtures/tags-with-document-id.csv')
        cls.csv_with_urls_path = absolute_path('tests/fixtures/tags-with-document-url.csv')

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

    def test_apikey_header_is_NOT_sent_while_tagging_with_cli(self):
        with self.mock_tagging_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                self.datashare_project, self.csv_with_ids_path])
            self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tagging_with_cli(self):
        with self.mock_tagging_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                self.datashare_project, '--apikey',
                                'my_api_key', self.csv_with_ids_path])
            self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')

    def test_apikey_header_is_NOT_sent_while_tagging_by_query_with_cli(self):
        with self.mock_tagging_by_query_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                     '--datashare-project', self.datashare_project, self.json_tags_path])
            self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tagging_by_query_with_cli(self):
        with self.mock_tagging_by_query_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                     '--datashare-project', self.datashare_project, '--apikey', 'my_api_key', self.json_tags_path])
            self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')

    def test_apikey_header_is_NOT_sent_while_tag_cleaning_by_query_with_cli(self):
        with self.mock_tagging_by_query_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['clean-tags-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                     '--datashare-project', self.datashare_project, '--query', '@' + absolute_path('tests/fixtures/match_all_query.json')])
            self.assertIsNone(resp.calls[0].request.headers.get('Authorization'))

    def test_apikey_header_is_sent_while_tag_cleaning_by_query_with_cli(self):
        with self.mock_tagging_by_query_endpoint() as resp:
            runner = CliRunner()
            runner.invoke(cli, ['clean-tags-by-query', '--elasticsearch-url', self.elasticsearch_url,
                                     '--datashare-project', self.datashare_project, '--apikey', 'my_api_key', '--query', '@' + absolute_path('tests/fixtures/match_all_query.json')])
            self.assertEqual(resp.calls[0].request.headers['Authorization'], 'bearer my_api_key')
