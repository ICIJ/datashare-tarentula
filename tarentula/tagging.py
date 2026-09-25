import csv
from functools import cached_property
from time import sleep
from urllib.parse import urlparse
import click
from rich.progress import Progress
import requests
from requests.exceptions import HTTPError, RequestException

from tarentula.datashare_client import HTTP_REQUEST_TIMEOUT_SEC, CsrfState, parse_cookies
from tarentula.logger import logger

DOCUMENT_ROUTE_PREFIXES = ('d', 'e', 'ds', 'dm')


def parse_document_url(url):
    fragment = urlparse(url).fragment.split('?')[0].split('#')[0]
    segments = [segment for segment in fragment.split('/') if segment]
    if len(segments) not in (3, 4) or segments[0] not in DOCUMENT_ROUTE_PREFIXES:
        raise click.BadParameter(f'unsupported Datashare document URL: {url}')
    return segments[2], segments[3] if len(segments) == 4 else None


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

    @cached_property
    def csv_rows(self):
        with open(self.csv_path, newline='', encoding='utf-8-sig') as csv_file:
            return [self.sanitize_row(row) for row in csv.DictReader(csv_file)]

    @property
    def tags(self):
        return list(dict.fromkeys([row['tag'] for row in self.csv_rows]))

    @property
    def document_ids(self):
        return list(dict.fromkeys([row['documentId'] for row in self.csv_rows]))

    @cached_property
    def tree(self):
        tree = dict()
        for row in self.csv_rows:
            document_id = row['documentId']
            leaf = tree.setdefault(document_id, dict(tags=set(), routing=None, document_id=document_id))
            leaf['tags'].add(row['tag'])
            leaf['routing'] = leaf['routing'] or row.get('routing')
        for leaf in tree.values():
            leaf['routing'] = leaf['routing'] or leaf['document_id']
        return tree

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
    def _csrf(self):
        return CsrfState(self.datashare_url)

    @property
    def total_steps(self):
        return sum(len(leaf['tags']) for _, leaf in self.tree.items())

    def sleep(self):
        sleep(self.throttle / 1000)

    def sanitize_row(self, row):
        if row.get('documentUrl'):
            document_id, routing = parse_document_url(row['documentUrl'])
            row['documentId'] = document_id
            row['routing'] = routing or row.get('routing')
        if not row.get('documentId'):
            raise click.BadParameter(f'row has no documentId and no usable documentUrl: {row}')
        if not row.get('tag'):
            raise click.BadParameter(f'row has no tag: {row}')
        return row

    def leaf_tagging_endpoint(self, leaf):
        document_id, routing = (leaf['document_id'], leaf['routing'])
        # @see https://github.com/ICIJ/datashare/wiki/Datashare-API
        url_template = '{datashare_url}/api/{datashare_project}/documents/tags/{document_id}?routing={routing}'
        return url_template.format(
            datashare_url=self.datashare_url,
            datashare_project=self.datashare_project,
            document_id=document_id,
            routing=routing
        )

    def summarize(self):
        summary = f'Adding {len(self.tags)} tags to {len(self.document_ids)} documents'
        logger.info(summary)
        return summary

    def start(self):
        failures = 0
        with Progress(disable=self.no_progressbar) as progress:
            desc = self.summarize()
            task = progress.add_task(desc, total=self.total_steps)
            for document_id, leaf in self.tree.items():
                endpoint_url = self.leaf_tagging_endpoint(leaf)
                for tag in leaf['tags']:
                    try:
                        result = self._csrf.request('put', endpoint_url,
                                                    json=[tag],
                                                    cookies=self.cookies,
                                                    headers=self.headers,
                                                    timeout=HTTP_REQUEST_TIMEOUT_SEC)
                        result.raise_for_status()
                        if result.status_code == requests.codes.ok:
                            logger.info('Tag "%s" already exists on document "%s"', tag, document_id)
                        elif result.status_code == requests.codes.created:
                            logger.info('Added "%s" to document "%s"', tag, document_id)
                        self.sleep()
                    except HTTPError as error:
                        failures += 1
                        response = error.response
                        logger.warning('Unable to add "%s" to document "%s" (HTTP %s): %s',
                                       tag, document_id, response.status_code, response.text,
                                       exc_info=self.traceback)
                    except RequestException as error:
                        failures += 1
                        logger.warning('Unable to add "%s" to document "%s": %s',
                                       tag, document_id, error, exc_info=self.traceback)
                    progress.advance(task)
        if failures:
            raise click.ClickException(f'{failures} of {self.total_steps} tagging request(s) failed')
