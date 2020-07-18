import json
import time
import sys
import requests

from http.cookies import SimpleCookie
from tqdm import tqdm

class TaggerByQuery:
    def __init__(self,
                datashare_url,
                datashare_project,
                elasticsearch_url,
                throttle,
                json_path,
                cookies = '',
                traceback = False,
                progressbar = True):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.elasticsearch_url = elasticsearch_url
        self.cookies_string = cookies
        self.throttle = throttle
        self.json_path = json_path
        self.traceback = traceback
        self.progressbar = progressbar

    @property
    def no_progressbar(self):
        return not self.progressbar

    @property
    def cookies(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.cookies_string)
            return {key: morsel.value for (key, morsel) in cookies.items()}
        except (TypeError, AttributeError):
            return {}

    @property
    def tags(self):
        json_file = open(self.json_path, 'r')
        tags = json.loads(json_file.read())
        json_file.close()
        return tags

    @property
    def tagging_by_query_endpoint(self):
        url_template = '{elasticsearch_url}/{datashare_project}/_update_by_query?conflicts=proceed'
        return url_template.format(elasticsearch_url = self.elasticsearch_url,
                                    datashare_project = self.datashare_project)

    def tag_documents(self, tag, query):
        query = {
            "script": {
                "source": """
                    if( !ctx._source.containsKey("tags") ) {
                        ctx._source.tags = [];
                    }
                    if( !ctx._source.tags.contains(params.tag) ) {
                        ctx._source.tags.add(params.tag);
                    }
                """,
                "lang": "painless",
                "params" : {
                    "tag" : tag
                }
            },
            **query
        }
        result = requests.post(self.tagging_by_query_endpoint, json = query, cookies = self.cookies)
        result.raise_for_status()
        return result

    @property
    def tags_count(self):
        return len(self.tags.keys())

    def start(self):
        count = self.tags_count
        pbar = tqdm(self.tags.items(), total=count, desc="This action will add %s tag(s)" % count, file=sys.stdout, disable=self.no_progressbar)
        for (tag, query) in pbar:
            if not self.no_progressbar:
                tqdm.write('Adding "%s" tag' % tag)
                self.tag_documents(tag, query)
