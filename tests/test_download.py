import json
import shutil

from click.testing import CliRunner

from .test_abstract import TestAbstract, root
from tarentula.cli import cli

loadJsonFile = lambda x: json.loads(open(root(x), 'r').read())

class TestDownload(TestAbstract):

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(root('tmp'))

    def test_summary(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_scroll(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*', '--scroll', '1m'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_summary_with_wildcard_sta(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            result = runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:*dae'])
            self.assertIn('Downloading 20 document(s)', result.output)

    def test_meta_is_downloaded_for_actinopodidae(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Actinopodidae'])
            json = loadJsonFile('tmp/l7/Vn/l7VnZZEzg2fr960NWWEG.json')
            self.assertEqual(json['_id'], 'l7VnZZEzg2fr960NWWEG')

    def test_meta_is_downloaded_for_ctenizidae(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Ctenizidae'])
            json = loadJsonFile('tmp/Bm/ov/BmovvXBisWtyyx6o9cuG.json')
            self.assertEqual(json['_id'], 'BmovvXBisWtyyx6o9cuG')

    def test_meta_is_downloaded_for_idiopidae_with_default_properties(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Idiopidae'])
            json = loadJsonFile('tmp/Dz/LO/DzLOskax28jPQ2CjFrCo.json')
            self.assertIn('_id', json)
            self.assertIn('_source', json)
            self.assertNotIn('name', json['_source'])

    def test_meta_is_downloaded_for_idiopidae_with_extra_properties(self):
        with self.existing_species_documents() as species:
            runner = CliRunner()
            runner.invoke(cli, ['download', '--datashare-url', self.datashare_url, '--datashare-project', self.datashare_project, '--no-raw-file', '--query', 'name:Idiopidae', '--source', 'name'])
            json = loadJsonFile('tmp/Dz/LO/DzLOskax28jPQ2CjFrCo.json')
            self.assertIn('_id', json)
            self.assertIn('_source', json)
            self.assertIn('name', json['_source'])
