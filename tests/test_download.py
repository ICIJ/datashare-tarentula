import glob
import io
import json
import os
from contextlib import contextmanager
from os.path import exists, getsize, join
from tempfile import TemporaryDirectory

from click.testing import CliRunner
from requests.exceptions import HTTPError
from urllib3.exceptions import ProtocolError

from .test_abstract import TestAbstract
from tarentula.cli import cli
from tarentula.download import Download


def load_json_file(path):
    return json.loads(open(path).read())


class FakeResponse:
    def __init__(self, raw):
        self.raw = raw

    def raise_for_status(self):
        return None


class FlakyRaw(io.RawIOBase):
    def __init__(self, data, fail_after):
        self.buffer = io.BytesIO(data)
        self.fail_after = fail_after
        self.sent = 0

    def read(self, size=-1):
        if self.sent >= self.fail_after:
            raise ProtocolError('Connection broken: IncompleteRead')
        chunk = self.buffer.read(min(size if size and size > 0 else 8192, self.fail_after - self.sent))
        self.sent += len(chunk)
        return chunk


class TestDownload(TestAbstract):
    datashare_project = 'test-datashare-download'

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

    @contextmanager
    def existing_documents(self, documents):
        self.index_documents(documents)
        try:
            yield documents
        finally:
            self.delete_documents(documents)

    def download_command(self, destination_directory, once=False):
        return Download(datashare_url=self.datashare_url, elasticsearch_url=self.elasticsearch_url,
                        datashare_project=self.datashare_project, destination_directory=destination_directory,
                        query='name:raw*', path_format='{id}', size=1000, progressbar=False, once=once)

    def test_broken_stream_keeps_no_truncated_file_and_does_not_abort_the_run(self):
        documents = [{'_id': f'f{i}', 'name': f'raw{i}', 'type': 'Document', 'path': f'/d/{i}.txt'} for i in range(3)]
        with self.existing_documents(documents), TemporaryDirectory() as tmp:
            command = self.download_command(tmp)
            command.datashare_client.download = lambda project, id, routing: FakeResponse(
                FlakyRaw(b'X' * 100000, 4096) if id == 'f0' else io.BytesIO(b'Y' * 10))
            command.start()
            self.assertEqual(['f0.json', 'f1', 'f1.json', 'f2', 'f2.json'], sorted(os.listdir(tmp)))

    def test_once_redownloads_a_file_broken_by_a_previous_run(self):
        documents = [{'_id': 'f0', 'name': 'raw0', 'type': 'Document', 'path': '/d/0.txt'}]
        with self.existing_documents(documents), TemporaryDirectory() as tmp:
            first = self.download_command(tmp)
            first.datashare_client.download = lambda project, id, routing: FakeResponse(FlakyRaw(b'X' * 100000, 4096))
            first.start()
            self.assertFalse(exists(join(tmp, 'f0')))
            second = self.download_command(tmp, once=True)
            second.datashare_client.download = lambda project, id, routing: FakeResponse(io.BytesIO(b'X' * 100000))
            second.start()
            self.assertEqual(100000, getsize(join(tmp, 'f0')))

    def test_named_entities_metadata_is_downloaded(self):
        documents = [{'_id': f'ne{i}', 'name': f'ent{i}', 'type': 'NamedEntity'} for i in range(3)]
        with self.existing_documents(documents), TemporaryDirectory() as tmp:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--destination-directory', tmp, '--query', 'name:ent*', '--type', 'NamedEntity', '--path-format', '{id}'])
            self.assertEqual(['ne0.json', 'ne1.json', 'ne2.json'], sorted(os.listdir(tmp)))

    def test_summary_with_from_greater_than_total(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--from', 100, '--query', 'name:*'])
            self.assertIn('Downloading 0 document(s)', result.output)

    def test_summary_with_scroll_ignores_from(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--scroll', '1m', '--from', 5, '--query', 'name:*'])
            self.assertIn(f'Downloading {len(get_document_files(tmp))} document(s)', result.output)

    def test_limit_downloads_exactly_the_requested_number_of_documents(self):
        with self.existing_species_documents(), TemporaryDirectory() as tmp:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--destination-directory', tmp, '--query', 'name:*', '--path-format', '{id}', '--limit', 15, '--size', 7])
            self.assertIn('Downloading 15 document(s)', result.output)
            self.assertEqual(15, len(get_document_files(tmp, '*.json')))

    def test_unknown_project_reports_a_readable_count_error(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--elasticsearch-url', self.elasticsearch_url, '--datashare-project', 'test-datashare-typo', '--no-raw-file', '--query', 'name:*'])
        self.assertNotIsInstance(result.exception, HTTPError)
        self.assertEqual(1, result.exit_code)
        self.assertIn('test-datashare-typo', result.output)


def get_document_files(folder: str, pattern: str = '*/*/*.json'):
    return glob.glob(join(folder, pattern))
