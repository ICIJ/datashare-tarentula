from json import dumps

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class MetadataFields:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 elasticsearch_url: str = 'http://elasticsearch:9200',
                 cookies: str = '',
                 apikey: str = None,
                 traceback: bool = False,
                 type: str = 'Document'):
        self.datashare_url = datashare_url
        self.elasticsearch_url = elasticsearch_url
        self.datashare_project = datashare_project
        self.cookies = cookies
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

    def start(self):
        fields = self.datashare_client.metadata_fields(self.datashare_project, documentType=self.type)
        print(dumps(fields))
