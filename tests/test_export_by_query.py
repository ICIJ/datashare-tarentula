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
                csv_reader = csv.reader(csv_file)
                # Skip headers
                next(csv_reader)
                [query, document_url, document_id, root_id, content_type, content_length, document_path, creation_date,
                 document_number] = next(csv_reader)
                self.assertEqual(query, 'Actinopodidae OR Antrodiaetidae')
                self.assertEqual(document_url,
                                 'http://localhost:8080/#/d/test-datashare/DWLOskax28jPQ2CjFrCo/l7VnZZEzg2fr960NWWEG')
                self.assertEqual(document_id, 'DWLOskax28jPQ2CjFrCo')
                self.assertEqual(root_id, 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(content_type, 'audio/vnd.wave')
                self.assertEqual(content_length, '0')
                self.assertEqual(document_path, '')
                datetime_object = datetime.strptime(creation_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                self.assertIsInstance(datetime_object, datetime)
                self.assertEqual(document_number, '0')
                [query, document_url, document_id, root_id, content_type, content_length, document_path, creation_date,
                 document_number] = next(csv_reader)
                self.assertEqual(query, 'Actinopodidae OR Antrodiaetidae')
                self.assertEqual(document_url,
                                 'http://localhost:8080/#/d/test-datashare/l7VnZZEzg2fr960NWWEG/l7VnZZEzg2fr960NWWEG')
                self.assertEqual(document_id, 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(root_id, 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(content_type, 'audio/mpeg')
                self.assertEqual(content_length, '25')
                self.assertEqual(document_path, '/path/to/file.txt')
                datetime_object = datetime.strptime(creation_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                self.assertIsInstance(datetime_object, datetime)
                self.assertEqual(document_number, '1')
