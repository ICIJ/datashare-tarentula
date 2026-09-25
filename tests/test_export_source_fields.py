import csv

from click.testing import CliRunner
from os.path import join
from tempfile import TemporaryDirectory

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestExportSourceFields(TestAbstract):
    def export(self, output_file, *args):
        runner = CliRunner()
        runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                            self.elasticsearch_url, '--datashare-project', self.datashare_project,
                            '--no-progressbar', '--output-file', output_file] + list(args))
        with open(output_file, newline='') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            return csv_reader.fieldnames, list(csv_reader)

    def test_source_field_with_whitespace_around_colon_default(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            fields, rows = self.export(join(tmp, 'output.csv'), '--query', 'Actinopodidae',
                                       '--source', 'path, contentLength : 0')
            self.assertIn('contentLength', fields)
            self.assertEqual(rows[0]['contentLength'], '25')

    def test_source_with_trailing_comma_adds_no_nameless_column(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            fields, _ = self.export(join(tmp, 'output.csv'), '--query', 'Actinopodidae',
                                    '--source', 'contentType,path,')
            self.assertNotIn('', fields)

    def test_source_named_like_a_default_column_keeps_the_computed_value(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            _, rows = self.export(join(tmp, 'output.csv'), '--query', 'Actinopodidae',
                                  '--source', 'documentId')
            self.assertEqual(rows[0]['documentId'], 'l7VnZZEzg2fr960NWWEG')
