import re
import json
import shutil
import sys
import inquirer

from requests.exceptions import HTTPError
from urllib3.exceptions import ProtocolError

from tarentula.command import Command
from tarentula.datashare_client import DatashareClient
from tarentula.logger import logger

DEFAULT_SOURCE = 'extractionLevel,language,contentType,contentLength:0,extractionDate,path,metadata.tika_metadata_resourcename,metadata.tika_metadata_file_size'
DEFAULT_SORT_BY = '_id'
DEFAULT_ORDER_BY = 'asc'
DEFAULT_FROM = 0
DEFAULT_LIMIT = 10
DEFAULT_SIZE = 100
MIN_COMMONALITIES_TO_OFFER = 2
ANSI_RED = '\033[31m'
ANSI_RESET = '\033[0m'

# File-size buckets used to let the user narrow results by contentLength.
# Each entry is (label, gte, lt) in bytes; None means unbounded. `from` is
# inclusive and `to` exclusive, matching Elasticsearch range semantics.
SIZE_RANGES = [
    ('< 10 KB', None, 10_000),
    ('10 KB - 100 KB', 10_000, 100_000),
    ('100 KB - 1 MB', 100_000, 1_000_000),
    ('> 1 MB', 1_000_000, None),
]
SIZE_RANGE_BY_LABEL = {label: (gte, lt) for (label, gte, lt) in SIZE_RANGES}

# Doc-picker row layout: every column except `blurb` is a fixed width, so the
# table stays predictable regardless of terminal size. `blurb` absorbs
# whatever width is left -- down to 0 on a narrow terminal -- so the row
# never exceeds the available width (overflowing wraps the printed line,
# which breaks inquirer's cursor-repaint math, see CHECKBOX_PREFIX_WIDTH).
COL_SEP = '  '
ID_WIDTH = 6
TYPE_WIDTH = 16
LANG_WIDTH = 10
SIZE_WIDTH = 8
NAME_WIDTH = 22
FALLBACK_TERMINAL_WIDTH = 80

# inquirer prints "  [ ] " / "> [ ] " (7 visible chars: leading space +
# 1-char selector + space + "[ ]"/"[X]" + space) before every checkbox
# choice line (see inquirer.render.console._checkbox.get_options and
# console.__init__.print_line). Row content must leave room for it, or the
# printed line wraps past the terminal width and breaks inquirer's
# cursor-repaint math (it moves the cursor up by choice count, not actual
# physical line count) -- producing stacked/duplicated prompt frames.
CHECKBOX_PREFIX_WIDTH = 7


class SimilarDocs(Command):
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
                 traceback: bool = False,
                 max_query_terms: int = 30,
                 min_term_freq: int = 1,
                 min_doc_freq: int = 10,
                 min_word_length: int = 4,
                 minimum_should_match: str = '30%'):
        super().__init__(query, type)
        self.datashare_url = datashare_url
        self.datashare_project = datashare_project
        self.output_file = output_file
        self.cookies_string = cookies
        self.apikey = apikey
        self.source = source
        self.sort_by = sort_by
        self.order_by = order_by
        self.traceback = traceback
        self.max_query_terms = max_query_terms
        self.min_term_freq = min_term_freq
        self.min_doc_freq = min_doc_freq
        self.min_word_length = min_word_length
        self.minimum_should_match = minimum_should_match

        try:
            self.datashare_client = DatashareClient(datashare_url,
                                                    elasticsearch_url,
                                                    datashare_project,
                                                    cookies,
                                                    apikey)
        except (ConnectionRefusedError, ConnectionError):
            logger.critical('Unable to connect to Datashare', exc_info=self.traceback)
            sys.exit()

    @staticmethod
    def term_clause(term):
        return {"match_phrase": {"content": term}}

    def build_mlt_query(self, sel_docs, liked_terms, unliked_docs=None, unliked_terms=None):
        """`more_like_this` only ever holds doc refs (it's a fuzzy "find docs
        shaped like these" signal) and is the query's sole `must`. Picked terms
        don't get ANDed onto it -- with several picked terms that zeroes the
        result set fast -- they're `should` clauses instead, gated by the same
        `minimum_should_match` used to tune MLT itself: "match at least this
        fraction of the terms", not all of them. Unliked terms stay a hard
        `must_not`. Mixing raw strings into MLT's like/unlike, as before, just
        feeds its term extractor diluted by max_query_terms/minimum_should_match,
        so a doc could match without ever containing the term you picked."""
        def doc_ref(doc_id):
            return {"_index": self.datashare_project, "_id": doc_id}

        mlt = {
            "more_like_this": {
                "like": [doc_ref(doc_id) for doc_id in sel_docs],
                "unlike": [doc_ref(doc_id) for doc_id in (unliked_docs or [])],
                # keep the seed docs in the results: the saved query must retrieve them too
                "include": True,
                "fields": ["content"],
                "min_term_freq": self.min_term_freq,
                "max_query_terms": self.max_query_terms,
                "min_doc_freq": self.min_doc_freq,
                "min_word_length": self.min_word_length,
                "minimum_should_match": self.minimum_should_match,
            }
        }

        q = {"query": {"bool": {"must": [mlt]}}}
        if liked_terms:
            q["query"]["bool"]["should"] = [self.term_clause(term) for term in liked_terms]
            q["query"]["bool"]["minimum_should_match"] = self.minimum_should_match
        if unliked_terms:
            q["query"]["bool"]["must_not"] = [self.term_clause(term) for term in unliked_terms]

        return q

    @staticmethod
    def _find_more_like_this(node):
        """Locate the more_like_this clause inside a query body, however deep
        facet filters have nested it (build_facet_filter_query wraps in bool/must)."""
        if isinstance(node, dict):
            if 'more_like_this' in node:
                return node['more_like_this']
            for value in node.values():
                found = SimilarDocs._find_more_like_this(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = SimilarDocs._find_more_like_this(item)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _find_owning_bool(node):
        """Locate the bool clause built by build_mlt_query -- the one whose
        `must` holds the more_like_this clause directly -- however deep facet
        filters have nested it."""
        if isinstance(node, dict):
            bool_clause = node.get('bool')
            if isinstance(bool_clause, dict):
                must = bool_clause.get('must', [])
                if any(isinstance(item, dict) and 'more_like_this' in item for item in must):
                    return bool_clause
            for value in node.values():
                found = SimilarDocs._find_owning_bool(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = SimilarDocs._find_owning_bool(item)
                if found is not None:
                    return found
        return None

    def refresh_unlike(self, query_body, unliked_ids, unliked_terms):
        """Patch the query's more_like_this.unlike doc refs and the owning
        bool's must_not term clauses in place with this round's exclusions, so
        the printed/saved query reflects marks just made instead of only
        taking effect on the next rebuilt query."""
        mlt = self._find_more_like_this(query_body)
        if mlt is not None:
            mlt['unlike'] = [{"_index": self.datashare_project, "_id": doc_id}
                              for doc_id in unliked_ids]
        bool_clause = self._find_owning_bool(query_body)
        if bool_clause is not None:
            if unliked_terms:
                bool_clause['must_not'] = [self.term_clause(term) for term in unliked_terms]
            else:
                bool_clause.pop('must_not', None)

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

        resp = self.datashare_client.query(index, query=query, source=source, size=len(doc_ids))
        return resp['hits']['hits']
    
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

    def get_doc_ngrams(self, doc, n=3):
        text = (doc['_source'].get('content') or '').lower()
        text = re.sub(r'\s+', ' ', text).strip()
        words = text.split(" ")
        ngrams = []
        for i in range(len(words)-n+1):
            ngrams.append(" ".join(words[i:i+n]))
        return ngrams
    
    def get_doc_lines(self, doc):
        text = doc['_source'].get('content') or ''
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def common_lines(self, docs):
        common_lines = set(self.get_doc_lines(docs[0]))
        for doc in docs[1:]:
            common_lines = common_lines & set(self.get_doc_lines(doc))

        # sort by len desc
        common_lines = sorted(common_lines, key=len, reverse=True)

        return common_lines
    
    def common_ngrams(self, docs, n=3):
        common_ngrams = set(self.get_doc_ngrams(docs[0], n=n))
        for doc in docs[1:]:
            common_ngrams = common_ngrams & set(self.get_doc_ngrams(doc, n=n))

        # sort by len desc
        common_ngrams = sorted(common_ngrams, key=len, reverse=True)

        return common_ngrams

    @staticmethod
    def doc_name(doc):
        return doc['_source'].get('path', '').rsplit('/', 1)[-1] or doc['_id']

    @staticmethod
    def content_width_for_checkbox(terminal_width):
        """Terminal width available for row content once inquirer's checkbox
        marker prefix (see CHECKBOX_PREFIX_WIDTH) is reserved."""
        return max(1, terminal_width - CHECKBOX_PREFIX_WIDTH)

    @staticmethod
    def column_widths(total_width):
        """Fixed per-column widths; only `blurb` grows with the terminal."""
        fixed_width = (ID_WIDTH + TYPE_WIDTH + LANG_WIDTH + SIZE_WIDTH + NAME_WIDTH
                       + 5 * len(COL_SEP))
        blurb_width = max(0, total_width - fixed_width)
        return {'id': ID_WIDTH, 'type': TYPE_WIDTH, 'lang': LANG_WIDTH,
                'size': SIZE_WIDTH, 'name': NAME_WIDTH, 'blurb': blurb_width}

    @staticmethod
    def format_header_row(widths):
        return COL_SEP.join([
            f"{'id':<{widths['id']}}",
            f"{'type':<{widths['type']}}",
            f"{'lang':<{widths['lang']}}",
            f"{'size':>{widths['size']}}",
            f"{'name':<{widths['name']}}",
            'blurb'[:widths['blurb']],
        ])

    @staticmethod
    def format_doc_row(doc, blurb, widths):
        src = doc['_source']
        size_kb = f"{(int(src.get('contentLength') or 0)) // 1024} KB"
        return COL_SEP.join([
            f"{doc['_id']:<{widths['id']}.{widths['id']}}",
            f"{src.get('contentType', '?'):<{widths['type']}.{widths['type']}}",
            f"{src.get('language', '?'):<{widths['lang']}.{widths['lang']}}",
            f"{size_kb:>{widths['size']}}",
            f"{SimilarDocs.doc_name(doc):<{widths['name']}.{widths['name']}}",
            blurb[:widths['blurb']],  # last column: no padding, just cut
        ])

    @staticmethod
    def build_doc_choices(docs, contents_by_id, widths):
        """(row_string, doc) pairs, in `docs` order; row_string doubles as the checkbox
        label and the lookup key back to its doc."""
        choices = []
        for doc in docs:
            blurb = re.sub(r'\s+', ' ', contents_by_id.get(doc['_id'], '')).strip()
            choices.append((SimilarDocs.format_doc_row(doc, blurb, widths), doc))
        return choices

    def ask_user_to_select(self, name, question, choices, default=None):

        questions = [
            inquirer.Checkbox(name,
                message=question,
                choices=choices,
                default=default,
            ),
        ]
        answers = inquirer.prompt(questions)

        # ponytail: Ctrl-C makes prompt() return None; keep the pre-checked defaults
        return answers or {name: list(default or [])}

    NEXT_PAGE_CHOICE = '▸ Show next page of results'

    def paginated_doc_picker(self, name, question, query_body, from_=DEFAULT_FROM, limit=DEFAULT_LIMIT):
        """Checkbox doc picker where the user can keep checking NEXT_PAGE_CHOICE
        to browse further pages before submitting. Picks made on earlier pages
        are kept, shown pre-checked when a page is revisited (pagination wraps
        around), and can be unchecked there to drop them."""
        picked_by_id = {}
        while True:
            page_docs = self.query_all(query_body=query_body, from_=from_, limit=limit)
            if not page_docs:
                if from_ == DEFAULT_FROM:
                    return list(picked_by_id.values())
                print("No more results for the current query; wrapping to the first page.")
                from_ = DEFAULT_FROM
                continue

            contents = {d['_id']: d['_source'].get('content') or ''
                        for d in self.query_doc_content([doc['_id'] for doc in page_docs])}
            terminal_width = shutil.get_terminal_size(fallback=(FALLBACK_TERMINAL_WIDTH, 24)).columns
            widths = self.column_widths(self.content_width_for_checkbox(terminal_width))

            print(' ' * CHECKBOX_PREFIX_WIDTH + self.format_header_row(widths))
            choice_pairs = self.build_doc_choices(page_docs, contents, widths)
            row_choices = [row for row, _ in choice_pairs]
            # a partial page proves there's nothing more to fetch; only offer to
            # page further when this page came back full (there may be more)
            if len(page_docs) == limit:
                row_choices += [self.NEXT_PAGE_CHOICE]
            defaults = [row for row, doc in choice_pairs if doc['_id'] in picked_by_id]
            answers = self.ask_user_to_select(name, question, row_choices, default=defaults)[name]

            # sync this page's checkboxes: check = keep/add, uncheck = drop
            for row, doc in choice_pairs:
                if row in answers:
                    picked_by_id[doc['_id']] = doc
                else:
                    picked_by_id.pop(doc['_id'], None)

            if self.NEXT_PAGE_CHOICE not in answers:
                return list(picked_by_id.values())
            from_ += limit

    def ask_user_to_choose(self, name, question, choices, default_idx=0):

        questions = [
            inquirer.List(name,
                message=question,
                choices=choices,
                default=choices[default_idx],
            ),
        ]

        # ponytail: Ctrl-C makes prompt() return None; treat it as the last choice ("give it up")
        return inquirer.prompt(questions) or {name: choices[-1]}

    @staticmethod
    def facet_choice(value, count):
        # Display label for a facet option; parsed back by the two-space marker.
        return f"{value}  ({count})"

    @staticmethod
    def build_facet_filter_query(query_body, content_types=None, languages=None, size_ranges=None):
        """Wrap the original query, keeping it in `must`, and AND facet filters onto it.

        `size_ranges` is a list of (gte, lt) byte bounds (None = unbounded); the
        selected ranges are OR-ed together. Returns `query_body` unchanged when no
        facet is selected.
        """
        filters = []
        if content_types:
            filters.append({'terms': {'contentType': list(content_types)}})
        if languages:
            filters.append({'terms': {'language': list(languages)}})
        if size_ranges:
            shoulds = []
            for (gte, lt) in size_ranges:
                bounds = {}
                if gte is not None:
                    bounds['gte'] = gte
                if lt is not None:
                    bounds['lt'] = lt
                shoulds.append({'range': {'contentLength': bounds}})
            filters.append({'bool': {'should': shoulds, 'minimum_should_match': 1}})
        if not filters:
            return query_body
        return {'query': {'bool': {'must': [query_body.get('query', {})], 'filter': filters}}}

    def facet_aggregations(self, query_body):
        """Run terms + range aggregations over the current result set."""
        keyed_ranges = []
        for (label, gte, lt) in SIZE_RANGES:
            bucket = {'key': label}
            if gte is not None:
                bucket['from'] = gte
            if lt is not None:
                bucket['to'] = lt
            keyed_ranges.append(bucket)
        resp = self.datashare_client.query(
            index=self.datashare_project,
            query=dict(query_body),
            size=0,
            aggs={
                'content_types': {'terms': {'field': 'contentType', 'size': 50}},
                'languages': {'terms': {'field': 'language', 'size': 50}},
                'sizes': {'range': {'field': 'contentLength', 'keyed': True, 'ranges': keyed_ranges}},
            })
        aggs = resp['aggregations']
        size_buckets = aggs['sizes']['buckets']
        return {
            'content_types': [(b['key'], b['doc_count']) for b in aggs['content_types']['buckets']],
            'languages': [(b['key'], b['doc_count']) for b in aggs['languages']['buckets']],
            'sizes': [(label, size_buckets.get(label, {}).get('doc_count', 0)) for (label, _, _) in SIZE_RANGES],
        }

    def ask_facet(self, name, question, buckets):
        """Prompt one checkbox for a facet. Returns the selected values (empty = keep all)."""
        buckets = [(v, c) for (v, c) in buckets if c > 0]
        if len(buckets) < 2:
            # Nothing to narrow: a single (or no) value already covers the whole set.
            return []
        choices = [self.facet_choice(v, c) for (v, c) in buckets]
        answers = self.ask_user_to_select(name, question, choices)
        if not answers or not answers.get(name):
            return []
        chosen = set(answers[name])
        return [v for (v, c) in buckets if self.facet_choice(v, c) in chosen]

    def filter_by_facets(self, query_body):
        """Let the user narrow a heterogeneous result set by facets, in two steps.

        Step 1: content type, then language. Step 2: file size. After each
        selection the aggregations are recomputed over the narrowed set, so
        every prompt shows counts that reflect the previous choices.
        """
        print("Step 1/2: narrow by content type and language")
        aggs = self.facet_aggregations(query_body)
        content_types = self.ask_facet('content_types',
                                       'Filter by content type? (check to keep, none = keep all)',
                                       aggs['content_types'])
        if content_types:
            query_body = self.build_facet_filter_query(query_body, content_types=content_types)
            aggs = self.facet_aggregations(query_body)
        languages = self.ask_facet('languages',
                                   'Filter by language? (check to keep, none = keep all)',
                                   aggs['languages'])
        if languages:
            query_body = self.build_facet_filter_query(query_body, languages=languages)
            aggs = self.facet_aggregations(query_body)
        print("Step 2/2: narrow by file size")
        size_labels = self.ask_facet('sizes',
                                     'Filter by file size? (check to keep, none = keep all)',
                                     aggs['sizes'])
        size_ranges = [SIZE_RANGE_BY_LABEL[label] for label in size_labels]
        return self.build_facet_filter_query(query_body, size_ranges=size_ranges)

    def top_terms(self, doc_ids, size=15):
        """Most salient terms of these docs vs the whole index (significant_text)."""
        resp = self.datashare_client.query(
            index=self.datashare_project,
            query={'query': {'terms': {'_id': doc_ids}}},
            size=0,
            aggs={'keywords': {'significant_text': {
                'field': 'content', 'size': size, 'filter_duplicate_text': True,
                # a term counts if it appears in >=2 of the picked docs (default 3
                # returns nothing for short docs like emails/posts)
                'min_doc_count': 2}}})
        return [(b['key'], b['doc_count']) for b in resp['aggregations']['keywords']['buckets']]

    @staticmethod
    def format_reuse_query_examples(datashare_project, datashare_url, elasticsearch_url, output_file):
        """Example commands showing how to reuse the saved query file with
        other tarentula commands, using this session's own connection options."""
        conn_opts = f"--datashare-project {datashare_project} --datashare-url {datashare_url}"
        if elasticsearch_url:
            conn_opts += f" --elasticsearch-url {elasticsearch_url}"
        export_fields = ("path,metadata.tika_metadata_content_type,language,contentLength,"
                          "metadata.tika_metadata_file_size,metadata.tika_metadata_creation_date,content")
        return (
            "Reuse this query with other tarentula commands:\n"
            f"  tarentula download {conn_opts} --query @{output_file}\n"
            f"  tarentula export-by-query {conn_opts} --query @{output_file} "
            f"--output-file similar_docs.csv --source {export_fields}"
        )

    @staticmethod
    def format_facet_lines(facet, buckets):
        """One line per non-zero bucket: value left-aligned, count right-aligned
        under a "facet:" header -- instead of one long comma-joined line that
        wraps mid-value on anything but a huge terminal."""
        shown = [(v, c) for (v, c) in buckets if c > 0]
        if not shown:
            return []
        value_width = max(len(v) for v, _ in shown)
        count_width = max(len(str(c)) for _, c in shown)
        return [f"{facet}:"] + [f"  {v:<{value_width}}  {c:>{count_width}}" for v, c in shown]

    def print_status(self, query_body):
        """Where the search stands: the query itself, hit count and facet breakdown."""
        print("\nCurrent query:")
        print(json.dumps(query_body, indent=2))
        print("Matches:", self.count_matches(query_body=query_body))
        aggs = self.facet_aggregations(query_body)
        for facet, buckets in aggs.items():
            lines = self.format_facet_lines(facet, buckets)
            if lines:
                print()
                print('\n'.join(lines))
        print()

    def narrow_by_facets(self, query_body):
        """Facet-filter the current query and report the narrowed match count."""
        query_body = self.filter_by_facets(query_body)
        print("Num of matches after filtering:", self.count_matches(query_body=query_body))
        return query_body

    def start(self):

        # start from a broad query: a couple of words already cuts the noise a lot
        if self.query in (None, '', '*'):
            answers = inquirer.prompt([inquirer.Text(
                'query', message='Start with a broad query (2-3 words; empty = all docs)')])
            if answers and answers['query'].strip():
                self.query = answers['query'].strip()

        print("Num of matches:", self.count_matches())

        # Narrow the (often heterogeneous) first batch by facets before hand-picking.
        query = self.narrow_by_facets(self.query_body)

        loop_from = DEFAULT_FROM
        loop_limit = DEFAULT_LIMIT

        # Enter interactive loop
        chat_choices = [
            'No, keep going', 
            'Yes, save current query and leave', 
            'No, give it up',
        ]
        chat_answers = {'user_chat': 'No, keep going'}
        unliked_ids = []
        liked_terms, unliked_terms = [], []

        while chat_answers['user_chat'] == 'No, keep going':
            try:

                # 1 select interesting docs (paginated: check "next page" to browse further)
                selected_docs = self.paginated_doc_picker(
                    'first_docs', 'Which docs are you interested in?', query, from_=loop_from, limit=loop_limit)

                while len(selected_docs) < 2:
                    print("You need to select at least 2 documents to find commonalities, current selection: %s" % len(selected_docs))

                    action = self.ask_user_to_choose('more', 'What now?', ['Try again', 'Exit'])['more']
                    if action == 'Exit':
                        print("Ok, exiting. Bye!")
                        return

                    selected_docs = self.paginated_doc_picker(
                        'first_docs', 'Which docs are you interested in?', query, from_=loop_from, limit=loop_limit)

                # 2 find commonalities between them
                full_docs = self.query_doc_content([doc['_id'] for doc in selected_docs])

                # find common lines between the docs
                commonalities = self.common_lines(full_docs)

                if len(commonalities) < MIN_COMMONALITIES_TO_OFFER:
                    print(f"No common lines found between the selected documents. Trying with ngrams")
                
                    # find common lines between the docs
                    n_grams_choices = reversed(range(1, 4))
                    for n in n_grams_choices:
                        print(f"Trying with ngrams of size {n}")
                        commonalities += self.common_ngrams(full_docs, n=n)
                        if len(commonalities) > MIN_COMMONALITIES_TO_OFFER:
                            break
            
                if len(commonalities) > 0:
                    if len(commonalities) > 30:
                        print(f"Showing the 30 longest of {len(commonalities)} commonalities found")
                        commonalities = commonalities[:30]
                    # rank by whole-index doc count: rare ones are the distinctive,
                    # narrowing terms we're after; common ones are boilerplate that
                    # would broaden the query, so push them to the bottom
                    scored = [(term, self.count_matches(
                        query_body={'query': {'match_phrase': {'content': term}}}))
                        for term in commonalities]
                    scored.sort(key=lambda term_count: term_count[1])
                    labeled = {f"{term}  [in {n} docs of the whole index]": term for term, n in scored}
                    answers = self.ask_user_to_select(
                        'commonalities',
                        'Common terms of your picks, rarest (most distinctive) first: use '
                        'some to narrow the query? (high doc counts = boilerplate, they '
                        'would broaden it instead)',
                        list(labeled))
                    answers['commonalities'] = [labeled[l] for l in answers['commonalities']]
                else:
                    answers = {'commonalities': []}

                # 3 search for commonalities

                # offer the salient terms of the picked docs as extra query terms
                selected_ids = [doc['_id'] for doc in selected_docs]
                candidates = {f"{t}  [in {c} of {len(selected_ids)} picks]": t
                              for t, c in self.top_terms(selected_ids) if t not in liked_terms}
                if candidates:
                    picked = self.ask_user_to_select(
                        'liked_terms',
                        'Salient terms: frequent in your picks but rare in the rest of '
                        'the index. Add some to the query? (none = skip)',
                        list(candidates))
                    liked_terms += [candidates[l] for l in picked['liked_terms']]

                # run query for the selected commonalities
                query = self.build_mlt_query(
                    selected_ids,
                    answers['commonalities'] + liked_terms,
                    unliked_docs=unliked_ids,
                    unliked_terms=unliked_terms,
                )

                # The MLT results are heterogeneous again: offer another facet-narrowing pass.
                query = self.narrow_by_facets(query)

                # precision proxy: how many of the docs the user picked still match?
                still_matching = self.count_matches(query_body={'query': {'bool': {
                    'must': [query['query'], {'terms': {'_id': selected_ids}}]}}})
                print(f"{still_matching}/{len(selected_ids)} of your selected docs still match")

                # false positives feed the next round's MLT `unlike`
                false_positives = self.paginated_doc_picker(
                    'false_positives',
                    f'{ANSI_RED}Mark false positives (excluded as "unlike" next round, none = skip){ANSI_RESET}',
                    query)
                unliked_ids += [doc['_id'] for doc in false_positives if doc['_id'] not in unliked_ids]

                # offer the salient terms of all unliked docs so far as exclusions,
                # skipping any term that's also salient in your liked picks (a term
                # shared by both sides isn't a discriminator, it'd just gut recall)
                if unliked_ids:
                    candidates = {f"{t}  [in {c} of {len(unliked_ids)} unliked docs]": t
                                  for t, c in self.top_terms(unliked_ids)
                                  if t not in unliked_terms and t not in liked_terms}
                    if candidates:
                        picked = self.ask_user_to_select(
                            'unliked_terms',
                            'Salient terms of the unliked docs (frequent there, rare '
                            'elsewhere, absent from your liked terms). Exclude some as '
                            'NOT clauses? (none = skip)',
                            list(candidates))
                        unliked_terms += [candidates[l] for l in picked['unliked_terms']]

                # this round's exclusions only get baked into `query` on the next
                # build_mlt_query call; patch them in now so status/save reflect them
                self.refresh_unlike(query, unliked_ids, unliked_terms)

                # show where the search stands before asking to continue or stop
                self.print_status(query)

                # reask to the user if he wants to keep going
                chat_answers = self.ask_user_to_choose('user_chat', 'Is your search good enough for you?', chat_choices, default_idx=0)
            except (HTTPError, ProtocolError):
                logger.error('Request failed mid-round', exc_info=self.traceback)
                print("A request to the server failed; keeping your selections, let's retry.")

        print(chat_answers['user_chat'])
        
        # 4 see if end user is happy with the results
        if chat_answers['user_chat'] == 'Yes, save current query and leave':
            with open(self.output_file, 'w') as f:
                json.dump(query, f, indent=4)
                print("Saved query to file %s" % self.output_file)
            print()
            print(self.format_reuse_query_examples(
                self.datashare_project, self.datashare_url,
                self.datashare_client.elasticsearch_url, self.output_file))

        elif chat_answers['user_chat'] == 'No, give it up':
            print("Ok, giving up. Bye!")