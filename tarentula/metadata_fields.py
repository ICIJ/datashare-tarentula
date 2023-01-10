import json

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class Count:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 query: str = '*',
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 traceback: bool = False,
                 type: str = 'Document'):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.type = type
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
        return {
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

    def count_matches(self):
        index = self.datashare_project
        return self.datashare_client.count(index=index, query=self.query_body).get('count')

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s' % (count, index))
        return count

    def start(self):
        count = self.log_matches()
        logger.info('Number of matched elements: %s' % count)
        print('Number of matched elements: %s' % count)
