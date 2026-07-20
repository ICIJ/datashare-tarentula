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


def test_mlt_query_only_holds_doc_refs_terms_become_should_and_must_not():
    s = SimilarDocs.__new__(SimilarDocs)  # skip __init__: no live Datashare needed
    s.datashare_project = 'proj'
    s.max_query_terms, s.min_term_freq, s.min_doc_freq, s.min_word_length = 30, 1, 10, 4
    s.minimum_should_match = '30%'
    q = s.build_mlt_query(['a'], ['common term'], unliked_docs=['b'],
                          unliked_terms=['bad term'])['query']['bool']
    mlt = q['must'][0]['more_like_this']
    assert q['must'] == [{'more_like_this': mlt}]
    assert mlt['like'] == [{'_index': 'proj', '_id': 'a'}]
    assert mlt['unlike'] == [{'_index': 'proj', '_id': 'b'}]
    assert q['should'] == [{'match_phrase': {'content': 'common term'}}]
    assert q['minimum_should_match'] == 1  # ceil(1 * 30%) == 1
    assert q['must_not'] == [{'match_phrase': {'content': 'bad term'}}]


def test_terms_minimum_should_match_floors_at_one():
    s = SimilarDocs.__new__(SimilarDocs)
    s.minimum_should_match = '30%'
    # ES's own percentage handling would floor(2 * 30%) = 0, disabling the
    # requirement entirely; ours must never go below 1.
    assert s.terms_minimum_should_match(2) == 1
    assert s.terms_minimum_should_match(1) == 1
    assert s.terms_minimum_should_match(10) == 3


def test_mlt_query_omits_should_and_must_not_when_no_terms():
    s = SimilarDocs.__new__(SimilarDocs)
    s.datashare_project = 'proj'
    s.max_query_terms, s.min_term_freq, s.min_doc_freq, s.min_word_length = 30, 1, 10, 4
    s.minimum_should_match = '30%'
    q = s.build_mlt_query(['a'], [])['query']['bool']
    assert 'should' not in q
    assert 'minimum_should_match' not in q
    assert 'must_not' not in q


def test_refresh_unlike_patches_nested_facet_wrapped_query():
    s = SimilarDocs.__new__(SimilarDocs)
    s.datashare_project = 'proj'
    s.max_query_terms, s.min_term_freq, s.min_doc_freq, s.min_word_length = 30, 1, 10, 4
    s.minimum_should_match = '30%'
    q = s.build_mlt_query(['a'], ['common term'])
    q = SimilarDocs.build_facet_filter_query(q, content_types=['application/pdf'])
    s.refresh_unlike(q, ['b', 'c'], ['bad term'])
    bool_clause = SimilarDocs._find_owning_bool(q)
    mlt = SimilarDocs._find_more_like_this(q)
    assert mlt['unlike'] == [{'_index': 'proj', '_id': 'b'}, {'_index': 'proj', '_id': 'c'}]
    assert bool_clause['must_not'] == [{'match_phrase': {'content': 'bad term'}}]


def test_common_ngrams_uses_requested_n_for_all_docs():
    s = SimilarDocs.__new__(SimilarDocs)
    docs = [{'_source': {'content': 'In article foo bar'}},
            {'_source': {'content': 'In article baz qux'}}]
    assert 'in article' in s.common_ngrams(docs, n=2)
    assert s.common_ngrams(docs, n=3) == []


def test_common_lines_and_ngrams_dont_crash_on_missing_content():
    # e.g. images indexed with OCR off: _source has no 'content' key at all
    s = SimilarDocs.__new__(SimilarDocs)
    docs = [{'_source': {}}, {'_source': {}}]
    assert s.common_lines(docs) == []
    assert s.common_ngrams(docs, n=2) == []


def test_mlt_param_candidates_are_half_current_double_deduped_and_floored():
    assert SimilarDocs.mlt_param_candidates(30) == [15, 30, 60]
    assert SimilarDocs.mlt_param_candidates(10) == [5, 10, 20]
    # half(1) floors at 1, colliding with current -- dedup leaves 2 candidates
    assert SimilarDocs.mlt_param_candidates(1) == [1, 2]


if __name__ == '__main__':
    test_no_facets_returns_query_unchanged()
    test_content_type_and_language_become_terms_filters()
    test_size_ranges_are_or_ed_and_respect_bounds()
    test_mlt_query_only_holds_doc_refs_terms_become_should_and_must_not()
    test_terms_minimum_should_match_floors_at_one()
    test_mlt_query_omits_should_and_must_not_when_no_terms()
    test_refresh_unlike_patches_nested_facet_wrapped_query()
    test_common_ngrams_uses_requested_n_for_all_docs()
    test_common_lines_and_ngrams_dont_crash_on_missing_content()
    test_mlt_param_candidates_are_half_current_double_deduped_and_floored()
    print('ok')
