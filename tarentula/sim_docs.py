import re
import json
import inquirer

from collections import OrderedDict
from contextlib import contextmanager

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger
from .aggregate import AggCount, NumUnique, DateHistogram

DEFAULT_SOURCE = 'extractionLevel,language,contentType,contentLength:0,extractionDate,path,metadata.tika_metadata_resourcename,metadata.tika_metadata_file_size'
DEFAULT_SORT_BY = '_id'
DEFAULT_ORDER_BY = 'asc'
DEFAULT_FROM = 0
DEFAULT_LIMIT = 10
DEFAULT_SIZE = 100


class SimilarDocs:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 output_file: str = 'similar_docs_query.json',
                 query: str = '*',
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 source: str = DEFAULT_SOURCE,
                 sort_by: str = DEFAULT_SORT_BY,
                 order_by: str = DEFAULT_ORDER_BY,
                 type: str = 'Document',
                 query_field: bool = True):
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.query = query
        self.output_file = output_file
        self.cookies_string = cookies
        self.apikey = apikey
        self.source = source
        self.sort_by = sort_by
        self.order_by = order_by
        self.type = type
        self.query_field = query_field

        self.scroll = None
        self.size = DEFAULT_SIZE
        self.from_ = DEFAULT_FROM
        self.limit = DEFAULT_LIMIT

        self.agg_options = {
            'datashare_url': datashare_url,
            'datashare_project': datashare_project,
            'query': query,
            'cookies': cookies,
            'apikey': apikey,
            'elasticsearch_url': elasticsearch_url,
            'traceback': False,
            'type': 'Document',
            'group_by': 'contentType',
            # 'operation_field': 'contentType',
            # 'run': 'count',
        }
        
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

    def build_query_multiple_terms(self, terms):
        q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "type": self.type
                            }
                        }
                    ],
                    "should": [
                        {
                            "match_phrase": {
                                "content": term
                            }
                        }
                        for term in terms
                    ],
                    "minimum_should_match": 1
                }
            }
        }
        return q

    def build_mlt_query(self, sel_docs, terms, min_term_freq=1, max_query_terms=12):
        like_query_section = [
            {
                "_index": self.datashare_project,
                "_id": doc_id
            }
            for doc_id in sel_docs
        ]
        like_query_section += [term for term in terms]

        q = {
            "query": {
                "more_like_this": {
                "fields": [ "content" ],
                "like": like_query_section,
                "min_term_freq": min_term_freq,
                "max_query_terms": max_query_terms
                }
            }
        }

        return q

    # function that queries for a document by id and returns the content
    def query_doc_content(self, doc_ids):
        index = self.datashare_project
        source = 'content'
        query = {
            "query": {
                "terms": {
                    "_id": doc_ids
                }
            }
        }

        resp = self.datashare_client.query(index, query=query, source=source)
        return resp['hits']['hits']

    @property
    def source_fields(self):
        return [ self.source_field_params(f) for f in self.source.split(',') ]

    @property
    def source_fields_names(self):
        return [ field.pop(0) for field in self.source_fields ]

    def source_field_params(self, field):
        field_params = field.strip().split(':')
        field_name = field_params[0]
        field_default = field_params[1] if len(field_params) > 1 else ''
        return [field_name, field_default]

    def count_matches(self, query_body=None):
        if not query_body:
            query_body = self.query_body
        index = self.datashare_project
        return self.datashare_client.count(index=index, query=query_body).get('count')

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s' % (count, index))
        return count

    def query_all(self, query_body=None, 
                  from_=DEFAULT_FROM, 
                  limit=DEFAULT_LIMIT, 
                  size=DEFAULT_SIZE, 
                  sort_by=DEFAULT_SORT_BY, 
                  order_by=DEFAULT_ORDER_BY):
        
        if not query_body:
            query_body = self.query_body

        sort = {sort_by: order_by}
        docs = self.datashare_client.query_all(
                **{'index': self.datashare_project, 
                   'query': query_body, 
                   'source': self.source_fields_names, 
                   'sort': sort, 
                   'from': from_, 
                   'limit': limit,
                   'size': size})

        return list(docs)
    
    # function pretty prints to console the content of a doc
    def print_doc_content(self, doc):
        text = doc['_source']['content'].lower()
        text = re.sub(r'\s+', ' ', text).strip()
        print(text.splitlines())

    def get_doc_ngrams(self, doc):
        text = doc['_source']['content'].lower()
        text = re.sub(r'\s+', ' ', text).strip()
        words = text.split(" ")
        ngrams = []
        for i in range(len(words)-2):
            ngrams.append(" ".join(words[i:i+3]))
        return ngrams
    
    def get_doc_lines(self, doc):
        text = doc['_source']['content']
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def common_lines(self, docs):
        common_lines = set(self.get_doc_lines(docs[0]))
        for doc in docs[1:]:
            common_lines = common_lines & set(self.get_doc_lines(doc))

        # sort by len desc
        common_lines = sorted(common_lines, key=len, reverse=True)

        return common_lines
    
    def common_ngrams(self, docs):
        docs_ngrams = []
        for doc in docs:
            docs_ngrams += self.get_doc_ngrams(doc)
        common_ngrams = set(docs_ngrams)

        # sort by len desc
        common_ngrams = sorted(common_ngrams, key=len, reverse=True)

        return common_ngrams

    def build_choices_from_docs(self, docs):
        return [f"{doc['_id'][:6]} - {doc['_source']['path']}" for doc in docs]
    
    def ask_user_to_select(self, name, question, choices):
    
        questions = [
            inquirer.Checkbox(name,
                message=question,
                choices=choices,
            ),
        ]
        answers = inquirer.prompt(questions)

        return answers

    
    def ask_user_to_select_docs(self, name, question, documents):

        choices = self.build_choices_from_docs(documents)
        answers = self.ask_user_to_select(name, question, choices)
        sliced_ids = [answer.split(' - ')[0] for answer in answers[name]]
        selected_docs = [doc for doc in documents if doc['_id'][:6] in sliced_ids]

        return selected_docs
    
    def ask_user_to_choose(self, name, question, choices, default_idx=0):

        questions = [
            inquirer.List(name,
                message=question,
                choices=choices,
                default=choices[default_idx],
            ),
        ]

        return inquirer.prompt(questions)

    def print_aggs_by_query(self, query_body=None):
        if not query_body:
            query_body = self.query

        self.agg_options.update({'query': query_body, 'operation_field': 'contentType'})

        NumUnique(**self.agg_options).start()
        AggCount(**self.agg_options).start()

    def start(self):

        documents = self.query_all()        
        print("Num of matches:", self.count_matches())

        # TODO
        # print("Current query results overview :\n"),
        # self.print_aggs_by_query()
        
        # Enter interactive loop
        chat_choices = [
            'No, keep going', 
            'Yes, save current query and leave', 
            'No, give it up',
        ]
        chat_answers = self.ask_user_to_choose('user_chat', 'Is your search good enough for you?', chat_choices, default_idx=0)

        loop_from = DEFAULT_FROM
        loop_limit = DEFAULT_LIMIT
        num_docs_to_show = 10

        query = self.query

        while chat_answers['user_chat'] == 'No, keep going':
            # 1 select interesting docs
            selected_docs = self.ask_user_to_select_docs('first_docs', 'Which docs are you interested in?', documents)

            while len(selected_docs) < 2:
                
                # increase search page
                loop_from += num_docs_to_show

                # show next page of results of query
                logger.debug("Querying next page of results at from=%s, limit=%s" % (loop_from, loop_limit))
                if isinstance(query, str):
                    # query = self.build_mlt_query(selected_docs, [query])
                    query = self.build_query_multiple_terms([query])
                next_docs = self.query_all(query_body=query, from_=loop_from, limit=loop_limit)
                selected_docs = self.ask_user_to_select_docs('next_docs', 'Which docs are you interested in?', next_docs)

            # 2 find commonalities between them
            full_docs = self.query_doc_content([doc['_id'] for doc in selected_docs])
            
            # OPTIONAL
            # # get selected docs metadata
            # # TODO ask user for operation with docs
            # print(full_docs)

            # find common lines between the docs
            commonalities = self.common_lines(full_docs)

            if len(commonalities) == 0:
                print(f"No common lines found between the selected documents. Trying with ngrams")
                
                # find common lines between the docs
                commonalities = self.common_ngrams(full_docs)

            # interact to select few commonalities to search docs
            answers = self.ask_user_to_select(
                'commonalities', 
                'Which common terms found would you like to use to search again?', 
                commonalities)

            # 3 search for commonalities
                
            # run query for the selected commonalities
            # query = self.build_query_multiple_terms(answers['commonalities'])
            query = self.build_mlt_query(
                [doc['_id'] for doc in selected_docs],
                answers['commonalities']
            )
            print(f"Query for commonalities: {query}")

            documents = self.query_all(query_body=query)
            print("Num of matches:", self.count_matches(query_body=query))
            print("Last result documents: %s" % documents)

            # TODO fix it
            # print("Current query results overview :\n"),
            # self.print_aggs_by_query(query_body=query)
 
            # reask to the user if he wants to keep going
            chat_answers = self.ask_user_to_choose('user_chat', 'Is your search good enough for you?', chat_choices, default_idx=0)

        print(chat_answers['user_chat'])
        
        # 4 see if end user is happy with the results
        if chat_answers['user_chat'] == 'Yes, save current query and leave':
            with open(self.output_file, 'w') as f:
                json.dump(f, query, indent=4)
                print("Saved query to file %s" % self.output_file)
        
        elif chat_answers['user_chat'] == 'No, give it up':
            print("Ok, giving up. Bye!")