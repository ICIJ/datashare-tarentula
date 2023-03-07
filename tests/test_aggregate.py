from typing import Optional

import pytest

from json import loads
from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestAggregate(TestAbstract):
    maxDiff = None

    def tearDown(self):
        self.datashare_client.delete_all(index=self.datashare_project)

    def test_aggregate_by_field_and_count(self):
        self.index_documents([{"name": "foo", "type": "Document", "contentType": "audio/vorbis",
                               "_id": "id1"},
                              {"name": "bar", "type": "Document", "contentType": "audio/vorbis",
                               "_id": "id2"},
                              {"name": "baz", "type": "Document", "contentType": "audio/mp3",
                               "_id": "id3"},
                              {"name": "qux", "type": "Document", "contentType": "audio/flac",
                               "_id": "id4"}
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--group_by',  'contentType',
                            '--query',  '*' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertIn('buckets', data['aggregation-1'])
        self.assertEqual(3, len(data['aggregation-1']['buckets']))
        self.assertEqual(2, get_bucket(data, 'audio/vorbis')['doc_count'])
        self.assertEqual(1, get_bucket(data, 'audio/mp3')['doc_count'])
        self.assertEqual(1, get_bucket(data, 'audio/flac')['doc_count'])

    def test_aggregate_by_num_unique_field(self):
        self.index_documents([{"name": "foo", "type": "Document", "contentType": "image/jpeg",
                               "_id": "id1"},
                              {"name": "bar", "type": "Document", "contentType": "image/png",
                               "_id": "id2"}
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--run',  'nunique',
                            '--operation_field',  'contentType',
                            '--query',  '*' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertIn('value', data['aggregation-1'])
        self.assertEqual(2, data['aggregation-1']['value'])

    def test_aggregate_sum_field(self):
        self.index_documents([{"name": "foo", "type": "Document", "contentLength": 15,
                               "_id": "id1"},
                              {"name": "bar", "type": "Document", "contentLength": 25,
                               "_id": "id2"}
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--run',  'sum',
                            '--operation_field',  'contentLength',
                            '--query',  '*' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertIn('value', data['aggregation-1'])
        self.assertEqual(40.0, data['aggregation-1']['value'])

    def test_aggregate_string_stats(self):
        if self.elasticsearch_version_info < (7, 11):
            return pytest.skip("requires ElasticSearch 7.11+")

        self.index_documents([{"name": "foo", "type": "Document", "language": "FRENCH",
                               "_id": "id1"},
                              {"name": "bar", "type": "Document", "language": "ENGLISH",
                               "_id": "id2"}
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--run',  'string_stats',
                            '--operation_field',  'language' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertTrue(all([stat in data['aggregation-1'].keys() for stat in ['count', 'min_length', 'max_length', 'avg_length', 'entropy']]))

    def test_aggregate_query_and_sum_field(self):
        self.index_documents([{"name": "foo", "type": "Document", "language": "FRENCH", "contentLength": 123,
                               "_id": "id1"},
                              {"name": "bar", "type": "Document", "language": "ENGLISH", "contentLength": 321,
                               "_id": "id2"}
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--run',  'sum',
                            '--operation_field',  'contentLength',
                            '--query',  'language:FRENCH' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertIn('value', data['aggregation-1'])
        self.assertEqual(123.0, data['aggregation-1']['value'])

    def test_aggregate_date_histogram_yearly(self):
        self.index_documents([{"name": "foo", "type": "Document",
                               "metadata": {"tika_metadata_creation_date": "2004-01-01T12:00:00.000Z"}, "_id": "id1"},
                              {"name": "bar", "type": "Document",
                               "metadata": {"tika_metadata_creation_date": "2005-01-02T13:00:00.000Z"}, "_id": "id2"},
                              ])
        runner = CliRunner()

        result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--run',  'date_histogram',
                            '--operation_field',  'metadata.tika_metadata_creation_date' ])

        data = loads(result.output)
        self.assertIn('aggregation-1', data)
        self.assertIn('buckets', data['aggregation-1'])
        self.assertEqual(2, len(data['aggregation-1']['buckets']))
        self.assertEqual(1, get_bucket(data, '2004-01-01T00:00:00.000Z', key='key_as_string')['doc_count'])


def get_bucket(data: dict, key_value: str, aggregation_key: str = 'aggregation-1', key: str = "key") -> Optional[dict]:
    for bucket in data[aggregation_key]['buckets']:
        if bucket[key] == key_value:
            return bucket