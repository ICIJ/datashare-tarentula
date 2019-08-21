import csv
import json
import re
import requests
from time import sleep

from tarentula.logger import logger

DATASHARE_DOCUMENT_ROUTE = re.compile(r'/#/d/[a-zA-Z0-9_-]+/(\w+)(?:/(\w+))?$')

class Tagger:
    def __init__(self, datashare_url, datashare_project, throttle, csv_path):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.throttle = throttle
        self.csv_path = csv_path

    @property
    def csv_rows(self):
        with open(self.csv_path, newline='') as csv_file:
            return list(self.sanitize_row(row) for row in csv.DictReader(csv_file))

    @property
    def tags(self):
        return list(dict.fromkeys([ row['tag'] for row in self.csv_rows ]))

    @property
    def documentIds(self):
        return list(dict.fromkeys([ row['documentId'] for row in self.csv_rows ]))

    @property
    def tree(self):
        tree = dict()
        for row in self.csv_rows:
            # Extract row values
            tag, document_id, routing = (row['tag'], row['documentId'], row['routing'] or row['documentId'],)
            # Append to an existing dictionary or create one
            tree[document_id] = tree[document_id] if document_id in tree else dict(tags = set(), routing = routing, document_id = document_id)
            # Tags are added to a set so they are unique
            tree[document_id]['tags'].add(tag)
        return tree

    def sanitize_row(self, row):
        if 'documentUrl' in row:
            groups = DATASHARE_DOCUMENT_ROUTE.findall(row['documentUrl'])
            if len(groups) > 0:
                row['documentId'], row['routing'] = groups[0]
        return row

    def leaf_tagging_endpoint(self, leaf):
        document_id, tags, routing = (leaf['document_id'], leaf['tags'], leaf['routing'])
        url_template = '{datashare_url}/api/document/project/tag/{datashare_project}/{document_id}?routing={routing}'
        return url_template.format(
            datashare_url = self.datashare_url,
            datashare_project = self.datashare_project,
            document_id = document_id,
            routing = routing
        )

    def summarize(self):
        logger.info('Adding %s tags to %s documents' % (len(self.tags), len(self.documentIds)))

    def start(self):
        for document_id, leaf in self.tree.items():
            endpoint_url = self.leaf_tagging_endpoint(leaf)
            data = json.dumps(list(leaf['tags']))
            requests.put(endpoint_url, data = data)
            sleep(self.throttle / 1000)
            for tag in leaf['tags']:
                logger.info('Added "%s" to document "%s"' % (tag, document_id,))
