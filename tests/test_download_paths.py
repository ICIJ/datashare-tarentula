import io
import os
import tempfile
from os.path import abspath, isdir, join, sep
from urllib.parse import quote

import requests
from click.testing import CliRunner

from .test_abstract import TestAbstract
from tarentula.cli import cli
from tarentula.download import Download


class FakeResponse:
    def __init__(self, raw):
        self.raw = raw

    def raise_for_status(self):
        return None


def files_in(folder):
    return sorted(join(root, name) for root, _, names in os.walk(folder) for name in names)


class TestDownloadPaths(TestAbstract):
    datashare_project = 'test-datashare-paths'

    def setUp(self):
        self.indexed_ids = []

    def tearDown(self):
        for id in self.indexed_ids:
            requests.delete(self.document_url(id), params={'refresh': 'true'})
        super().tearDown()

    def document_url(self, id):
        return f'{self.elasticsearch_url}/{self.datashare_project}/_doc/{quote(id, safe="")}'

    def index_document(self, id, source):
        requests.put(self.document_url(id), json=source, params={'refresh': 'true'}).raise_for_status()
        self.indexed_ids.append(id)

    def invoke_download(self, *args, destination=None, loglevel=None):
        argv = ['--stdout-loglevel', loglevel] if loglevel else []
        argv += ['download', '--datashare-url', self.datashare_url,
                 '--elasticsearch-url', self.elasticsearch_url,
                 '--datashare-project', self.datashare_project, '--no-progressbar']
        if destination is not None:
            argv += ['--destination-directory', destination]
        return CliRunner().invoke(cli, argv + list(args))

    def test_crafted_id_cannot_escape_destination_directory(self):
        self.index_document('../escaped/pwned-by-id', {"type": "Document", "name": "evil", "path": "/d/ok.txt"})
        with tempfile.TemporaryDirectory() as base:
            destination = join(base, 'dest')
            os.makedirs(destination)
            self.invoke_download('--no-raw-file', '--query', 'name:evil', destination=destination)
            outside = [path for path in files_in(base)
                       if not abspath(path).startswith(abspath(destination) + sep)]
            self.assertEqual([], outside)

    def test_crafted_path_cannot_escape_destination_directory(self):
        self.index_document('safe01', {"type": "Document", "name": "evil2", "path": "/data/.."})
        with tempfile.TemporaryDirectory() as base:
            destination = join(base, 'dest')
            os.makedirs(destination)
            self.invoke_download('--no-raw-file', '--query', 'name:evil2',
                                 '--path-format', '{basename}/{id}', destination=destination)
            outside = [path for path in files_in(base)
                       if not abspath(path).startswith(abspath(destination) + sep)]
            self.assertEqual([], outside)

    def test_documents_without_path_do_not_collapse_on_one_file(self):
        self.index_document('nop1', {"type": "Document", "name": "nopath"})
        self.index_document('nop2', {"type": "Document", "name": "nopath"})
        with tempfile.TemporaryDirectory() as destination:
            self.invoke_download('--no-raw-file', '--query', 'name:nopath',
                                 '--path-format', '{basename}', destination=destination)
            self.assertEqual(['nop1.json', 'nop2.json'], sorted(os.listdir(destination)))

    def test_document_without_path_does_not_raise_is_a_directory(self):
        with tempfile.TemporaryDirectory() as destination:
            command = Download(datashare_url=self.datashare_url, elasticsearch_url=self.elasticsearch_url,
                               datashare_project=self.datashare_project, destination_directory=destination,
                               path_format='{basename}')
            document = {'_id': 'nop1', '_source': {'type': 'Document'}}
            command.save_raw_file(document, FakeResponse(io.BytesIO(b'data')))
            self.assertEqual(['nop1'], os.listdir(destination))

    def test_colliding_paths_warn_about_the_overwritten_document(self):
        self.index_document('aaaa1111', {"type": "Document", "name": "coll", "path": "/inbox/2020/report.pdf"})
        self.index_document('bbbb2222', {"type": "Document", "name": "coll", "path": "/inbox/2021/report.pdf"})
        with tempfile.TemporaryDirectory() as destination:
            result = self.invoke_download('--no-raw-file', '--query', 'name:coll', '--path-format', '{basename}',
                                          destination=destination, loglevel='WARNING')
            self.assertIn('report.pdf.json', result.output)
            self.assertIn('already downloaded', result.output)

    def test_unknown_path_format_placeholder_reports_available_placeholders(self):
        self.index_document('aaaa1111', {"type": "Document", "name": "coll", "path": "/inbox/report.pdf"})
        with tempfile.TemporaryDirectory() as destination:
            result = self.invoke_download('--no-raw-file', '--query', 'name:coll',
                                          '--path-format', '{foo}/{id}', destination=destination)
            self.assertNotIsInstance(result.exception, KeyError)
            self.assertIn('--path-format', result.output)
            self.assertIn('parentDocument', result.output)

    def test_parent_document_placeholder_is_not_literal_none(self):
        self.index_document('dddd4444', {"type": "Document", "name": "child", "path": "/inbox/a.zip"})
        with tempfile.TemporaryDirectory() as destination:
            self.invoke_download('--no-raw-file', '--query', 'name:child',
                                 '--path-format', '{parentDocument}/{id}', destination=destination)
            self.assertFalse(isdir(join(destination, 'None')))
            self.assertEqual(['dddd4444.json'], sorted(os.listdir(destination)))
