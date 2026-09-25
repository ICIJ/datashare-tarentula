import sys
from json import dumps

import click
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError

from tarentula.datashare_client import DatashareClient, DATASHARE_DEFAULT_PROJECT, DATASHARE_DEFAULT_URL, \
    ELASTICSEARCH_DEFAULT_URL, elasticsearch_reason
from tarentula.logger import logger


def parse_filters(filter_by):
    filters = []
    for part in filter_by.split(','):
        name, separator, value = part.partition('=')
        if not separator:
            raise click.BadParameter(f'cannot parse filter {part.strip()!r}, '
                                     'expected "field=value" pairs separated by ","')
        filters.append({"term": {name.strip(): value.strip()}})
    return filters


class MetadataFields:
    def __init__(self,
                 datashare_url: str = DATASHARE_DEFAULT_URL,
                 datashare_project: str = DATASHARE_DEFAULT_PROJECT,
                 elasticsearch_url: str = ELASTICSEARCH_DEFAULT_URL,
                 cookies: str = '',
                 apikey: str = None,
                 traceback: bool = False,
                 type: str = 'Document',
                 filter_by: str = '',
                 count: bool = True):
        self.datashare_url = datashare_url
        self.elasticsearch_url = elasticsearch_url
        self.datashare_project = datashare_project
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.type = type
        self.count = count

        self.query_filters = parse_filters(filter_by) if filter_by else []

        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError, RequestsConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            sys.exit(1)

    def query_mappings(self):
        return self.datashare_client.mappings(self.datashare_project)

    def query_field_count(self, complete_field_name):
        query_filters = self.query_filters + [{"exists": {"field": complete_field_name}}]
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "type": self.type
                            }
                        }
                    ],
                    "filter": query_filters
                }
            }
        }
        return self.datashare_client.count(self.datashare_project, query)

    def get_fields(self, mapping, field_stack):
        results = []
        for field, properties in mapping[self.datashare_project]['mappings'].get('properties', {}).items():
            complete_field_name = '.'.join(field_stack + [field])

            if 'type' in properties:
                item = {"field": complete_field_name, "type": properties["type"]}
                if self.count:
                    field_count = self.query_field_count(complete_field_name)
                    if field_count["count"] > 0:
                        item["count"] = field_count["count"]
                        results.append(item)
                else:
                    results.append(item)

            elif 'properties' in properties:
                results += self.get_fields({self.datashare_project: {
                    "mappings": mapping[self.datashare_project]['mappings']['properties'][field]}
                },
                    field_stack + [field])

        return results

    def start(self):
        try:
            fields = self.get_fields(self.query_mappings(), [])
        except HTTPError as error:
            logger.critical('Elasticsearch error: %s', elasticsearch_reason(error), exc_info=self.traceback)
            sys.exit(1)
        print(dumps(fields))
