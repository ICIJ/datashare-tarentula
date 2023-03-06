import requests
from json import dumps

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger
from tarentula.datashare_client import urljoin


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

    def query_mapping(self):
        return self.datashare_client.mappings(self.datashare_project)

    def query_count(self, complete_field_name):
        query_filters = self.query_filters + [{"exists": {"field": complete_field_name}}]
        query={
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
        num_properties = len(mapping[self.datashare_project]['mappings']['properties'])
        logger.info(f"We found {num_properties} properties indexed")

        results = []
        for field, properties in mapping[self.datashare_project]['mappings']['properties'].items():
            complete_field_name = '.'.join(field_stack + [field])
            count = self.query_count(complete_field_name)

            if 'type' in properties:
                if count["count"] > 0:
                    results.append({"field": complete_field_name, "type": properties["type"], "count": count["count"]})
            elif 'properties' in properties:
                results += self.get_fields({self.datashare_project: {
                                    "mappings": mapping[self.datashare_project]['mappings']['properties'][field]}
                                }, 
                                field_stack + [field])
        
        return results

    def start(self):
        mapping = self.query_mapping()
        
        fields = self.get_fields(mapping, [])
        print(dumps(fields))
