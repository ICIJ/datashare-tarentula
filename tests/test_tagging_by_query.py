from click.testing import CliRunner

from tarentula.cli import cli
from .test_abstract import TestAbstract, absolute_path


class TestTaggingByQuery(TestAbstract):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.json_tags_path = absolute_path('tests/fixtures/tags-by-content-type.json')

    def test_summary(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--datashare-project', self.datashare_project, self.json_tags_path])
        self.assertIn('This action will add 8 tag(s)', result.output)

    def test_summary_by_tag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--datashare-project', self.datashare_project, self.json_tags_path])
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
            result = runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            actinopodidae = self.datashare_client.document(self.datashare_project, 'l7VnZZEzg2fr960NWWEG')
            tags = actinopodidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)
            barychelidae = self.datashare_client.document(self.datashare_project, 'iuL6GUBpO7nKyfSSFaS0')
            tags = barychelidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)

    def test_three_documents_are_emails(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            self.datashare_client.refresh(self.datashare_project)
            emails = self.datashare_client.query(self.datashare_project, q='tags:email-type AND name:*')
            self.assertEqual(emails['hits']['total']['value'], 3)

    def test_actinopodidae_is_tagged_as_audio_once(self):
        with self.existing_species_documents():
            runner = CliRunner()
            runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path])
            actinopodidae = self.datashare_client.document(self.datashare_project, 'l7VnZZEzg2fr960NWWEG')
            tags = actinopodidae.get('_source', {}).get('tags', [])
            self.assertIn('audio-type', tags)
            self.assertEqual(1, len(tags))

    def test_tasks_are_created(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path, '--no-wait-for-completion'])
        self.assertEqual(result.output.count('task created'), 8)
        self.assertEqual(result.output.count('documents updated in'), 0)

    def test_tasks_are_not_created(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path, '--wait-for-completion'])
        self.assertEqual(result.output.count('task created'), 0)
        self.assertEqual(result.output.count('documents updated in'), 8)

    def test_progressbar_is_not_created(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path, '--no-progressbar'])
        self.assertNotIn('This action will add 8 tag(s)', result.output)

    def test_logs_are_printed_to_stdout(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--stdout-loglevel', 'INFO', 'tagging-by-query', '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, self.json_tags_path])
        self.assertNotIn('This action will add 8 tag(s)', result.output)
        self.assertEqual(result.output.count('Documents tagged with'), 16)  # logs + stdout
