from json import load

from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract
from .test_download import load_json_file

class TestAggregate(TestAbstract):
    maxDiff = None

    def tearDown(self):
        super().tearDown()

    def test_aggregate_by_field_and_count_1(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--group_by',  'contentType',
                                '--query',  '*' ])

            with open('tests/fixtures/species_test_aggs_count_response_1.json', 'r') as ifile:
                expected_text = ifile.read()

            self.assertEqual(expected_text+"\n", result.output)

    def test_aggregate_by_field_and_count_2(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--group_by',  'contentType',
                                '--query',  'Actinopodidae OR Antrodiaetidae' ])

            with open('tests/fixtures/species_test_aggs_count_response_2.json', 'r') as ifile:
                expected_text = ifile.read()

            self.assertEqual(expected_text+"\n", result.output)

    def test_aggregate_nunique_field_1(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'nunique',
                                '--operation_field',  'contentType',
                                '--query',  '*' ])

            with open('tests/fixtures/species_test_aggs_nunique_contenttype.json', 'r') as ifile:
                expected_text = ifile.read()

            self.assertEqual(expected_text+"\n", result.output)

    def test_aggregate_nunique_luxleaks_languages(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'nunique',
                                '--operation_field',  'language'])

            expected_text = """{\n    "aggregation-1": {\n        "value": 3\n    }\n}\n"""
            self.assertEqual(expected_text, result.output)

    def test_aggregate_sum_field(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'sum',
                                '--operation_field',  'contentLength',
                                '--query',  '*' ])

            with open('tests/fixtures/luxleaks_test_aggs_sum_contentlength_all.json', 'r') as ifile:
                expected_text = ifile.read()

            self.assertEqual(expected_text+"\n", result.output)
            
    def test_aggregate_string_stats(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'string_stats',
                                '--operation_field',  'language' ])

            expected_text = '{\n    "aggregation-1": {\n        "count": 212,\n        "min_length": 6,\n        "max_length": 7,\n        "avg_length": 6.933962264150943,\n        "entropy": 2.970184813429149\n    }\n}\n'
            self.assertEqual(expected_text, result.output)
            
    def test_aggregate_query_and_sum_field(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'sum',
                                '--operation_field',  'contentLength',
                                '--query',  'language:FRENCH' ])

            with open('tests/fixtures/luxleaks_test_aggs_sum_contentlength_filter1.json', 'r') as ifile:
                expected_text = ifile.read()

            self.assertEqual(expected_text+"\n", result.output)
            
    def test_aggregate_date_histogram(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'date_histogram',
                                '--operation_field',  'metadata.tika_metadata_creation_date' ])

            expected_text = '{\n    "aggregation-1": {\n        "buckets": [\n            {\n                "key_as_string": "2004-01-01T00:00:00.000Z",\n                "key": 1072915200000,\n                "doc_count": 1\n            },\n            {\n                "key_as_string": "2005-01-01T00:00:00.000Z",\n                "key": 1104537600000,\n                "doc_count": 0\n            },\n            {\n                "key_as_string": "2006-01-01T00:00:00.000Z",\n                "key": 1136073600000,\n                "doc_count": 0\n            },\n            {\n                "key_as_string": "2007-01-01T00:00:00.000Z",\n                "key": 1167609600000,\n                "doc_count": 3\n            },\n            {\n                "key_as_string": "2008-01-01T00:00:00.000Z",\n                "key": 1199145600000,\n                "doc_count": 2\n            },\n            {\n                "key_as_string": "2009-01-01T00:00:00.000Z",\n                "key": 1230768000000,\n                "doc_count": 2\n            },\n            {\n                "key_as_string": "2010-01-01T00:00:00.000Z",\n                "key": 1262304000000,\n                "doc_count": 15\n            },\n            {\n                "key_as_string": "2011-01-01T00:00:00.000Z",\n                "key": 1293840000000,\n                "doc_count": 0\n            },\n            {\n                "key_as_string": "2012-01-01T00:00:00.000Z",\n                "key": 1325376000000,\n                "doc_count": 3\n            },\n            {\n                "key_as_string": "2013-01-01T00:00:00.000Z",\n                "key": 1356998400000,\n                "doc_count": 0\n            },\n            {\n                "key_as_string": "2014-01-01T00:00:00.000Z",\n                "key": 1388534400000,\n                "doc_count": 1\n            }\n        ]\n    }\n}\n'
            self.assertEqual(expected_text, result.output)
            