from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestCount(TestAbstract):
    def tearDown(self):
        super().tearDown()

    @staticmethod
    def extract_num_docs_from_response(message):
        return message.rsplit(" ", 1)[1].strip()

    def test_count_all(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project])
            self.assertEqual('20', self.extract_num_docs_from_response(result.output))

            result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                '*'])
            self.assertEqual('20', self.extract_num_docs_from_response(result.output))

    def test_count_docs_1(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                'Actinopodidae OR Antrodiaetidae'])
            self.assertEqual('2', self.extract_num_docs_from_response(result.output))

    def test_count_docs_2(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                '_id:6VEdcVlWszkUd94XeuSd'])
            self.assertEqual('1', self.extract_num_docs_from_response(result.output))
