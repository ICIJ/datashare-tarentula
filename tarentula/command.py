import json


class Command:
    def __init__(self, query: str, type: str) -> None:
        self.query = query
        self.type = type

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
    def query_body(self):
        if self.query.startswith('@'):
            return self.query_body_from_file
        return self.query_body_from_string

    @property
    def query_body_from_file(self):
        with open(self.query[1:]) as json_file:
            query_body = json.load(json_file)
        return query_body
