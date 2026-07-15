"""Live-ES coverage for SimilarDocs query methods (facet_aggregations, query_all,
count_matches) — the pieces test_sim_docs_facets.py can't reach without an index.
"""
from tarentula.sim_docs import SimilarDocs
from .test_abstract import TestAbstract

DOCS = [
    {'_id': 'doc-pdf-en-small', 'type': 'Document', 'contentType': 'application/pdf',
     'language': 'ENGLISH', 'contentLength': 5_000, 'content': 'alpha bravo charlie'},
    {'_id': 'doc-pdf-en-large', 'type': 'Document', 'contentType': 'application/pdf',
     'language': 'ENGLISH', 'contentLength': 2_000_000, 'content': 'alpha bravo delta'},
    {'_id': 'doc-html-es-small', 'type': 'Document', 'contentType': 'text/html',
     'language': 'SPANISH', 'contentLength': 1_000, 'content': 'echo foxtrot golf'},
]


class TestSimDocsLive(TestAbstract):
    def similar_docs(self):
        return SimilarDocs(datashare_url=self.datashare_url,
                            elasticsearch_url=self.elasticsearch_url,
                            datashare_project=self.datashare_project)

    def test_facet_aggregations_counts_by_type_language_and_size(self):
        self.index_documents(DOCS)
        try:
            sim = self.similar_docs()
            aggs = sim.facet_aggregations({'query': {'match_all': {}}})
            self.assertIn(('application/pdf', 2), aggs['content_types'])
            self.assertIn(('text/html', 1), aggs['content_types'])
            self.assertIn(('ENGLISH', 2), aggs['languages'])
            self.assertIn(('SPANISH', 1), aggs['languages'])
            sizes = dict(aggs['sizes'])
            self.assertEqual(sizes['< 10 KB'], 2)
            self.assertEqual(sizes['> 1 MB'], 1)
        finally:
            self.delete_documents(DOCS)

    def test_build_facet_filter_query_narrows_query_all_and_count_matches(self):
        self.index_documents(DOCS)
        try:
            sim = self.similar_docs()
            narrowed = sim.build_facet_filter_query(
                {'query': {'match_all': {}}}, content_types=['application/pdf'])
            self.assertEqual(sim.count_matches(query_body=narrowed), 2)
            ids = {doc['_id'] for doc in sim.query_all(query_body=narrowed)}
            self.assertEqual(ids, {'doc-pdf-en-small', 'doc-pdf-en-large'})
        finally:
            self.delete_documents(DOCS)
