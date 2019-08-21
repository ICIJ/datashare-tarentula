import responses
import os
import re

from click.testing import CliRunner
from contextlib import contextmanager
from os.path import dirname
from unittest import  TestCase

from tarentula.cli import cli
from tarentula.tagging import Tagger

root = lambda x: os.path.join(os.path.abspath(dirname(dirname(__file__))), x)

class TestTagging(TestCase):
    @classmethod
    def setUpClass(self):
        self.datashare_url = 'http://localhost:8080'
        self.datashare_project = 'local-tests'
        self.csv_with_ids_path = root('tests/fixtures/tags-with-document-id.csv')
        self.csv_with_urls_path = root('tests/fixtures/tags-with-document-url.csv')

    @contextmanager
    def mock_tagging_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/document/project/tag/%s" % (self.datashare_url, self.datashare_project)
            resp.add(responses.PUT, re.compile(tagging_endpoint_re), body='')
            yield resp

    def test_summary(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertIn('Adding 20 tags to 10 documents', result.output)

    def test_progression(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertIn('Added "Actinopodidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Hexathelidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Dipluridae" to document "vYl1C4bsWphUKvXEBDhM"', result.output)
            self.assertTrue(result.exit_code == 0)

    def test_http_tagging_requests(self):
        with self.mock_tagging_endpoint() as resp:
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertTrue(len(resp.calls) == 10)

    def test_routing_is_correct(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path)
        self.assertEqual(tagger.tree['l7VnZZEzg2fr960NWWEG']['routing'], 'l7VnZZEzg2fr960NWWEG')
        self.assertEqual(tagger.tree['6VE7cVlWszkUd94XeuSd']['routing'], 'vZJQpKQYhcI577gJR0aN')

    def test_routing_uses_fallback(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path)
        self.assertEqual(tagger.tree['DWLOskax28jPQ2CjFrCo']['routing'], 'DWLOskax28jPQ2CjFrCo')

    def test_document_is_in_tree(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path)
        self.assertIn('l7VnZZEzg2fr960NWWEG', tagger.tree)

    def test_tags_are_in_tree(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path)
        self.assertIn('Antrodiaetidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
        self.assertIn('Idiopidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])

    def tst_document_has_two_tags(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path)
        self.assertEqual(len(tagger.tree['DWLOskax28jPQ2CjFrCo']['tags']), 2)


    def test_tags_are_in_tree_with_url(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_urls_path)
        self.assertIn('Antrodiaetidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
        self.assertIn('Idiopidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])

    def test_routing_is_correct_with_url(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_urls_path)
        self.assertEqual(tagger.tree['l7VnZZEzg2fr960NWWEG']['routing'], 'l7VnZZEzg2fr960NWWEG')
        self.assertEqual(tagger.tree['6VE7cVlWszkUd94XeuSd']['routing'], 'vZJQpKQYhcI577gJR0aN')
