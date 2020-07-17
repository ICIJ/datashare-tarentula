import os
import json
import shutil

from click.testing import CliRunner
from contextlib import contextmanager
from os.path import dirname
from unittest import  TestCase

from tarentula.cli import cli
from tarentula.datashare_client import DatashareClient

root = lambda x: os.path.join(os.path.abspath(dirname(dirname(__file__))), x)
loadJsonFile = lambda x: json.loads(open(root(x), 'r').read())

class TestDownload(TestCase):
    @classmethod
    def setUpClass(self):
        self.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9200')
        self.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        self.datashare_project = 'local-datashare'
        self.datashare_client = DatashareClient(self.datashare_url, self.elasticsearch_url)
        self.species_path = root('tests/fixtures/species.json')

    @classmethod
    def tearDown(self):
        shutil.rmtree(root('tmp'))

    def index_documents(self, documents = []):
        for document in documents:
            self.datashare_client.index(index = self.datashare_project, document = document, id = document['_id'])
        self.datashare_client.refresh(index = self.datashare_project)

    def delete_documents(self, documents = []):
        for document in documents:
            self.datashare_client.delete(index = self.datashare_project, id = document['_id'])
        self.datashare_client.refresh(index = self.datashare_project)

    @contextmanager
    def existing_species_documents(self):
        with open(self.species_path, 'r') as species_file:
            species = json.loads(species_file.read())
            self.index_documents(species)
            try:
                yield species
            finally:
                self.delete_documents(species)

    def test_summary(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_scroll(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*', '--scroll', '1m'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard_sta(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_meta_is_downloaded_for_actinopodidae(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Actinopodidae'])
            json = loadJsonFile('tmp/l7/Vn/l7VnZZEzg2fr960NWWEG.json')
            self.assertEqual(json['_id'], 'l7VnZZEzg2fr960NWWEG')

    def test_meta_is_downloaded_for_ctenizidae(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Ctenizidae'])
            json = loadJsonFile('tmp/Bm/ov/BmovvXBisWtyyx6o9cuG.json')
            self.assertEqual(json['_id'], 'BmovvXBisWtyyx6o9cuG')

    def test_meta_is_downloaded_for_idiopidae_with_default_properties(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Idiopidae'])
            json = loadJsonFile('tmp/Dz/LO/DzLOskax28jPQ2CjFrCo.json')
            self.assertIn('_id', json)
            self.assertIn('_source', json)
            self.assertNotIn('name', json['_source'])

    def test_meta_is_downloaded_for_idiopidae_with_extra_properties(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Idiopidae', '--source', 'name'])
            json = loadJsonFile('tmp/Dz/LO/DzLOskax28jPQ2CjFrCo.json')
            self.assertIn('_id', json)
            self.assertIn('_source', json)
            self.assertIn('name', json['_source'])
