import json
from os.path import join
from tempfile import TemporaryDirectory

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
