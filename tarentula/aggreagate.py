import json

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class Aggregate:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 query: str = '*',
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 traceback: bool = False,
                 type: str = 'Document',
                 by: str = 'contentType',
                 run: str = 'count',
                 ):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.type = type
        self.by = by
        self.run = run
        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            exit()

    @property
    def query_body(self):
        if self.query.startswith('@'):
            return self.query_body_from_file
        else:
            return self.query_body_from_string

    @property
    def query_body_from_string(self):
        operation = "_count" if self.run == "count" else "_nunique"
        return {
            "aggs": {
                "contentType": {
                    "aggs": {
                        "bucket_truncate": {
                            "bucket_sort": {
                                "from": 0,
                                "size": 25
                            }
                        }
                    },
                    "terms": {
                        "field": self.by,
                        "order": {
                            operation: "desc"
                        },
                        "size": 25
                    }
                }
            },
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "type": self.type
                            }
                        },
                        {
                            "query_string": {
                                "query": self.query
                            }
                        }
                    ]
                }
            }
        }
    
    @property
    def query_body_from_file(self):
        with open(self.query[1:]) as json_file:
            query_body = json.load(json_file)
        return query_body

    def aggregate_matches(self):
        index = self.datashare_project
        return self.datashare_client.query(index=index, query=self.query_body).get('aggregations')

    def log_matches(self):
        index = self.datashare_project
        agg = self.aggregate_matches()
        logger.info('%s matching document(s) in %s' % (agg, index))
        return agg

    def start(self):
        agg = self.log_matches()
        logger.info(json.dumps(agg, indent=4))
        print(json.dumps(agg, indent=4))
