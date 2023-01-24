import requests
from json import dumps

from tarentula.datashare_client import urljoin
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
                 type: str = 'Document',
                 count: bool = True):
        self.datashare_url = datashare_url
        self.elasticsearch_url = elasticsearch_url
        self.datashare_project = datashare_project
        self.cookies_string = cookies
        self.apikey = apikey
        self.traceback = traceback
        self.type = type
        self.count = count

    def query_mapping(self):
        url = urljoin(self.elasticsearch_url, self.datashare_project)
        return requests.get(url).json()

    def query_count(self, complete_field_name):
        query={
            "query": {"bool": {"must": {"match": {"type": self.type}},
                                "filter": {"exists": {"field": complete_field_name}}}}
        }
        url = urljoin(self.elasticsearch_url, self.datashare_project, '_count')
        return requests.post(url, json=query).json()

    def get_fields(self, mapping, field_stack):
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

    def query_mappings(self):
        return self.datashare_client.mappings(self.datashare_project)

    def query_field_count(self, complete_field_name):
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
                    "filter": complete_field_name
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

            if 'type' in properties:
                item = {"field": complete_field_name, "type": properties["type"] }
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
        mapping = self.query_mappings()        
        
        fields = self.get_fields(mapping, [])
        print(dumps(fields))
