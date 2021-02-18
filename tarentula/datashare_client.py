import requests

from contextlib import contextmanager
from datetime import datetime
from http.cookies import SimpleCookie
from uuid import uuid4


def urljoin(*args):
    return '/'.join(s.strip('/') for s in args if s is not None)


DATASHARE_DEFAULT_PROJECT = 'local-datashare'


class DatashareClient:
    def __init__(self, datashare_url='http://localhost:8080', elasticsearch_url=None,
                 datashare_project=DATASHARE_DEFAULT_PROJECT, cookies='', apikey=None):
        self.datashare_url = datashare_url
        self.cookies_string = cookies
        self.apikey = apikey
        self.elasticsearch_url = elasticsearch_url
        # Create the datashare default index
        self.create(datashare_project)

    @property
    def cookies(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.cookies_string)
            return {key: morsel.value for (key, morsel) in cookies.items()}
        except (TypeError, AttributeError):
            return {}

    @property
    def headers(self):
        if self.apikey is None:
            return None
        else:
            return {'Authorization': 'bearer %s' % self.apikey}

    @property
    def elasticsearch_host(self):
        if self.elasticsearch_url is not None:
            return self.elasticsearch_url
        else:
            # @see https://github.com/ICIJ/datashare/wiki/Datashare-API
            return urljoin(self.datashare_url, '/api/index/search/')

    def create(self, index=DATASHARE_DEFAULT_PROJECT):
        url = urljoin(self.datashare_url, '/api/index/', index)
        return requests.put(url)

    def index(self, index=DATASHARE_DEFAULT_PROJECT, document=None, id=None, routing=None):
        if document is None:
            document = {}
        params = {'routing': routing}
        # Clone the document to perform changes
        document = dict(document)
        # Elasticsearch doesn't allow passing the _id as a property in the document
        if '_id' in document:
            document.pop('_id', None)
        if '_routing' in document:
            document.pop('_routing', None)
        # When no id is provided, we use POST method (to create the resource)
        if 'content' in document:
            content_length = len(document.get('content', ''))
            document.update({'contentLength': content_length})
        now = datetime.now()
        extraction_date = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        document.update({'extractionDate': extraction_date})
        if id is None:
            url = urljoin(self.elasticsearch_url, index, '/_doc?refresh')
            result = requests.post(url, json=document, params=params)
        # When an id is provided, we use PUT method (to update the resource)
        else:
            if routing is None:
                query_params = '?refresh'
            else:
                query_params = '?refresh&routing=' + routing
            url = urljoin(self.elasticsearch_url, index, '/_doc/', id, query_params)
            result = requests.put(url, json=document, params=params)
        result.raise_for_status()
        return result.json().get('_id')

    def delete(self, index=DATASHARE_DEFAULT_PROJECT, id=None):
        url = urljoin(self.elasticsearch_url, index, '/_doc/', id, '?refresh')
        return requests.delete(url)

    def refresh(self, index=DATASHARE_DEFAULT_PROJECT):
        url = urljoin(self.elasticsearch_url, index, '/_refresh')
        return requests.post(url)

    def delete_index(self, index):
        url = urljoin(self.elasticsearch_url, index)
        return requests.delete(url)

    def delete_all(self, index):
        url = urljoin(self.elasticsearch_url, index, '_delete_by_query')
        body = {"query": {"match_all": {}}}
        params = {"conflicts": "proceed", "refresh": True}
        return requests.post(url, json=body, params=params)

    def reindex(self, source=DATASHARE_DEFAULT_PROJECT, dest=None, size=1):
        # Create a default destination index name
        if dest is None:
            dest = '%s-copy-%s' % (source, uuid4().hex[:6])
        # Source index must at least have one document
        document_id = self.index(source, document={"content": "This is a temporary document", "tags": ["tmp"]})
        # Copy everything
        json = {"source": {"index": source}, "dest": {"index": dest}, "size": size}
        # Send the request to elasticsearch
        url = urljoin(self.elasticsearch_url, '_reindex')
        result = requests.post(url + '?refresh', json=json)
        # Delete the dummy docs
        self.delete(source, document_id)
        self.delete(dest, document_id)
        self.delete_all(dest)
        # Return the dest name
        return dest if result.status_code == requests.codes.ok else None

    def query(self, index=DATASHARE_DEFAULT_PROJECT, query={}, q=None, source=None, scroll=None, **kwargs):
        local_query = {"sort": {"_id": "asc"}, **query, **kwargs}
        if source is not None:
            local_query.update({'_source': source})
        url = urljoin(self.elasticsearch_host, index, '/_doc/_search')
        response = requests.post(url, params={"q": q, "scroll": scroll},
                                 json=local_query,
                                 headers=self.headers,
                                 cookies=self.cookies)
        response.raise_for_status()
        return response.json()

    def scroll(self, scroll_id, scroll=None):
        url = urljoin(self.elasticsearch_host, '/_search/scroll')
        body = {"scroll_id": scroll_id, "scroll": scroll}
        response = requests.post(url, json=body,
                                 cookies=self.cookies,
                                 headers=self.headers)
        response.raise_for_status()
        return response.json()

    def scan_all(self, scroll='10m', **kwargs):
        response = self.query(scroll=scroll, **kwargs)
        while len(response['hits']['hits']) > 0:
            for item in response['hits']['hits']:
                yield item
            if '_scroll_id' not in response:
                break
            scroll_id = response['_scroll_id']
            response = self.scroll(scroll_id, scroll)

    def query_all(self, **kwargs):
        response = self.query(**kwargs)
        while len(response['hits']['hits']) > 0:
            for item in response['hits']['hits']:
                yield item
            search_after = response['hits']['hits'][-1]['sort']
            response = self.query(search_after=search_after, **kwargs)

    def count(self, index=DATASHARE_DEFAULT_PROJECT, query={}):
        url = urljoin(self.elasticsearch_host, index, '_count')
        return requests.post(url, json=query,
                             cookies=self.cookies,
                             headers=self.headers).json()

    def document(self, index=DATASHARE_DEFAULT_PROJECT, id=None, routing=None, source=None):
        url = urljoin(self.elasticsearch_host, index, '/_doc/', id)
        params = {'routing': routing, '_source': source}
        return requests.get(url, params=params,
                            cookies=self.cookies,
                            headers=self.headers).json()

    def download(self, index=DATASHARE_DEFAULT_PROJECT, id=None, routing=None):
        routing = routing or id
        url = urljoin(self.datashare_url, 'api', index, '/documents/src', id)
        return requests.get(url, params={'routing': routing},
                            cookies=self.cookies,
                            headers=self.headers,
                            stream=True)

    def document_url(self, index=DATASHARE_DEFAULT_PROJECT, id='', routing=None):
        routing = id if routing is None else routing
        return urljoin(self.datashare_url, f'#/d/{index}/{id}/{routing}')

    @contextmanager
    def temporary_project(self, source=DATASHARE_DEFAULT_PROJECT, delete=True):
        project = None
        try:
            project = self.reindex(source)
            yield project
        finally:
            if delete and project is not None:
                self.delete_index(project)
        return project
