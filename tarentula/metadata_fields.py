import requests
from json import dumps

from tarentula.datashare_client import urljoin


class MetadataFields:
    def __init__(self,
                 datashare_project: str = 'local-datashare',
                 elasticsearch_url: str = 'http://elasticsearch:9200',
                 filter_by: str = '',
                 type: str = 'Document'):
        self.elasticsearch_url = elasticsearch_url
        self.datashare_project = datashare_project

        if filter_by and "=" in filter_by:
            k, v = [part.strip() for part in filter_by.split("=")]
            self.query_filters = [
                {"term": {f"{k}": f"{v}"}} 
            ]
        else:
            self.query_filters = []

        self.type = type

    def query_mapping(self):
        url = urljoin(self.elasticsearch_url, self.datashare_project)
        return requests.get(url).json()

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

    def start(self):
        mapping = self.query_mapping()
        
        fields = self.get_fields(mapping, [])
        print(dumps(fields))
