import json
import os

from contextlib import contextmanager
from os.path import dirname
from unittest import TestCase

from tarentula.datashare_client import DatashareClient


def absolute_path(relative_path):
    return os.path.join(os.path.abspath(dirname(dirname(__file__))), relative_path)


class TestAbstract(TestCase):
    datashare_client = None
    datashare_project = 'test-datashare'

    @classmethod
    def setUpClass(cls):
        cls.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9200')
        cls.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        cls.datashare_client = DatashareClient(cls.datashare_url, cls.elasticsearch_url)
        cls.species_path = absolute_path('tests/fixtures/species.json')
        cls.datashare_client.create(cls.datashare_project)

    @classmethod
    def tearDownClass(cls):
        cls.datashare_client.delete_index(cls.datashare_project)

    def index_documents(self, documents=None):
        if documents is None:
            documents = []
        for document in documents:
            self.datashare_client.index(index=self.datashare_project, document=document, id=document['_id'])
        self.datashare_client.refresh(index=self.datashare_project)

    def delete_documents(self, documents=None):
        if documents is None:
            documents = []
        for document in documents:
            self.datashare_client.delete(index=self.datashare_project, id=document['_id'])
        self.datashare_client.refresh(index=self.datashare_project)

    @contextmanager
    def existing_species_documents(self):
        with open(self.species_path, 'r') as species_file:
            species = json.loads(species_file.read())
            self.index_documents(species)
            try:
                yield species
            finally:
                self.delete_documents(species)
