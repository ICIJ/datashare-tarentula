import requests

from elasticsearch import Elasticsearch, helpers
from uuid import uuid4
from contextlib import contextmanager
from http.cookies import SimpleCookie

def urljoin(*args):
    return '/'.join(s.strip('/') for s in args if s is not None)

class DatashareClient:
    def __init__(self, datashare_url = 'http://localhost:8080', elasticsearch_url = None, cookies = '', scroll =  '10m'):
        self.datashare_url = datashare_url
        self.cookies_string = cookies
        self.scroll = scroll
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
        self.delete(dest, document_id)
        self.delete_all(dest)
        # Return the dest name
        return dest if result.status_code == requests.codes.ok else None

    def query(self, index = 'local-datashare', query = {}, search_after = None, q = None, size = None, _source_includes = None):
        local_query = {
            "size": size,
            "_source": _source_includes,
            "sort": { "_id": "asc" }
        }
        if search_after is not None:
            local_query["search_after"] = search_after
        url = urljoin(self.elasticsearch_host, index, '/doc/_search')
        response = requests.post(url, params = { "q": q }, json = { **local_query, **query }, cookies = self.cookies)
        response.raise_for_status()
        return response.json()

    def scan_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        return helpers.scan(self.elasticsearch, query = query, scroll = self.scroll, index = index, doc_type = 'doc', _source_includes = _source_includes, request_timeout = 60)

    def query_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        search_after = None
        response = self.query(search_after = search_after, size = 25, index = index, query = query, _source_includes = _source_includes)
        while len(response['hits']['hits']) > 0:
            for item in response['hits']['hits']:
                yield item
            search_after = response['hits']['hits'][-1]['sort']
            response = self.query(search_after = search_after, size = 25, index = index, query = query, _source_includes = _source_includes)


    def scan_or_query_all(self, index = 'local-datashare', query = {}, _source_includes = None):
        if self.is_elasticsearch_behind_proxy:
            return self.query_all(index, query, _source_includes)
        else:
            return self.scan_all(index, query, _source_includes)

    def count(self, index = 'local-datashare', query = {}):
        url = urljoin(self.datashare_url, '/api/index/search/', index, '_count')
        return requests.post(url, json = query, cookies = self.cookies).json()

    def document(self, index = 'local-datashare', id = None, routing = None):
        url = urljoin(self.datashare_url, '/api/index/search/', index, '/doc/', id)
        return requests.get(url, params = { "routing": routing }, cookies = self.cookies).json()

    def download(self, index = 'local-datashare', id = None, routing = None):
        routing = routing or id
        url = urljoin(self.datashare_url, 'api', index, '/documents/src', id)
        return requests.get(url, params = { "routing": routing }, cookies = self.cookies, stream = True)

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
