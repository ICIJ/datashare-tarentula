import json
import sys
import csv

from tarentula.command import Command
from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class Aggregate(Command):
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 query: str = '*',
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 traceback: bool = False,
                 type: str = 'Document',
                 group_by: str = 'contentType',
                 operation_field: str = None,
                 run: str = 'count',
                 calendar_interval: str = 'year',
                 csv_format: bool = True,
                 ):
        super().__init__(query, type)
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.group_by = group_by
        self.run = run
        self.operation_field = operation_field
        self.calendar_interval = calendar_interval
        self.csv_format = csv_format
        self.agg_level_1 = None
        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            sys.exit()

    @property
    def query_body_from_string(self):
        return {
            "aggs": {
                "aggregation-1": self.agg_level_1,
            },
            "query": (super().query_body_from_string['query'])
        }

    def aggregate_matches(self):
        index = self.datashare_project
        return self.datashare_client.query(index=index, query=self.query_body).get('aggregations')

    @staticmethod
    def tabular(agg):
        keys = agg['aggregation-1'].keys()
        spamwriter = csv.writer(sys.stdout, delimiter=',', quotechar='"')
        spamwriter.writerow(keys)
        spamwriter.writerow([f"{agg['aggregation-1'][k]}" for k in keys])

    def start(self):
        agg = self.aggregate_matches()
        if self.csv_format:
            self.tabular(agg)
        else:
            print(json.dumps(agg, indent=4))


class AggCount(Aggregate):

    @property
    def query_body_from_string(self):
        self.agg_level_1 = {
            "aggs": {
                "bucket_truncate": {
                    "bucket_sort": {
                        "from": 0,
                        "size": 25
                    }
                }
            },
            "terms": {
                "field": self.group_by,
                "order": {
                    "_count": "desc"
                },
                "size": 25
            }
        }
        return super().query_body_from_string

    @staticmethod
    def tabular(agg):
        items = agg['aggregation-1']['buckets']
        # get all unique keys
        keys = []
        for item in items:
            keys += item.keys()
        keys = list(set(keys))

        spamwriter = csv.writer(sys.stdout, delimiter=',', quotechar='"')
        spamwriter.writerow(keys)
        for item in items:
            row = [f"{item[k]}" if k in item.keys() else None for k in keys]
            spamwriter.writerow(row)


class NumUnique(Aggregate):

    @property
    def query_body_from_string(self):
        self.agg_level_1 = {
            "cardinality": {
                "field": self.operation_field
            }
        }
        return super().query_body_from_string


class DateHistogram(Aggregate):

    @property
    def query_body_from_string(self):
        self.agg_level_1 = {
            "date_histogram": {
                "field": self.operation_field,
                "calendar_interval": self.calendar_interval
            }
        }
        return super().query_body_from_string

    @staticmethod
    def tabular(agg):
        items = agg['aggregation-1']['buckets']
        
        # get all unique keys
        keys = []
        for item in items:
            keys += item.keys()
        keys = list(set(keys))

        spamwriter = csv.writer(sys.stdout, delimiter=',', quotechar='"')
        spamwriter.writerow(keys)
        for item in items:
            row = [f"{item[k]}" if k in item.keys() else None for k in keys]
            spamwriter.writerow(row)

class GeneralStats(Aggregate):
    """Run one of the following agreggations: 'sum', 'stats', 'string_stats', 'min', 'max', 'avg' """

    @property
    def query_body_from_string(self):
        self.agg_level_1 = {
            self.run: {
                "field": self.operation_field
            }
        }
        return super().query_body_from_string
