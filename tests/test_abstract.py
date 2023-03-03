import json
import os
import requests

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
        cls.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')
        cls.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        cls.datashare_client = DatashareClient(cls.datashare_url, cls.elasticsearch_url)
        cls.species_path = absolute_path('tests/fixtures/species.json')
        cls.luxleaks_path = absolute_path('tests/fixtures/luxleaks-sample.json')
        cls.datashare_client.create(cls.datashare_project)

    @classmethod
    def tearDownClass(cls):
        cls.datashare_client.delete_index(cls.datashare_project)

    @property
    def elasticsearch_version(self):
        response = requests.get(self.elasticsearch_url)
        response.raise_for_status()
        return response.json().get('version').get('number')
    
    @property
    def elasticsearch_version_info(self):
        return tuple(map(int, self.elasticsearch_version.split('.')))

    def index_documents(self, documents=None):
        if documents is None:
            documents = []
        for document in documents:
            id = document.get('_id', None)
            routing = document.get('_routing', None)
            self.datashare_client.index(index=self.datashare_project, document=document, id=id, routing=routing)
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

    @contextmanager
    def existing_luxleaks_documents(self):
        with open(self.luxleaks_path, 'r') as luxleaks_file:
            luxleaks = json.loads(luxleaks_file.read())
            self.index_documents(luxleaks)
            try:
                yield luxleaks
            finally:
                self.delete_documents(luxleaks)

    from contextlib import contextmanager

    @contextmanager
    def working_directory(self, path):
        previous_cwd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous_cwd)
