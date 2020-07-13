import os
import requests
import uuid

from unittest import  TestCase
from tarentula.datashare_client import DatashareClient

class TestDatashareClient(TestCase):
    @classmethod
    def setUpClass(self):
        self.datashare_url = os.environ.get('TEST_DATASHARE_URL', 'http://localhost:8080')
        self.elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://localhost:9200')
        self.datashare_client = DatashareClient(self.datashare_url, self.elasticsearch_url)

    def test_default_index_creation(self):
        self.assertEqual(requests.get('%s/%s' % (self.elasticsearch_url, 'local-datashare')).status_code, requests.codes.ok)
        self.assertNotEqual(requests.get('%s/%s' % (self.elasticsearch_url, 'unkonwn-index')).status_code, requests.codes.ok)

    def test_temporary_project_creation(self):
        with self.datashare_client.temporary_project() as project:
            result = requests.get('%s/%s' % (self.elasticsearch_url, project))
            self.assertEqual(result.status_code, requests.codes.ok)

    def test_temporary_project_deletion(self):
        project = self.datashare_client.temporary_project()
        self.datashare_client.refresh()
        result = requests.get('%s/%s' % (self.elasticsearch_url, project))
        self.assertNotEqual(result.status_code, requests.codes.ok)

    def test_document_creation(self):
        with self.datashare_client.temporary_project() as project:
            id = self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'foo': 'bar' })
            result = requests.get('%s/%s/doc/%s' % (self.elasticsearch_url, project, id))
            self.assertEqual(result.status_code, requests.codes.ok)
            self.assertEqual(result.json().get('_source', {}).get('foo'), 'bar')

    def test_document_deletion(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'foo': 'bar' }, id = 'to-delete')
            result = requests.get('%s/%s/doc/%s' % (self.elasticsearch_url, project, 'to-delete'))
            self.assertTrue(result.json().get('found'))
            self.datashare_client.delete(index = project, id = 'to-delete')
            result = requests.get('%s/%s/doc/%s' % (self.elasticsearch_url, project, 'to-delete'))
            self.assertFalse(result.json().get('found'))

    def test_index_deletion(self):
        with self.datashare_client.temporary_project() as project:
            result = requests.get('%s/%s' % (self.elasticsearch_url, project))
            self.assertEqual(result.status_code, requests.codes.ok)
            self.datashare_client.delete_index(project)
            result = requests.get('%s/%s' % (self.elasticsearch_url, project))
            self.assertNotEqual(result.status_code, requests.codes.ok)

    def test_query_with_two_docs(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Migidae' })
            total = self.datashare_client.query(index = project).get('hits', {}).get('total')
            self.assertEqual(total, 2)

    def test_query_with_three_docs(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Euctenizidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Migidae' })
            total = self.datashare_client.query(index = project).get('hits', {}).get('total')
            self.assertEqual(total, 3)

    def test_query_has_limited_size(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Euctenizidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Migidae' })
            hits = self.datashare_client.query(index = project, size = 1).get('hits', {})
            self.assertEqual(hits['total'], 3)
            self.assertEqual(len(hits['hits']), 1)

    def test_query_is_applied_and_get_all_documents(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Euctenizidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Migidae' })
            total = self.datashare_client.query(index = project, q = 'name:*ae').get('hits', {}).get('total')
            self.assertEqual(total, 3)

    def test_query_is_applied_and_get_one_document(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Euctenizidae' })
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Migidae' })
            total = self.datashare_client.query(index = project, q = 'name:Migi*').get('hits', {}).get('total')
            self.assertEqual(total, 1)

    def test_get_document(self):
        with self.datashare_client.temporary_project() as project:
            self.datashare_client.index(index = project,  document = { '_id': str(uuid.uuid4()), 'name': 'Atypidae' }, id = 'atypidae')
            document = self.datashare_client.document(index = project, id = 'atypidae')
            self.assertEqual(document.get('_source', {}).get('name'), 'Atypidae')
