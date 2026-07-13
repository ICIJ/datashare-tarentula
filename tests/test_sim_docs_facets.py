"""Pure unit tests for the facet-filter query builder (no live Datashare needed)."""
from tarentula.sim_docs import SimilarDocs, SIZE_RANGE_BY_LABEL

BASE = {'query': {'bool': {'must': [{'query_string': {'query': 'acme'}}]}}}


def test_no_facets_returns_query_unchanged():
    assert SimilarDocs.build_facet_filter_query(BASE) is BASE


def test_content_type_and_language_become_terms_filters():
    q = SimilarDocs.build_facet_filter_query(
        BASE, content_types=['application/pdf'], languages=['ENGLISH', 'SPANISH'])
    filters = q['query']['bool']['filter']
    assert {'terms': {'contentType': ['application/pdf']}} in filters
    assert {'terms': {'language': ['ENGLISH', 'SPANISH']}} in filters
    # original query is preserved inside must
    assert q['query']['bool']['must'] == [BASE['query']]


def test_size_ranges_are_or_ed_and_respect_bounds():
    ranges = [SIZE_RANGE_BY_LABEL['< 10 KB'], SIZE_RANGE_BY_LABEL['> 1 MB']]
    q = SimilarDocs.build_facet_filter_query(BASE, size_ranges=ranges)
    should = q['query']['bool']['filter'][0]['bool']['should']
    assert {'range': {'contentLength': {'lt': 10_000}}} in should            # no gte -> unbounded below
    assert {'range': {'contentLength': {'gte': 1_000_000}}} in should        # no lt -> unbounded above
    assert q['query']['bool']['filter'][0]['bool']['minimum_should_match'] == 1


def test_mlt_query_likes_docs_and_terms_and_unlikes_docs():
    s = SimilarDocs.__new__(SimilarDocs)  # skip __init__: no live Datashare needed
    s.datashare_project = 'proj'
    s.max_query_terms, s.min_term_freq, s.min_doc_freq, s.min_word_length = 30, 1, 10, 4
    s.minimum_should_match = '30%'
    mlt = s.build_mlt_query(['a'], ['common term'], unliked_docs=['b'],
                            unliked_terms=['bad term'])['query']['more_like_this']
    assert {'_index': 'proj', '_id': 'a'} in mlt['like']
    assert 'common term' in mlt['like']
    assert mlt['unlike'] == [{'_index': 'proj', '_id': 'b'}, 'bad term']


def test_common_ngrams_uses_requested_n_for_all_docs():
    s = SimilarDocs.__new__(SimilarDocs)
    docs = [{'_source': {'content': 'In article foo bar'}},
            {'_source': {'content': 'In article baz qux'}}]
    assert 'in article' in s.common_ngrams(docs, n=2)
    assert s.common_ngrams(docs, n=3) == []


if __name__ == '__main__':
    test_no_facets_returns_query_unchanged()
    test_content_type_and_language_become_terms_filters()
    test_size_ranges_are_or_ed_and_respect_bounds()
    test_mlt_query_likes_docs_and_terms_and_unlikes_docs()
    test_common_ngrams_uses_requested_n_for_all_docs()
    print('ok')
