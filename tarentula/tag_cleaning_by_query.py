import json
from http.cookies import SimpleCookie

import requests

from tarentula.logger import logger


class TagsCleanerByQuery:
    def __init__(self,
                 datashare_project: str = 'local-datashare',
                 elasticsearch_url: str = 'http://localhost:9200',
                 cookies: str = '',
                 apikey: str = None,
                 traceback: bool = False,
                 wait_for_completion: bool = True,
                 query: str = None):
        if query is None:
            self.query = {"query": {"match_all": {}}}
        elif query.startswith('@'):
            with open(query[1:]) as f:
                self.query = json.loads(f.read())
        else:
            self.query = json.loads(query)
        self.datashare_project = datashare_project
        self.elasticsearch_url = elasticsearch_url
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.wait_for_completion = wait_for_completion

    @property
    def cookies(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.cookies_string)
            return {key: morsel.value for (key, morsel) in cookies.items()}
        except (TypeError, AttributeError):
            return {}

    @property
    def tagging_by_query_endpoint(self):
        url_template = '{elasticsearch_url}/{datashare_project}/_update_by_query?conflicts=proceed'
        return url_template.format(elasticsearch_url=self.elasticsearch_url, datashare_project=self.datashare_project)

    def start(self):
        logger.info("This action will remove all tags for documents matching query")
        script = {"script": {"source": "ctx._source['tags'] = []"}}
        params = {"wait_for_completion": str(self.wait_for_completion).lower()}
        result = requests.post(self.tagging_by_query_endpoint, params=params, json={**script, **self.query},
                               cookies=self.cookies,
                               headers=None if self.apikey is None else {'Authorization': 'bearer %s' % self.apikey})
        result.raise_for_status()
        if self.wait_for_completion:
            logger.info('updated %s documents' % result.json()['updated'])
        else:
            logger.info('task created: [%s]' % result.json()['task'])
        return result
