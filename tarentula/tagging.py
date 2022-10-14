import csv
import re
import requests
from time import sleep
from rich.progress import Progress
from http.cookies import SimpleCookie
from requests.exceptions import HTTPError, ConnectionError

from tarentula.logger import logger

DATASHARE_DOCUMENT_ROUTE = re.compile(r'/#/d/[a-zA-Z0-9_-]+/(\w+)(?:/(\w+))?$')


class Tagger:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 throttle: int = 0,
                 csv_path: str = '',
                 cookies: str = '',
                 apikey: str = None,
                 traceback: bool = False,
                 progressbar: bool = True):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.cookies_string = cookies
        self.apikey = apikey
        self.throttle = throttle
        self.csv_path = csv_path
        self.traceback = traceback
        self.progressbar = progressbar

    @property
    def no_progressbar(self):
        return not self.progressbar

    @property
    def csv_rows(self):
        with open(self.csv_path, newline='', encoding='utf-8-sig') as csv_file:
            return list(self.sanitize_row(row) for row in csv.DictReader(csv_file))

    @property
    def tags(self):
        return list(dict.fromkeys([row['tag'] for row in self.csv_rows]))

    @property
    def documentIds(self):
        return list(dict.fromkeys([row['documentId'] for row in self.csv_rows]))

    @property
    def tree(self):
        tree = dict()
        for row in self.csv_rows:
            # Extract row values
            tag, document_id, routing = (row['tag'], row['documentId'],
                                         row.get('routing', row['documentId']) or row['documentId'],)
            # Append to an existing dictionary or create one
            tree[document_id] = tree[document_id] if document_id in tree else dict(tags=set(), routing=routing,
                                                                                   document_id=document_id)
            # Tags are added to a set so they are unique
            tree[document_id]['tags'].add(tag)
        return tree

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
    def total_steps(self):
        return sum(len(leaf['tags']) for _, leaf in self.tree.items())

    def sleep(self):
        sleep(self.throttle / 1000)

    def sanitize_row(self, row):
        if 'documentUrl' in row:
            groups = DATASHARE_DOCUMENT_ROUTE.findall(row['documentUrl'])
            if len(groups) > 0:
                row['documentId'], row['routing'] = groups[0]
        return row

    def leaf_tagging_endpoint(self, leaf):
        document_id, tags, routing = (leaf['document_id'], leaf['tags'], leaf['routing'])
        # @see https://github.com/ICIJ/datashare/wiki/Datashare-API
        url_template = '{datashare_url}/api/{datashare_project}/documents/tags/{document_id}?routing={routing}'
        return url_template.format(
            datashare_url=self.datashare_url,
            datashare_project=self.datashare_project,
            document_id=document_id,
            routing=routing
        )

    def summarize(self):
        summary = 'Adding %s tags to %s documents' % (len(self.tags), len(self.documentIds))
        logger.info(summary)
        return summary

    
    def start(self):
        with Progress(disable=self.no_progressbar) as progress:     
            desc = self.summarize()
            task = progress.add_task(desc, total=self.total_steps) 
            for document_id, leaf in self.tree.items():
                endpoint_url = self.leaf_tagging_endpoint(leaf)
                for tag in leaf['tags']:
                    try:
                        result = requests.put(endpoint_url, 
                                                json=[tag], 
                                                cookies=self.cookies,
                                                headers=self.headers)
                        result.raise_for_status()
                        if result.status_code == requests.codes.ok:
                            logger.info('Tag "%s" already exists on document "%s"' % (tag, document_id,))
                        elif result.status_code == requests.codes.created:
                            logger.info('Added "%s" to document "%s"' % (tag, document_id,))
                        self.sleep()
                    except (HTTPError, ConnectionError):
                        logger.warning('Unable to add "%s" to document "%s"' % (tag, document_id), exc_info=self.traceback)
                    progress.advance(task)
