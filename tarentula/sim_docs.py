import csv
import json
import inquirer

from collections import OrderedDict
from contextlib import contextmanager

from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger


class SimilarDocs:
    def __init__(self,
                 datashare_url: str = 'http://localhost:8080',
                 datashare_project: str = 'local-datashare',
                 output_file: str = 'tarentula_documents.csv',
                 query: str = '*',
                 cookies: str = '',
                 apikey: str = None,
                 elasticsearch_url: str = None,
                 source: str = 'contentType,contentLength:0,extractionDate,path,metadata.tika_metadata_resourcename',
                 sort_by: str = '_id',
                 order_by: str = 'asc',
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
        self.size = 1000
        self.from_ = 0
        self.limit = 10

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

    def count_matches(self):
        index = self.datashare_project
        return self.datashare_client.count(index=index, query=self.query_body).get('count')

    def log_matches(self):
        index = self.datashare_project
        count = self.count_matches()
        logger.info('%s matching document(s) in %s' % (count, index))
        return count

    def scan_or_query_all(self, query_body=None):
        if not query_body:
            query_body = self.query_body
            
        index = self.datashare_project
        source = self.source_fields_names
        logger.info('Searching document(s) metadata in %s' % index)
        return self.datashare_client.scan_or_query_all(index, source,
                                                        self.sort_by,
                                                        self.order_by,
                                                        self.scroll,
                                                        query_body,
                                                        self.from_, self.limit, self.size)

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
    
    # function pretty prints to console the content of a doc
    def print_doc_content(self, doc):
        text = doc['_source']['content']
        print(doc.splitlines())

    def find_ngrams(self, doc):
        text = doc['_source']['content']
        ngrams = []
        for i in range(len(text)-2):
            ngrams.append(text[i:i+3])
        return ngrams
    
    def find_lines(self, doc):
        text = doc['_source']['content']
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def common_lines(self, docs):
        common_lines = set(self.find_lines(docs[0]))
        for doc in docs[1:]:
            common_lines = common_lines & set(self.find_lines(doc))
        return common_lines
    
    def common_ngrams(self, docs):
        common_ngrams = set(self.find_ngrams(docs[0]))
        for doc in docs[1:]:
            common_ngrams = common_ngrams & set(self.find_ngrams(doc))
        return common_ngrams

    def ask_user_to_choose(self, name, question, choices):
        questions = [
            inquirer.Checkbox(name,
                message=question,
                choices=choices,
            ),
        ]
        return inquirer.prompt(questions)

    def build_query_multiple_terms(self, terms):
        q = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "content": term
                            }
                        }
                        for term in terms
                    ]
                }
            }
        }
        return q

    def build_choices_from_docs(self, docs):
        return [f"{doc['_id'][:6]} - {doc['_source']['path']}" for doc in docs]
                
    def start(self):
        documents = self.scan_or_query_all()
        documents = list(documents)
        document = documents[0]
        print(document)

        choices = self.build_choices_from_docs(documents)
        answers = self.ask_user_to_choose('first_docs', 'Which docs are you interested in?', choices)

        # get sliced ids from answers
        sliced_ids = [answer.split(' - ')[0] for answer in answers['first_docs']]
        selected_docs = [doc for doc in documents if doc.get('_id')[:6] in sliced_ids]

        # get selected docs metadata
        full_docs = self.query_doc_content([doc.get('_id') for doc in selected_docs])
        print(full_docs)

        if len(selected_docs) == 1:
        
            # pretty print doc content
            self.print_doc_content(full_docs[0])

            # select between finding ngrams or entire lines to search another similar doc
            answers = self.ask_user_to_choose('search_type', 
                                            'What would you like to search for?', 
                                            ['ngrams', 'lines'])

            # if ngrams, find ngrams
            if answers['search_type'] == 'ngrams':
                # find ngrams
                possible_search_terms = self.find_ngrams(full_docs[0])
            else:
                # find lines
                possible_search_terms = self.find_lines(full_docs[0])

            print(possible_search_terms)

            # interact for selecting documents
            self.ask_user_to_choose('search_terms', 'Which search term would you like to use?', possible_search_terms)

        elif len(selected_docs) > 1:
            # find common lines between the docs
            commonalities = self.common_lines(full_docs)
            print(commonalities)

            if len(commonalities) == 0:
                print(f"No common lines found between the selected documents. Trying with ngrams")
                
                # find common lines between the docs
                commonalities = self.common_ngrams(full_docs)
                print(commonalities)

            # interact to select few commonalities to search docs
            answers = self.ask_user_to_choose(
                'commonalities', 
                'Which common terms found would you like to use to search again?', 
                commonalities)

            # run query for the selected commonalities
            query = self.build_query_multiple_terms(answers['commonalities'])
            print(f"Query for commonalities: {query}")
            new_docs = self.scan_or_query_all(query_body=query)
            
            self.build_choices_from_docs(new_docs)
            answers = self.ask_user_to_choose('new_docs', 'Which docs are you interested in?', choices)
            # get sliced ids from answers
            sliced_ids = [answer.split(' - ')[0] for answer in answers['new_docs']]
            selected_docs = [doc for doc in new_docs if doc.get('_id')[:6] in sliced_ids]
