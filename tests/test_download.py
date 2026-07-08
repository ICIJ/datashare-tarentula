import glob
import json
import threading
from os.path import join
from tempfile import TemporaryDirectory
from unittest.mock import patch

import aiohttp
from click.testing import CliRunner

from .test_abstract import TestAbstract
from tarentula.cli import cli


def load_json_file(path):
    return json.loads(open(path).read())


class TestDownload(TestAbstract):

    def tearDown(self):
        super().tearDown()

    def test_summary(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_scroll(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*', '--scroll', '1m'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard_sta(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_meta_is_downloaded_for_actinopodidae(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--query', 'name:Actinopodidae'])
            json_file = load_json_file(join(tmp, 'l7/Vn/l7VnZZEzg2fr960NWWEG.json'))
            self.assertEqual(json_file['_id'], 'l7VnZZEzg2fr960NWWEG')

    def test_meta_is_downloaded_for_ctenizidae(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--query', 'name:Ctenizidae'])
            json_file = load_json_file(join(tmp, 'Bm/ov/BmovvXBisWtyyx6o9cuG.json'))
            self.assertEqual(json_file['_id'], 'BmovvXBisWtyyx6o9cuG')

    def test_meta_is_downloaded_for_idiopidae_with_default_properties(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project',
                                self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--query', 'name:Idiopidae'])
            json_file = load_json_file(join(tmp, 'Dz/LO/DzLOskax28jPQ2CjFrCo.json'))
            self.assertIn('_id', json_file)
            self.assertIn('_source', json_file)
            self.assertNotIn('name', json_file['_source'])

    def test_meta_is_downloaded_for_idiopidae_with_extra_properties(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--destination-directory', tmp, '--no-raw-file', '--query', 'name:Idiopidae', '--source', 'name'])
            json = load_json_file(join(tmp, 'Dz/LO/DzLOskax28jPQ2CjFrCo.json'))
            self.assertIn('_id', json)
            self.assertIn('_source', json)
            self.assertIn('name', json['_source'])

    def test_summary_with_from(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()

            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--from', 5, '--query', 'name:*'])
            self.assertIn('Downloading 15 document(s)', result.output)
            self.assertEqual(15, len(get_document_files(tmp)))

    def test_scroll_flag_is_deprecated_but_downloads(self):
        with self.existing_species_documents():
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url,
                                         '--elasticsearch-url', self.elasticsearch_url,
                                         '--datashare-project', self.datashare_project,
                                         '--no-raw-file', '--query', 'name:*', '--scroll', '1m'])
            self.assertIn('Downloading 20 document(s)', result.output)
            self.assertIn('deprecated', result.output.lower())

    def test_all_documents_downloaded_with_concurrency(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url,
                                '--elasticsearch-url', self.elasticsearch_url,
                                '--datashare-project', self.datashare_project,
                                '--no-raw-file', '--destination-directory', tmp,
                                '--query', 'name:*', '--concurrency', '8'])
            self.assertEqual(20, len(get_document_files(tmp)))

    def test_download_all_with_pit_direct_es(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url,
                                '--elasticsearch-url', self.elasticsearch_url,
                                '--datashare-project', self.datashare_project,
                                '--no-raw-file', '--destination-directory', tmp, '--query', 'name:*'])
            self.assertEqual(20, len(get_document_files(tmp)))

    def test_download_completes_when_all_downloads_fail(self):
        # Every raw-file download raises a non-ClientResponseError. Workers must log-and-continue
        # (except Exception) rather than dying; otherwise the producer would block forever on the
        # bounded queue once more than concurrency*2 docs flow through. The 20-doc fixture with
        # raw-file enabled and concurrency 4 exceeds that threshold.
        #
        # A regression re-introducing the deadlock leaves the download thread stuck inside
        # asyncio.run forever. We run the CLI in a *daemon* thread and join with a timeout: on
        # regression the join returns after the timeout, the assertFalse fails cleanly, and the
        # daemon thread does not block the rest of the suite or interpreter exit. (A plain
        # ThreadPoolExecutor context manager cannot be used here: its non-daemon worker plus
        # shutdown(wait=True) on __exit__ would itself hang the suite on regression.)
        async def boom(*a, **k):
            raise aiohttp.ClientError('boom')
        box = {}

        def run(runner):
            box['result'] = runner.invoke(cli, ['download',
                '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url,
                '--datashare-project', self.datashare_project, '--destination-directory', box['tmp'],
                '--query', 'name:*', '--concurrency', '4'])

        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            box['tmp'] = tmp
            with patch('tarentula.async_client.AsyncDatashareClient.stream_download', boom):
                worker = threading.Thread(target=run, args=(CliRunner(),), daemon=True)
                worker.start()
                worker.join(timeout=90)  # regression = deadlock = still alive after timeout
                self.assertFalse(worker.is_alive(), 'download deadlocked: worker died without draining queue')
        self.assertEqual(0, box['result'].exit_code)

    def test_download_reports_producer_error_cleanly(self):
        # A producer/search error (e.g. search_after_scan raising RuntimeError on a non-2xx
        # status) must be caught at the CLI boundary and logged cleanly, not let a raw
        # traceback escape start() uncaught.
        async def boom(*a, **k):
            raise RuntimeError('boom-search')
            yield  # pragma: no cover - makes this an async generator function

        with self.existing_species_documents():
            with patch('tarentula.async_client.AsyncDatashareClient.search_after_scan', boom):
                runner = CliRunner()
                result = runner.invoke(cli, ['download',
                    '--datashare-url', self.datashare_url,
                    '--elasticsearch-url', self.elasticsearch_url,
                    '--datashare-project', self.datashare_project,
                    '--no-raw-file', '--query', 'name:*'])
        self.assertEqual(1, result.exit_code)
        # A clean sys.exit(1) surfaces as SystemExit here (Click's own error-handling
        # convention), not the raw RuntimeError escaping uncaught.
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn('Download failed', result.output)
        self.assertNotIn('Traceback', result.output)

    def test_concurrency_must_be_positive(self):
        # --concurrency 0 used to yield zero workers with an *unbounded*
        # asyncio.Queue(maxsize=0): the producer fills the queue and nothing ever consumes it,
        # so the command silently exits 0 having downloaded nothing. Reject it up front.
        runner = CliRunner()
        result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url,
                                     '--elasticsearch-url', self.elasticsearch_url,
                                     '--datashare-project', self.datashare_project,
                                     '--concurrency', '0'])
        self.assertNotEqual(0, result.exit_code)
        self.assertIsInstance(result.exception, SystemExit)


def get_document_files(folder: str, pattern: str = '*/*/*.json'):
    return glob.glob(join(folder, pattern))
