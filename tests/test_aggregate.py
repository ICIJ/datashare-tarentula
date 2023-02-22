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
