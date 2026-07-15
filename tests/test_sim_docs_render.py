"""Pure unit tests for the doc-picker row/header formatting (no live Datashare needed)."""
from tarentula.sim_docs import SimilarDocs, CHECKBOX_PREFIX_WIDTH

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


def test_column_widths_blurb_shrinks_to_zero_rather_than_overflow():
    # way too narrow to fit the fixed columns: blurb must give up its width
    # entirely rather than push the row past the terminal (that wrap breaks
    # inquirer's cursor-repaint math -- see CHECKBOX_PREFIX_WIDTH)
    widths = SimilarDocs.column_widths(10)
    assert widths['blurb'] == 0


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


def test_rows_leave_room_for_inquirer_checkbox_prefix():
    # inquirer prints "  [ ] "/"> [ ] " (7 visible chars) before every choice
    # (inquirer/render/console/__init__.py's print_line + _checkbox.py's
    # get_options: " " + selector(1) + " " + "[ ]"/"[X]"(3) + " " = 7). If a
    # row's content fills the terminal width exactly, that prefix pushes the
    # printed line past the terminal, wraps it, and breaks inquirer's
    # cursor-repaint math (it moves the cursor up by choice count, not actual
    # physical line count) -- producing stacked/duplicated prompt frames.
    for terminal_width in (80, 100, 120, 200):
        content_width = SimilarDocs.content_width_for_checkbox(terminal_width)
        widths = SimilarDocs.column_widths(content_width)
        row = SimilarDocs.format_doc_row(DOC, 'x' * 200, widths)
        assert len(row) + CHECKBOX_PREFIX_WIDTH <= terminal_width


def test_header_row_also_stays_within_terminal_width():
    # printed with a CHECKBOX_PREFIX_WIDTH indent so it lines up visually
    # above the checkboxes; must not itself overflow the terminal
    for terminal_width in (80, 100, 120, 200):
        content_width = SimilarDocs.content_width_for_checkbox(terminal_width)
        widths = SimilarDocs.column_widths(content_width)
        header = SimilarDocs.format_header_row(widths)
        assert len(header) + CHECKBOX_PREFIX_WIDTH <= terminal_width


def test_format_facet_lines_skips_zero_buckets_and_aligns_columns():
    lines = SimilarDocs.format_facet_lines(
        'content_types', [('message/rfc822', 10467), ('text/plain', 145), ('empty', 0)])
    assert lines[0] == 'content_types:'
    assert len(lines) == 3  # header + 2 non-zero buckets, 'empty' dropped
    # value/count columns padded to a shared width -> every bucket line is the same length
    assert len({len(line) for line in lines[1:]}) == 1


def test_format_facet_lines_returns_empty_when_all_buckets_are_zero():
    assert SimilarDocs.format_facet_lines('languages', [('ENGLISH', 0)]) == []


if __name__ == '__main__':
    test_column_widths_fixed_cols_stay_constant_and_blurb_grows()
    test_column_widths_blurb_shrinks_to_zero_rather_than_overflow()
    test_format_header_row_lists_all_columns_in_order()
    test_format_doc_row_truncates_long_fields_and_right_aligns_size()
    test_build_doc_choices_maps_each_row_back_to_its_doc()
    test_rows_leave_room_for_inquirer_checkbox_prefix()
    test_header_row_also_stays_within_terminal_width()
    test_format_facet_lines_skips_zero_buckets_and_aligns_columns()
    test_format_facet_lines_returns_empty_when_all_buckets_are_zero()
    print('ok')
