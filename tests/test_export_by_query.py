import csv
import requests

from click.testing import CliRunner
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory

from tarentula.cli import cli
from tarentula.export_by_query import ExportByQuery
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
                                 'http://localhost:8080/#/d/test-datashare/l7VnZZEzg2fr960NWWEG/l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['documentId'], 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['rootId'], 'l7VnZZEzg2fr960NWWEG')
                self.assertEqual(row['contentType'], 'audio/mpeg')
                self.assertEqual(row['contentLength'], '25')
                self.assertEqual(row['path'], '/path/to/file.txt')
                datetime_object = datetime.strptime(row['extractionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                self.assertIsInstance(datetime_object, datetime)
                self.assertEqual(row['documentNumber'], '0')

                # Second row
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
                self.assertEqual(row['documentNumber'], '1')

    def test_csv_file_with_from(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                'Actinopodidae OR Antrodiaetidae', 
                                '--from', 1, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 1) # total size is 2 documents

    def test_csv_file_with_limit_1(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--limit', 3, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 3)

    def test_csv_file_with_limit_2(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--from', 2, '--limit', 3, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 3)

    def test_csv_file_with_limit_3(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--size', 2, '--limit', 10, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 10)

    def test_csv_file_with_limit_4(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, 
                                '--size', 20, '--limit', 3, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 3)

    def test_csv_file_with_scroll(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project,
                                '--scroll', '1m', '--size', 2, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 20)

    def test_csv_file_with_scroll_and_limit(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project,
                                '--scroll', '1m', '--size', 2, '--limit', 3, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 3)

    def test_csv_file_with_scroll_and_from(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project,
                                '--scroll', '1m', '--size', 2, '--from', 5, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 20)

    def test_count_matches_with_from_past_the_end(self):
        with self.existing_species_documents():
            export = ExportByQuery(datashare_url=self.datashare_url, elasticsearch_url=self.elasticsearch_url,
                                   datashare_project=self.datashare_project, from_=25, progressbar=False)
            self.assertEqual(export.count_matches(), 0)

    def test_count_matches_ignores_from_when_scrolling(self):
        with self.existing_species_documents():
            export = ExportByQuery(datashare_url=self.datashare_url, elasticsearch_url=self.elasticsearch_url,
                                   datashare_project=self.datashare_project, scroll='1m', from_=5, progressbar=False)
            self.assertEqual(export.count_matches(), 20)

    def test_malformed_query_reports_the_elasticsearch_reason(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            with self.assertLogs('tarentula', level='CRITICAL') as logs:
                result = runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url,
                                             '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                             self.datashare_project, '--query', 'name:(', '--no-progressbar',
                                             '--output-file', output_file])
            self.assertEqual(result.exit_code, 1)
            self.assertIn('Failed to parse query', '\n'.join(logs.output))

    def test_unknown_project_reports_the_elasticsearch_reason(self):
        with TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            with self.assertLogs('tarentula', level='CRITICAL') as logs:
                result = runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url,
                                             '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                             'test-datashaer', '--no-progressbar', '--output-file', output_file])
            self.assertEqual(result.exit_code, 1)
            self.assertIn('no such index', '\n'.join(logs.output))

    def test_csv_file_with_limit_not_multiple_of_size(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project,
                                '--size', 4, '--limit', 6, '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                ids = [row['documentId'] for row in csv.DictReader(csv_file)]
                self.assertEqual(len(ids), 6)
                self.assertEqual(len(set(ids)), 6)

    def test_csv_file_sorted_by_a_field_with_ties(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project,
                                '--size', 2, '--sort-by', 'type', '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                self.assertEqual(len(list(csv_reader)), 20)

    def test_csv_file_beyond_max_result_window(self):
        index = 'test-datashare-narrow-window'
        requests.put(f'{self.elasticsearch_url}/{index}',
                     json={'settings': {'index': {'max_result_window': 20}}}).raise_for_status()
        try:
            for number in range(30):
                self.datashare_client.index(index=index, document={'type': 'Document', 'content': f'c{number}'})
            self.datashare_client.refresh(index=index)
            with TemporaryDirectory() as tmp:
                output_file = join(tmp, 'output.csv')
                runner = CliRunner()
                result = runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url,
                                             '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                             index, '--size', 10, '--no-progressbar', '--output-file', output_file])
                self.assertIsNone(result.exception)
                with open(output_file, newline='') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    self.assertEqual(len(list(csv_reader)), 30)
        finally:
            self.datashare_client.delete_index(index)
