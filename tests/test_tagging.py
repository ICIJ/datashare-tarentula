import csv
import os
import re
import responses
import shutil

from click.testing import CliRunner
from contextlib import contextmanager
from os.path import dirname
from unittest import  TestCase

from tarentula.cli import cli
from tarentula.tagging import Tagger
from tarentula.datashare_client import DatashareClient

root = lambda x: os.path.join(os.path.abspath(dirname(dirname(__file__))), x)

class TestTagging(TestCase):

    def setUpClass(self):
        self.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9200')
        self.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        self.datashare_project = 'local-datashare'
        self.datashare_client = DatashareClient(self.datashare_url, self.elasticsearch_url)
        self.csv_with_ids_path = root('tests/fixtures/tags-with-document-id.csv')
        self.csv_with_urls_path = root('tests/fixtures/tags-with-document-url.csv')

    def tearDown(self):
        shutil.rmtree(root('tmp'))

    @contextmanager
    def mock_tagging_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/%s/documents/tags/" % (self.datashare_url, self.datashare_project)
            resp.add(responses.PUT, re.compile(tagging_endpoint_re), body='', status=201)
            yield resp

    def test_summary(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertIn('Adding 20 tags to 10 documents', result.output)

    def test_progression(self):
        with self.mock_tagging_endpoint():
            runner = CliRunner()
            result = runner.invoke(cli, ['--stdout-loglevel', 'INFO', 'tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertIn('Added "Actinopodidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Hexathelidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
            self.assertIn('Added "Dipluridae" to document "vYl1C4bsWphUKvXEBDhM"', result.output)
            self.assertTrue(result.exit_code == 0)

    def test_http_tagging_requests(self):
        with self.mock_tagging_endpoint() as resp:
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.csv_with_ids_path])
            self.assertTrue(len(resp.calls) == 20)

    def test_routing_is_correct(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, progressbar = False)
        self.assertEqual(tagger.tree['l7VnZZEzg2fr960NWWEG']['routing'], 'l7VnZZEzg2fr960NWWEG')
        self.assertEqual(tagger.tree['6VE7cVlWszkUd94XeuSd']['routing'], 'vZJQpKQYhcI577gJR0aN')

    def test_routing_uses_fallback(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, progressbar = False)
        self.assertEqual(tagger.tree['DWLOskax28jPQ2CjFrCo']['routing'], 'DWLOskax28jPQ2CjFrCo')

    def test_document_is_in_tree(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, progressbar = False)
        self.assertIn('l7VnZZEzg2fr960NWWEG', tagger.tree)

    def test_tags_are_in_tree(self):
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, progressbar = False)
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

    def test_tags_are_all_created(self):
        with self.datashare_client.temporary_project(self.datashare_project) as project:
            tagger = Tagger(self.datashare_url, project, 0, self.csv_with_ids_path, progressbar = False)
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

    def test_tag_is_correct(self):
        with self.datashare_client.temporary_project(self.datashare_project) as project:
            # Create the document
            self.datashare_client.index(index = project,  document = { 'name': 'Atypidae', 'tags': [] }, id ='atypidae')
            runner = CliRunner()
            with runner.isolated_filesystem():
                # Create a small CSV with just one tag
                with open('tags.csv', 'w') as file:
                    writer = csv.writer(file)
                    writer.writerows([ ['tag','documentId'], ['mygalomorph','atypidae'] ])
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', project, 'tags.csv'])
            # Get the document from Elasticsearch
            document = self.datashare_client.document(index = project, id = "atypidae")
            self.assertIn('mygalomorph', document.get('_source', {}).get('tags', []))

    def test_tags_are_correct(self):
        with self.datashare_client.temporary_project(self.datashare_project) as project:
            # Create the document
            self.datashare_client.index(index = project,  document = { 'name': 'Atypidae', 'tags': [] }, id ='atypidae')
            runner = CliRunner()
            with runner.isolated_filesystem():
                # Create a small CSV with just one tag
                with open('tags.csv', 'w') as file:
                    writer = csv.writer(file)
                    writer.writerows([ ['tag','documentId'], ['mygalomorph','atypidae'], ['spider','atypidae'] ])
                r = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', project, 'tags.csv'])
            # Get the document from Elasticsearch
            document = self.datashare_client.document(index = project, id = "atypidae")
            self.assertIn('mygalomorph', document.get('_source').get('tags', []))
            self.assertIn('spider', document.get('_source').get('tags', []))

    def test_cookies_are_parsed_by_tagger(self):
        cookies = 'session=mygalomorph;age=14'
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, cookies, progressbar = False)
        self.assertEqual(tagger.cookies['session'], 'mygalomorph')
        self.assertEqual(tagger.cookies['age'], '14')
        self.assertEqual(len(tagger.cookies.keys()), 2)

    def test_multiple_cookies_are_parsed_by_tagger(self):
        cookies = 'session=mygalomorph'
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, cookies, progressbar = False)
        self.assertEqual(tagger.cookies['session'], 'mygalomorph')
        self.assertEqual(len(tagger.cookies.keys()), 1)

    def test_session_cookies_are_parsed_by_tagger(self):
        cookies = r'_ds_session_id="{\"login\":\"\",\"roles\":[],\"sessionId\":\"dq18s0kj08dq10skLYGSu8SFVsg\",\"redirectAfterLogin\":\"/\"}"'
        tagger = Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, cookies, progressbar = False)
        self.assertEqual(tagger.cookies['_ds_session_id'], r'{"login":"","roles":[],"sessionId":"dq18s0kj08dq10skLYGSu8SFVsg","redirectAfterLogin":"/"}')
        self.assertEqual(len(tagger.cookies.keys()), 1)

    def test_cookies_are_send_while_tagging(self):
        with self.mock_tagging_endpoint() as resp:
            cookies = 'session=mygalomorph'
            Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, cookies, progressbar = False).start()
            self.assertEqual(resp.calls[0].request.headers['Cookie'], cookies)
            self.assertEqual(resp.calls[2].request.headers['Cookie'], cookies)
            self.assertEqual(resp.calls[6].request.headers['Cookie'], cookies)
            self.assertEqual(resp.calls[9].request.headers['Cookie'], cookies)

    def test_cookies_arent_send_while_tagging(self):
        with self.mock_tagging_endpoint() as resp:
            Tagger(self.datashare_url, self.datashare_project, 0, self.csv_with_ids_path, progressbar = False).start()
            self.assertNotIn('Cookie', resp.calls[0].request.headers)
            self.assertNotIn('Cookie', resp.calls[2].request.headers)
            self.assertNotIn('Cookie', resp.calls[6].request.headers)
            self.assertNotIn('Cookie', resp.calls[9].request.headers)

    def test_cookies_are_send_while_tagging_with_the_cli(self):
        with self.mock_tagging_endpoint() as resp:
            cookies = r'_ds_session_id="{\"login\":\"\",\"roles\":[],\"sessionId\":\"dq18s0kj08dq10skLYGSu8SFVsg\",\"redirectAfterLogin\":\"/\"}"'
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--cookies', cookies, self.csv_with_ids_path])
            self.assertEqual(resp.calls[1].request.headers['Cookie'], '_ds_session_id={"login":"","roles":[],"sessionId":"dq18s0kj08dq10skLYGSu8SFVsg","redirectAfterLogin":"/"}')
            self.assertEqual(resp.calls[3].request.headers['Cookie'], '_ds_session_id={"login":"","roles":[],"sessionId":"dq18s0kj08dq10skLYGSu8SFVsg","redirectAfterLogin":"/"}')
