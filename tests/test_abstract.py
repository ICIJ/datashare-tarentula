import json
import os

from contextlib import contextmanager
from os.path import dirname
from unittest import TestCase

from tarentula.datashare_client import DatashareClient

root = lambda x: os.path.join(os.path.abspath(dirname(dirname(__file__))), x)

class TestAbstract(TestCase):
    @classmethod
    def setUpClass(self):
        self.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9200')
        self.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        self.datashare_project = 'local-datashare'
        self.datashare_client = DatashareClient(self.datashare_url, self.elasticsearch_url)
        self.species_path = root('tests/fixtures/species.json')

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
