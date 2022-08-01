import json
import requests

from http.cookies import SimpleCookie
from requests.exceptions import HTTPError, ConnectionError
from time import sleep
from rich.progress import Progress

from tarentula.logger import logger


class TaggerByQuery:
    def __init__(self,
                 datashare_project: str = '',
                 elasticsearch_url: str = '',
                 json_path: str = '',
                 throttle: int = 0,
                 cookies: str = '',
                 apikey: str = None,
                 progressbar: bool = True,
                 traceback: bool = False,
                 wait_for_completion: bool = True,
                 scroll_size: int = 1000):
        self.datashare_project = datashare_project
        self.elasticsearch_url = elasticsearch_url
        self.cookies_string = cookies
        self.apikey = apikey
        self.throttle = throttle
        self.json_path = json_path
        self.traceback = traceback
        self.progressbar = progressbar
        self.wait_for_completion = wait_for_completion
        self.scroll_size = scroll_size

    @property
    def no_progressbar(self):
        return not self.progressbar

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
        if self.apikey is not None:
            return {
                'Authorization': 'bearer %s' % self.apikey
            }

    @property
    def tags(self):
        json_file = open(self.json_path, 'r')
        tags = json.loads(json_file.read())
        json_file.close()
        return tags

    @property
    def tagging_by_query_endpoint(self):
        url_template = '{elasticsearch_url}/{datashare_project}/_update_by_query?conflicts=proceed'
        return url_template.format(elasticsearch_url=self.elasticsearch_url, datashare_project=self.datashare_project)

    def sleep(self):
        sleep(self.throttle / 1000)

    def task_url(self, task):
        url_template = '{elasticsearch_url}/_tasks/{task}'
        return url_template.format(elasticsearch_url=self.elasticsearch_url, task=task)

    def tag_query_as_dict(self, query):
        if isinstance(query, str):
            return { 
                "query": {
                    "query_string": {
                        "query": query
                    }
                }
            }
        return query

    def tag_documents(self, tag, query):
        query = {
            "script": {
                "source": """
                    if( !ctx._source.containsKey("tags") ) {
                        ctx._source.tags = [];
                    }
                    if( !ctx._source.tags.contains(params.tag) ) {
                        ctx._source.tags.add(params.tag);
                    }
                """,
                "lang": "painless",
                "params": {
                    "tag": tag
                },
            },
            **self.tag_query_as_dict(query)
        }
        params = {
            "wait_for_completion": str(self.wait_for_completion).lower(),
            "scroll_size": self.scroll_size,
        }
        result = requests.post(self.tagging_by_query_endpoint, 
                                params=params, 
                                json=query, 
                                cookies=self.cookies,
                                headers=self.headers)
        result.raise_for_status()
        return result

    @property
    def tags_count(self):
        return len(self.tags.keys())

    def start(self):
        count = self.tags_count
        desc = "This action will add %s tag(s)" % count
        with Progress(disable=self.no_progressbar) as progress:  
            task = progress.add_task(desc, total=count)
            for (tag, query) in self.tags.items():
                try:
                    progress.console.print('Adding "%s" tag' % tag)
                    result = self.tag_documents(tag, query).json()
                    if self.wait_for_completion:
                        progress.console.print('└── documents updated in %sms' % result['took'])
                        logger.info('Documents tagged with [%s] in %sms' % (tag, result['took']))
                    else:
                        progress.console.print('└── task created: %s' % self.task_url(result['task']))
                        logger.info('Task [%s] created for tag [%s]' % (result['task'], tag))
                    progress.advance(task)
                    self.sleep()
                except (HTTPError, ConnectionError):
                    logger.error('Unable to add tag [%s] (connection error)' % tag, exc_info=self.traceback)
