from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract
from .test_download import load_json_file

class TestAggregate(TestAbstract):
    def tearDown(self):
        super().tearDown()

    @staticmethod
    def extract_num_docs_from_response(message):
        return message.rsplit(" ", 1)[1].strip()

    def test_aggregate_all(self):
        with self.existing_species_documents():
            runner = CliRunner()

            result = runner.invoke(cli, ['aggregate', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--by',  'contentType',
                                # '--count'
                                '--query',  '*' ])

            json_file = load_json_file('tests/fixtures/species_test_aggs_response_1.json')
            loads(result.output)

            # self.assertIn('_id', json_file)
            # self.assertIn('_source', json_file)
            # self.assertNotIn('name', json_file['_source'])
