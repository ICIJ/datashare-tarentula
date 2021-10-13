from click.testing import CliRunner
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestCount(TestAbstract):
    def tearDown(self):
        super().tearDown()

    def test_count_docs_1(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                            'Actinopodidae OR Antrodiaetidae'])
        self.assertEqual('2', result.output)

    def test_count_docs_2(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['count', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                            '_id:6VEdcVlWszkUd94XeuSd'])
        self.assertEqual('1', result.output)
