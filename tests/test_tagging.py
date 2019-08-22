import responses
import os
import re

from click.testing import CliRunner
from contextlib import contextmanager
from os.path import dirname
from unittest import  TestCase

from tarentula.cli import cli
from tarentula.tagging import Tagger
from tarentula.datashare_client import DatashareClient

root = lambda x: os.path.join(os.path.abspath(dirname(dirname(__file__))), x)

class TestTagging(TestCase):
    @classmethod
    def setUpClass(self):
        self.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9292')
        self.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8181')
        self.datashare_project = 'local-datashare'
        self.datashare_client = DatashareClient(self.datashare_url, self.elasticsearch_url)
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

    def test_tags_are_created(self):
        with self.datashare_client.temporary_project() as project:
            tagger = Tagger(self.datashare_url, project, 0, self.csv_with_ids_path)
            # Ensure there is no documents yet
            self.assertEqual(self.datashare_client.query(index = project, size = 0).get('hits', {}).get('total'), 0)
            # Create all the docs
            for document_id, leaf in tagger.tree.items():
                self.datashare_client.index(project, { "tags": [] }, document_id, leaf['routing'])
            # Ensure the docs exists
            self.assertEqual(self.datashare_client.query(index = project, size = 0).get('hits', {}).get('total'), 10)
            # Ensure the docs are not tagged yet
            self.assertEqual(self.datashare_client.query(index = project, size = 0, q = 'tags:*').get('hits', {}).get('total'), 0)
            # Tag them all!
            tagger.start()
            # Refresh the index
            self.datashare_client.refresh(project)
            # Ensure the docs have been tagged
            self.assertEqual(self.datashare_client.query(index = project, size = 0, q = 'tags:*').get('hits', {}).get('total'), 10)
