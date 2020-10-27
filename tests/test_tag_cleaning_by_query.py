import logging

from tarentula.cli import cli
from tarentula.logger import add_stdout_handler
from tarentula.tag_cleaning_by_query import TagsCleanerByQuery
from tests.test_abstract import TestAbstract, absolute_path
from click.testing import CliRunner


class TestTagsCleanerByQuery(TestAbstract):
    def test_cli_is_wired_on_tags_cleaner(self):
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, 'clean-tags-by-query')
        self.assertIn('This action will remove all tags for documents matching query', result.output)

    def test_cli_is_wired_on_tags_cleaner_with_no_query_option_selects_all(self):
        self.datashare_client.index(index=self.datashare_project, document={'content': "content", "tags": ["tag"]}, id="id")
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, ['clean-tags-by-query', "--datashare-project", self.datashare_project, "--elasticsearch-url", "http://elasticsearch:9200"])
        self.assertIn('updated 1 documents', result.output)

    def test_cli_is_wired_on_tags_cleaner_with_query_option(self):
        self.datashare_client.index(index=self.datashare_project, document={'content': "content", "tags": ["tag"]}, id="id")
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, ['clean-tags-by-query', "--datashare-project", self.datashare_project, "--elasticsearch-url", "http://elasticsearch:9200", "--query", '{"query": {"ids": {"values": ["id"]}}}'])
        self.assertIn('updated 1 documents', result.output)

    def test_cli_is_wired_on_tags_cleaner_with_background_task(self):
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, ['clean-tags-by-query', "--datashare-project", self.datashare_project, "--elasticsearch-url", "http://elasticsearch:9200", '--no-wait-for-completion'])
        self.assertIn('task created:', result.output)

    def test_cli_is_wired_on_tags_cleaner_with_query_option_in_a_file(self):
        self.datashare_client.index(index=self.datashare_project, document={'content': "content", "tags": ["tag"]}, id="id")
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, ['clean-tags-by-query', "--datashare-project", self.datashare_project, "--elasticsearch-url", "http://elasticsearch:9200", "--query", '@' + absolute_path('tests/fixtures/match_all_query.json')])
        self.assertIn('updated 1 documents', result.output)

    def test_clean_tags(self):
        self.datashare_client.index(index=self.datashare_project, document={"content": "content", "tags": ["tag1", "tag2"]}, id="id")
        TagsCleanerByQuery(self.datashare_project, self.elasticsearch_url).start()
        document = self.datashare_client.document(self.datashare_project, id="id")["_source"]
        self.assertListEqual(document["tags"], [])