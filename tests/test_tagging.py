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
        self.csv_path = root('tests/fixtures/tags.csv')

    @contextmanager
    def mock_tagging_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/document/project/tag/%s" % (self.datashare_url, self.datashare_project)
            resp.add(responses.PUT, re.compile(tagging_endpoint_re), body='')
            yield resp

    def test_summary(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_path])
            self.assertIn('Adding 20 tags to 10 documents', result.output)

    def test_progression(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_path])
            self.assertIn('Added "Actinopodidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Hexathelidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Dipluridae" to document "vYl1C4bsWphUKvXEBDhM"', result.output)
            self.assertTrue(result.exit_code == 0)

    @responses.activate
    def test_http_tagging_requests(self):
        with self.mock_tagging_endpoint() as resp:
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_path])
            self.assertTrue(len(resp.calls) == 10)

    def test_tagger_tree(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, self.csv_path)
        self.assertIn('l7VnZZEzg2fr960NWWEG', tagger.tree)
        self.assertEqual(tagger.tree['vYl1C4bsWphUKvXEBDhM']['routing'], 'vYl1C4bsWphUKvXEBDhM')
        self.assertIn('Antrodiaetidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
        self.assertIn('Idiopidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
        self.assertEqual(len(tagger.tree['DWLOskax28jPQ2CjFrCo']['tags']), 2)
