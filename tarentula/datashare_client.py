import requests

from elasticsearch import Elasticsearch, helpers
from uuid import uuid4
from contextlib import contextmanager
from http.cookies import SimpleCookie

def urljoin(*args):
    return '/'.join(s.strip('/') for s in args if s is not None)

class DatashareClient:
    def __init__(self, datashare_url = 'http://localhost:8080', elasticsearch_url = 'http://localhost:9200', cookies = ''):
        self.datashare_url = datashare_url
        self.cookies_string = cookies
        # Instanciate the Elasticsearch client
        self.elasticsearch_url = elasticsearch_url
        self.elasticsearch = Elasticsearch(self.elasticsearch_host)
        # Create the datrashare default index
        self.create()

    @property
    def cookies(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.cookies_string)
            return {key: morsel.value for (key, morsel) in cookies.items()}
        except (TypeError, AttributeError):
            return {}

    @property
    def elasticsearch_host(self):
        if self.elasticsearch_url is not None:
            return self.elasticsearch_url
        else:
            # @see https://github.com/ICIJ/datashare/wiki/Datashare-API
            return urljoin(self.datashare_url, '/api/index/search/')

    @property
    def is_elasticsearch_behind_proxy(self):
        return self.elasticsearch_url is None

    def create(self, index = 'local-datashare'):
        url = urljoin(self.datashare_url, '/api/index/', index)
        return requests.put(url)

    def index(self, index = 'local-datashare', document = {}, id = None, routing = None):
        params = { "routing": routing }
        if id is None:
            url = urljoin(self.elasticsearch_url, index, '/doc?refresh')
            result = requests.post(url, json = document, params = params)
        else:
            url = urljoin(self.elasticsearch_url, index, '/doc/', id, '?refresh')
            result = requests.put(url, json = document, params = params)
        return result.json().get('_id')

    def delete(self, index = 'local-datashare', id = None):
        url = urljoin(self.elasticsearch_url, index, '/doc/', id, '?refresh')
        return requests.delete(url)

    def refresh(self, index = 'local-datashare'):
        url = urljoin(self.elasticsearch_url, index, '/_refresh')
        return requests.post(url)

    def delete_index(self, index):
        url = urljoin(self.elasticsearch_url, index)
        return requests.delete(url)

    def delete_all(self, index):
        url = urljoin(self.elasticsearch_url, index, '_delete_by_query')
        body = { "query": { "match_all": { } } }
        params = { "conflicts": "proceed", "refresh": True }
        return requests.post(url, json = body, params = params)

    def reindex(self, source = 'local-datashare', dest = None, size = 1):
        # Create a default destination index name
        if dest is None: dest = '%s-copy-%s' % (source, uuid4().hex[:6])
        # Source index must at least have one document
        document_id = self.index(source)
        # Copy everything
        json = { "source": { "index": source }, "dest": { "index": dest }, "size": size }
        # Send the request to elasticsearch
        url = urljoin(self.elasticsearch_url, '_reindex')
        result = requests.post(url + '?refresh', json = json)
        # Delete the dummy docs
        self.delete(source, document_id)
        self.delete_all(dest)
        # Return the dest name
        return dest if result.status_code == requests.codes.ok else None

    def query(self, index = 'local-datashare', query = {}, q = None, size = None, offset = 0, _source_includes = None):
        params = { "q": q, "size": size, "from": offset, "_source_includes": _source_includes }
        url = urljoin(self.elasticsearch_host, index, '/doc/_search')
        return requests.post(url, params = params, json = query, cookies = self.cookies).json()

    def scan_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        scroll = '10m'
        return helpers.scan(self.elasticsearch, query = query, scroll = scroll, index = index, doc_type = 'doc', _source_includes = _source_includes)

    def query_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        offset = 0
        response = self.query(offset = offset, size = 25, index = index, query = query, _source_includes = _source_includes)
        while len(response['hits']['hits']) > 0:
            for item in response['hits']['hits']:
                yield item
            offset = offset + len(response['hits']['hits'])
            response = self.query(offset = offset, size = 25, index = index, query = query, _source_includes = _source_includes)

    def scan_or_query_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        if self.is_elasticsearch_behind_proxy:
            return self.query_all(index, query, _source_includes)
        else:
            return self.scan_all(index, query, _source_includes)

    def count(self, index = 'local-datashare', query = {}):
        return self.elasticsearch.count(index = index, body = query)

    def document(self, index = 'local-datashare', id = None, routing = None):
        url = urljoin(self.elasticsearch_url, index, '/doc/', id)
        return requests.get(url, params = { routing: routing }).json()

    def download(self, index = 'local-datashare', id = None, routing = None):
        routing = routing or id
        url = urljoin(self.datashare_url, index, '/documents/src', id)
        return requests.get(url, params = { routing: routing }, stream=True)

    @contextmanager
    def temporary_project(self, source = 'local-datashare', delete = True):
        project = None
        try:
            project = self.reindex(source)
            yield project
        finally:
            if delete and project is not None:
                self.delete_index(project)
        return project
