import asyncio
import csv

from click.testing import CliRunner
from datetime import datetime
from os.path import join
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from tarentula.async_client import AsyncDatashareClient
from tarentula.cli import cli
from .test_abstract import TestAbstract


class TestExportByQuery(TestAbstract):
    def tearDown(self):
        super().tearDown()

    def test_pit_keep_alive_option_is_passed_through(self):
        # --pit-keep-alive must reach search_after_scan's keep_alive kwarg (default '10m' when
        # not given, so a slow multi-page export does not outlive a too-short PIT window).
        captured = {}
        original = AsyncDatashareClient.search_after_scan

        def spy(self, *args, **kwargs):
            captured.update(kwargs)
            return original(self, *args, **kwargs)

        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            with patch('tarentula.async_client.AsyncDatashareClient.search_after_scan', spy):
                runner = CliRunner()
                runner.invoke(cli, ['export-by-query',
                    '--datashare-url', self.datashare_url,
                    '--elasticsearch-url', self.elasticsearch_url,
                    '--datashare-project', self.datashare_project,
                    '--query', 'name:*', '--output-file', output_file,
                    '--pit-keep-alive', '5m'])
        self.assertEqual('5m', captured.get('keep_alive'))

    def test_export_reports_producer_error_cleanly(self):
        # A producer/search error (e.g. search_after_scan raising RuntimeError on a non-2xx
        # status) must be caught at the CLI boundary and logged cleanly, not let a raw
        # traceback escape start() uncaught.
        async def boom(*a, **k):
            raise RuntimeError('boom-search')
            yield  # pragma: no cover - makes this an async generator function

        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            with patch('tarentula.async_client.AsyncDatashareClient.search_after_scan', boom):
                runner = CliRunner()
                result = runner.invoke(cli, ['export-by-query',
                    '--datashare-url', self.datashare_url,
                    '--elasticsearch-url', self.elasticsearch_url,
                    '--datashare-project', self.datashare_project,
                    '--query', 'name:*', '--output-file', output_file])
        self.assertEqual(1, result.exit_code)
        # A clean sys.exit(1) surfaces as SystemExit here (Click's own error-handling
        # convention), not the raw RuntimeError escaping uncaught.
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn('Export failed', result.output)
        self.assertNotIn('Traceback', result.output)

    def test_throttle_sleeps_between_rows_and_still_exports_everything(self):
        # --throttle used to be silently ignored by export-by-query (unlike download, which
        # honors it per-item). Honor it here too: after writing each CSV row, sleep
        # throttle/1000 seconds. Assert the sleep is invoked (a timing assertion would be
        # flaky) and that the export still produces correct/complete output.
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            with patch('tarentula.export_by_query.asyncio.sleep',
                      new_callable=AsyncMock) as mock_sleep:
                runner = CliRunner()
                runner.invoke(cli, ['export-by-query',
                    '--datashare-url', self.datashare_url,
                    '--elasticsearch-url', self.elasticsearch_url,
                    '--datashare-project', self.datashare_project,
                    '--query', 'name:*', '--output-file', output_file,
                    '--throttle', '50'])
            with open(output_file, newline='') as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(20, len(rows))
            mock_sleep.assert_called_with(0.05)

    def test_export_reports_timeout_error_cleanly(self):
        # _send() re-raises a bare asyncio.TimeoutError (not an aiohttp.ClientError subclass)
        # once its retries are exhausted. start() must catch it too, not let it escape as a raw
        # traceback.
        async def boom(*a, **k):
            raise asyncio.TimeoutError('boom-timeout')
            yield  # pragma: no cover - makes this an async generator function

        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            with patch('tarentula.async_client.AsyncDatashareClient.search_after_scan', boom):
                runner = CliRunner()
                result = runner.invoke(cli, ['export-by-query',
                    '--datashare-url', self.datashare_url,
                    '--elasticsearch-url', self.elasticsearch_url,
                    '--datashare-project', self.datashare_project,
                    '--query', 'name:*', '--output-file', output_file])
        self.assertEqual(1, result.exit_code)
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn('Export failed', result.output)
        self.assertNotIn('Traceback', result.output)

    def test_csv_file(self):
        # These two documents tie on _score, so their relative order depends on the
        # tiebreaker used by the underlying pagination (_id ascending on the plain
        # search_after path, _shard_doc ascending under Point-in-Time). Both are valid
        # orderings, so assert on the *set* of rows keyed by documentId rather than a
        # specific physical row order, which is an implementation detail.
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output_file = join(tmp, 'output.csv')
            runner = CliRunner()
            runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url, '--elasticsearch-url',
                                self.elasticsearch_url, '--datashare-project', self.datashare_project, '--query',
                                'Actinopodidae OR Antrodiaetidae', '--output-file', output_file])
            with open(output_file, newline='') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                rows = list(csv_reader)

            self.assertEqual(len(rows), 2)
            rows_by_id = {row['documentId']: row for row in rows}
            self.assertEqual(set(rows_by_id.keys()),
                             {'DWLOskax28jPQ2CjFrCo', 'l7VnZZEzg2fr960NWWEG'})
            self.assertEqual({row['documentNumber'] for row in rows}, {'0', '1'})

            row = rows_by_id['DWLOskax28jPQ2CjFrCo']
            self.assertEqual(row['query'], 'Actinopodidae OR Antrodiaetidae')
            self.assertEqual(row['documentUrl'],
                             'http://localhost:8080/#/d/test-datashare/DWLOskax28jPQ2CjFrCo/l7VnZZEzg2fr960NWWEG')
            self.assertEqual(row['rootId'], 'l7VnZZEzg2fr960NWWEG')
            self.assertEqual(row['contentType'], 'audio/vnd.wave')
            self.assertEqual(row['contentLength'], '0')
            self.assertEqual(row['path'], '')
            datetime_object = datetime.strptime(row['extractionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            self.assertIsInstance(datetime_object, datetime)

            row = rows_by_id['l7VnZZEzg2fr960NWWEG']
            self.assertEqual(row['query'], 'Actinopodidae OR Antrodiaetidae')
            self.assertEqual(row['documentUrl'],
                             'http://localhost:8080/#/d/test-datashare/l7VnZZEzg2fr960NWWEG/l7VnZZEzg2fr960NWWEG')
            self.assertEqual(row['rootId'], 'l7VnZZEzg2fr960NWWEG')
            self.assertEqual(row['contentType'], 'audio/mpeg')
            self.assertEqual(row['contentLength'], '25')
            self.assertEqual(row['path'], '/path/to/file.txt')
            datetime_object = datetime.strptime(row['extractionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            self.assertIsInstance(datetime_object, datetime)

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

    def test_export_scroll_deprecated_and_exports_all(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            output = join(tmp, 'out.csv')
            runner = CliRunner()
            result = runner.invoke(cli, ['export-by-query', '--datashare-url', self.datashare_url,
                                         '--elasticsearch-url', self.elasticsearch_url,
                                         '--datashare-project', self.datashare_project,
                                         '--query', 'name:*', '--output-file', output, '--scroll', '1m'])
            self.assertIn('deprecated', result.output.lower())
            with open(output) as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(21, len(rows))  # header + 20 documents

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
