import json

from functools import cached_property
from time import sleep
from requests.exceptions import HTTPError, RequestException
from rich.progress import Progress
import click
import requests

from tarentula.datashare_client import HTTP_REQUEST_TIMEOUT_SEC, parse_cookies
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
        return parse_cookies(self.cookies_string)

    @property
    def headers(self):
        if self.apikey is not None:
            return {
                'Authorization': f'bearer {self.apikey}'
            }
        return None

    @cached_property
    def tags(self):
        with open(self.json_path, 'r') as json_file:
            tags = json.loads(json_file.read())
            if not isinstance(tags, dict):
                raise click.BadParameter(f'{self.json_path} must hold a JSON object mapping each tag to a query')
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
                    def tags = ctx._source.tags;
                    if( !(tags instanceof List) ) {
                        ctx._source.tags = tags == null ? [] : [tags];
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
                               headers=self.headers,
                               timeout=HTTP_REQUEST_TIMEOUT_SEC)
        result.raise_for_status()
        return result

    @property
    def tags_count(self):
        return len(self.tags.keys())

    def start(self):
        count = self.tags_count
        failures = 0
        desc = f'This action will add {count} tag(s)'
        with Progress(disable=self.no_progressbar) as progress:
            task = progress.add_task(desc, total=count)
            for (tag, query) in self.tags.items():
                try:
                    progress.console.print(f'Adding "{tag}" tag')
                    result = self.tag_documents(tag, query).json()
                    if self.wait_for_completion:
                        progress.console.print(f'└── documents updated in {result["took"]}ms')
                        logger.info('Documents tagged with [%s] in %sms', tag, result['took'])
                    else:
                        progress.console.print(f'└── task created: {self.task_url(result["task"])}')
                        logger.info('Task [%s] created for tag [%s]', result['task'], tag)
                    progress.advance(task)
                    self.sleep()
                except HTTPError as error:
                    failures += 1
                    logger.error('Unable to add tag [%s] (HTTP %s): %s', tag,
                                 error.response.status_code, error.response.text, exc_info=self.traceback)
                except RequestException as error:
                    failures += 1
                    logger.error('Unable to add tag [%s]: %s', tag, error, exc_info=self.traceback)
        if failures:
            raise click.ClickException(f'{failures} of {count} tagging request(s) failed')
