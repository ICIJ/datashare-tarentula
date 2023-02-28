from json import loads

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

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('buckets', data['aggregation-1'])
            self.assertEqual(19, len(data['aggregation-1']['buckets']))
            self.assertIn(2, [bucket['doc_count'] for bucket in data['aggregation-1']['buckets'] if bucket['key']=='audio/vorbis'])


    def test_aggregate_by_field_and_count_2(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--group_by',  'contentType',
                                '--query',  'Actinopodidae OR Antrodiaetidae' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('buckets', data['aggregation-1'])
            self.assertEqual(2, len(data['aggregation-1']['buckets']))
            self.assertIn('audio/mpeg', [bucket['key'] for bucket in data['aggregation-1']['buckets']])
            self.assertIn('audio/vnd.wave', [bucket['key'] for bucket in data['aggregation-1']['buckets']])

    def test_aggregate_nunique_field_1(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'nunique',
                                '--operation_field',  'contentType',
                                '--query',  '*' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('value', data['aggregation-1'])
            self.assertEqual(19, data['aggregation-1']['value'])

    def test_aggregate_nunique_luxleaks_languages(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'nunique',
                                '--operation_field',  'language'])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('value', data['aggregation-1'])
            self.assertEqual(3, data['aggregation-1']['value'])

    def test_aggregate_sum_field(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'sum',
                                '--operation_field',  'contentLength',
                                '--query',  '*' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('value', data['aggregation-1'])
            self.assertEqual(679475452.0, data['aggregation-1']['value'])
            
    def test_aggregate_string_stats(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'string_stats',
                                '--operation_field',  'language' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertTrue(all([stat in data['aggregation-1'].keys() for stat in ['count', 'min_length', 'max_length', 'avg_length', 'entropy']]))

    def test_aggregate_query_and_sum_field(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'sum',
                                '--operation_field',  'contentLength',
                                '--query',  'language:FRENCH' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('value', data['aggregation-1'])
            self.assertEqual(21295969.0, data['aggregation-1']['value'])
            

    def test_aggregate_date_histogram(self):
        with self.existing_luxleaks_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--run',  'date_histogram',
                                '--operation_field',  'metadata.tika_metadata_creation_date' ])

            data = loads(result.output)
            self.assertIn('aggregation-1', data)
            self.assertIn('buckets', data['aggregation-1'])
            self.assertEqual(11, len(data['aggregation-1']['buckets']))
            self.assertIn(1, [bucket['doc_count'] for bucket in data['aggregation-1']['buckets'] if bucket['key_as_string']=='2004-01-01T00:00:00.000Z'])
