from json import loads

from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract


def load_json_file(path):
    return loads(open(path).read())


class TestMultiFilter(TestAbstract):

    def tearDown(self):
        super().tearDown()

    def test_zero_results(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['list-metadata', 
                                        '--elasticsearch-url', self.elasticsearch_url, 
                                        '--datashare-project', self.datashare_project,
                                        '--filter_by', 'type=Document,contentType=message/abc', 
                                        '--count'])
            json_result = loads(result.output)
            self.assertEqual([], json_result)

    def test_some_results(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['list-metadata', 
                                        '--elasticsearch-url', self.elasticsearch_url, 
                                        '--datashare-project', self.datashare_project,
                                        '--filter_by', 'type=Document,contentType=image/png', 
                                        '--count'])
            json_result = loads(result.output)
            self.assertEqual([{'count': 1, 'field': 'contentType', 'type': 'keyword'},
                            {"count": 1, "field": "extractionDate", "type": "date"},
                            {'count': 1, 'field': 'name', 'type': 'text'},
                            {'count': 1, 'field': 'type', 'type': 'keyword'}], json_result)
