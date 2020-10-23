import logging

from tarentula.cli import cli
from tarentula.logger import add_stdout_handler
from tarentula.tag_cleaning_by_query import TagsCleanerByQuery
from tests.test_abstract import TestAbstract
from click.testing import CliRunner


class TestTagsCleanerByQuery(TestAbstract):
    def test_cli_is_wired_on_tags_cleaner(self):
        add_stdout_handler(level=logging.INFO)
        runner = CliRunner()
        result = runner.invoke(cli, "clean-tags-by-query")
        self.assertIn('This action will remove all tags for documents matching query', result.output)

    def test_clean_tags(self):
        self.datashare_client.index(index=self.datashare_project, document={"content": "content", "tags": ["tag1", "tag2"]}, id="id")
        TagsCleanerByQuery(self.datashare_project, self.elasticsearch_url).start()
        document = self.datashare_client.document(self.datashare_project, id="id")["_source"]
        self.assertListEqual(document["tags"], [])