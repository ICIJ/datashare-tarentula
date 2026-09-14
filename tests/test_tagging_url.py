from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from unittest import TestCase

import click

from tarentula.tagging import Tagger

DOCUMENT_ID = 'DWLOskax28jPQ2CjFrCo'
ROUTING = 'vZJQpKQYhcI577gJR0aN'


@contextmanager
def tagger_for(csv):
    with NamedTemporaryFile('w', suffix='.csv') as file:
        file.write(csv)
        file.flush()
        yield Tagger(csv_path=file.name)


def one_row(url, routing_column=''):
    header = 'tag,documentUrl,routing' if routing_column else 'tag,documentUrl'
    row = f'Atracidae,{url},{routing_column}' if routing_column else f'Atracidae,{url}'
    return f'{header}\n{row}\n'


class TestTaggingUrl(TestCase):
    def test_every_document_route_prefix_is_parsed(self):
        for prefix in ('d', 'e', 'ds', 'dm'):
            with self.subTest(prefix=prefix):
                url = f'http://localhost:8080/#/{prefix}/local-datashare/{DOCUMENT_ID}/{ROUTING}'
                with tagger_for(one_row(url)) as tagger:
                    self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_url_with_query_string_is_parsed(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}/{ROUTING}?tab=text'
        with tagger_for(one_row(url)) as tagger:
            self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_url_with_trailing_slash_is_parsed(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}/{ROUTING}/'
        with tagger_for(one_row(url)) as tagger:
            self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_url_with_dotted_project_is_parsed(self):
        url = f'http://localhost:8080/#/ds/my.project/{DOCUMENT_ID}/{ROUTING}'
        with tagger_for(one_row(url)) as tagger:
            self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_url_without_routing_falls_back_to_document_id(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}'
        with tagger_for(one_row(url)) as tagger:
            self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], DOCUMENT_ID)

    def test_explicit_routing_column_is_kept_when_url_has_none(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}'
        with tagger_for(one_row(url, routing_column=ROUTING)) as tagger:
            self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_routing_does_not_depend_on_row_order(self):
        without_routing = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}'
        with_routing = f'{without_routing}/{ROUTING}'
        for first, second in ((without_routing, with_routing), (with_routing, without_routing)):
            with self.subTest(first=first):
                csv = f'tag,documentUrl\nAtracidae,{first}\nActinopodidae,{second}\n'
                with tagger_for(csv) as tagger:
                    self.assertEqual(tagger.tree[DOCUMENT_ID]['routing'], ROUTING)

    def test_unsupported_url_raises_a_readable_error(self):
        url = 'http://localhost:8080/#/settings'
        with tagger_for(one_row(url)) as tagger:
            with self.assertRaises(click.BadParameter) as context:
                tagger.tree
            self.assertIn(url, str(context.exception))

    def test_url_with_extra_segments_raises_a_readable_error(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}/{ROUTING}/text'
        with tagger_for(one_row(url)) as tagger:
            with self.assertRaises(click.BadParameter) as context:
                tagger.tree
            self.assertIn(url, str(context.exception))

    def test_row_without_document_id_or_url_raises_a_readable_error(self):
        with tagger_for('tag,documentId\nAtracidae,\n') as tagger:
            with self.assertRaises(click.BadParameter):
                tagger.tree

    def test_trailing_blank_lines_are_ignored(self):
        url = f'http://localhost:8080/#/ds/local-datashare/{DOCUMENT_ID}/{ROUTING}'
        with tagger_for(f'{one_row(url)}\n\n') as tagger:
            self.assertEqual(len(tagger.tree), 1)
