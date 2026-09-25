import json

import click


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
        body = self.query_body_from_string
        if self.query.startswith('@'):
            body['query']['bool']['must'][1] = self.query_body_from_file.get('query', self.query_body_from_file)
        return body

    @property
    def query_body_from_file(self):
        try:
            with open(self.query[1:]) as json_file:
                return json.load(json_file)
        except FileNotFoundError as exc:
            raise click.BadParameter(f'no such query file: {self.query[1:]}', param_hint='--query') from exc
