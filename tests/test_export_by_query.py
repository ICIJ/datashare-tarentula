import csv

from click.testing import CliRunner
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory

from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestExportByQuery(TestAbstract):
    def tearDown(self):
        super().tearDown()

    def test_csv_file(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                'Actinopodidae OR Antrodiaetidae', '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)

                # First row
                row = next(csv_reader)
                self.assertEqual(row['query'], 'Actinopodidae OR Antrodiaetidae')
                self.assertEqual(row['documentUrl'],
                                 'http://localhost:8080/#/d/test-datashare/DWLOskax28jPQ2CjFrCo/l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['documentId'], 'DWLOskax28jPQ2CjFrCo')
                self.assertEqual(row['rootId'], 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['contentType'], 'audio/vnd.wave')
                self.assertEqual(row['contentLength'], '0')
                self.assertEqual(row['path'], '')
                datetime_object = datetime.strptime(row['extractionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                self.assertIsInstance(datetime_object, datetime)
                self.assertEqual(row['documentNumber'], '0')

                # Second row
                row = next(csv_reader)
                self.assertEqual(row['query'], 'Actinopodidae OR Antrodiaetidae')
                self.assertEqual(row['documentUrl'],
                                 'http://localhost:8080/#/d/test-datashare/l7VnZZEzg2fr960NWWEG/l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['documentId'], 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['rootId'], 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['contentType'], 'audio/mpeg')
                self.assertEqual(row['contentLength'], '25')
                self.assertEqual(row['path'], '/path/to/file.txt')
                datetime_object = datetime.strptime(row['extractionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                self.assertIsInstance(datetime_object, datetime)
                self.assertEqual(row['documentNumber'], '1')
