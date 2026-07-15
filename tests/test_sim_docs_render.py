"""Pure unit tests for the doc-picker row/header formatting (no live Datashare needed)."""
from tarentula.sim_docs import SimilarDocs

DOC = {
    '_id': '0123456789abcdef',
    '_source': {
        'contentType': 'application/pdf',
        'language': 'ENGLISH',
        'contentLength': '2048',
        'path': '/data/reports/annual-report-2024.pdf',
    },
}


def test_column_widths_fixed_cols_stay_constant_and_blurb_grows():
    narrow = SimilarDocs.column_widths(80)
    wide = SimilarDocs.column_widths(200)
    for col in ('id', 'type', 'lang', 'size', 'name'):
        assert narrow[col] == wide[col]
    assert wide['blurb'] > narrow['blurb']


def test_column_widths_blurb_floors_at_minimum_on_narrow_terminal():
    widths = SimilarDocs.column_widths(10)  # way too narrow to fit the fixed columns
    assert widths['blurb'] == 20  # BLURB_MIN_WIDTH


def test_format_header_row_lists_all_columns_in_order():
    widths = SimilarDocs.column_widths(120)
    header = SimilarDocs.format_header_row(widths)
    assert header.index('id') < header.index('type') < header.index('lang') \
        < header.index('size') < header.index('name') < header.index('blurb')


def test_format_doc_row_truncates_long_fields_and_right_aligns_size():
    widths = SimilarDocs.column_widths(120)
    row = SimilarDocs.format_doc_row(DOC, 'some blurb text', widths)
    assert row.startswith('012345')  # id truncated to ID_WIDTH
    assert '2 KB' in row  # 2048 bytes -> 2 KB, right-aligned in SIZE_WIDTH
    assert 'annual-report-2024.pdf' in row  # doc_name() extracts the basename
    assert row.rstrip().endswith('some blurb text')


def test_build_doc_choices_maps_each_row_back_to_its_doc():
    docs = [DOC, {**DOC, '_id': 'fedcba9876543210'}]
    contents = {DOC['_id']: 'first content', docs[1]['_id']: 'second content'}
    widths = SimilarDocs.column_widths(120)
    pairs = SimilarDocs.build_doc_choices(docs, contents, widths)
    assert len(pairs) == 2
    rows_by_id = {doc['_id']: row for row, doc in pairs}
    assert 'first content' in rows_by_id[DOC['_id']]
    assert 'second content' in rows_by_id[docs[1]['_id']]


if __name__ == '__main__':
    test_column_widths_fixed_cols_stay_constant_and_blurb_grows()
    test_column_widths_blurb_floors_at_minimum_on_narrow_terminal()
    test_format_header_row_lists_all_columns_in_order()
    test_format_doc_row_truncates_long_fields_and_right_aligns_size()
    test_build_doc_choices_maps_each_row_back_to_its_doc()
    print('ok')
