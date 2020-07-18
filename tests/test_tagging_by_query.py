import responses

from click.testing import CliRunner
from contextlib import contextmanager

from .test_abstract import TestAbstract, root
from tarentula.cli import cli

class TestTaggingByQuery(TestAbstract):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.json_tags_path = root('tests/fixtures/tags-by-content-type.json')

    def test_summary(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
        self.assertIn('This action will add 8 tag(s)', result.output)

    def test_summary_by_tag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
        self.assertIn('Adding "audio-type" tag', result.output)
        self.assertIn('Adding "document-type" tag', result.output)
        self.assertIn('Adding "email-type" tag', result.output)
        self.assertIn('Adding "image-type" tag', result.output)
        self.assertIn('Adding "other-type" tag', result.output)
        self.assertIn('Adding "presentation-type" tag', result.output)
        self.assertIn('Adding "spreadsheet-type" tag', result.output)
        self.assertIn('Adding "video-type" tag', result.output)

    def test_actinopodidae_and_barychelidae_are_audio(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            actinopodidae = self.datashare_client.document(self.datashare_project, 'l7VnZZEzg2fr960NWWEG')
            tags = actinopodidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)
            barychelidae = self.datashare_client.document(self.datashare_project, 'iuL6GUBpO7nKyfSSFaS0')
            tags = barychelidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)

    def test_three_documents_are_emails(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            self.datashare_client.refresh(self.datashare_project)
            emails = self.datashare_client.query(self.datashare_project, q='tags:email-type AND name:*')
            self.assertEqual(emails['hits']['total'], 3)

    def test_actinopodidae_is_tagged_as_audio_once(self):
        with self.existing_species_documents():
            runner = CliRunner()
            runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            runner.invoke(cli, ['tagging-by-query', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            actinopodidae = self.datashare_client.document(self.datashare_project, 'l7VnZZEzg2fr960NWWEG')
            tags = actinopodidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)
            self.assertEqual(1, len(tags))
