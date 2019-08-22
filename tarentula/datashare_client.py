import requests

from uuid import uuid4
from contextlib import contextmanager

class DatashareClient:
    def __init__(self, datashareUrl = 'http://localhost:8080', elasticsearchUrl = 'http://localhost:9200'):
        self.datashareUrl = datashareUrl
        self.elasticsearchUrl = elasticsearchUrl
        # Create the datrashare default index
        self.create()

    def create(self):
        return requests.put('%s/api/index/create' % self.datashareUrl)

    def index(self, index = 'local-datashare', document = {}, id = None, routing = None):
        params = { "routing": routing }
        if id is None:
            result = requests.post('%s/%s/doc?refresh' % (self.elasticsearchUrl, index), json = document, params = params)
        else:
            result = requests.put('%s/%s/doc/%s?refresh' % (self.elasticsearchUrl, index, id), json = document, params = params)
        return result.json().get('_id')

    def delete(self, index = 'local-datashare', id = None):
        return requests.delete('%s/%s/doc/%s?refresh' % (self.elasticsearchUrl, index, id))

    def refresh(self, index = 'local-datashare'):
        return requests.post('%s/%s/_refresh' % (self.elasticsearchUrl, index))

    def delete_index(self, index):
        return requests.delete('%s/%s' % (self.elasticsearchUrl, index))

    def reindex(self, source = 'local-datashare', dest = None):
        # Create a default destination index name
        if dest is None: dest = '%s-copy-%s' % (source, uuid4().hex[:6])
        # Source index must at least have one document
        document_id = self.index(source)
        # Copy everything
        json = { "source": { "index": source }, "dest": { "index": dest } }
        # Send the request to elasticsearch
        result = requests.post('%s/_reindex' % self.elasticsearchUrl, json = json)
        # Delete the dummy docs
        self.delete(source, document_id)
        self.delete(dest, document_id)
        # Return the dest name
        return dest if result.status_code == requests.codes.ok else None

    def query(self, index = 'local-datashare', q = None, size = None):
        params = { "q": q, "size": size }
        return requests.get('%s/%s/_search' % (self.elasticsearchUrl, index), params = params).json()

    @contextmanager
    def temporary_project(self, source = 'local-datashare'):
        try:
            project = self.reindex(source)
            yield project
        finally:
            self.delete_index(project)
