from importlib import metadata, reload
from unittest import mock

from click.testing import CliRunner

from .test_abstract import TestAbstract
from tarentula.cli import cli
import tarentula
from tarentula import __version__

class TestVersion(TestAbstract):

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        self.assertIn('v%s' % __version__, result.output)

    def test_version_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        self.assertIn('Show the version and exit.', result.output)

    def test_version_without_installed_package_metadata(self):
        with mock.patch('importlib.metadata.version', side_effect=metadata.PackageNotFoundError):
            reload(tarentula)
            self.assertEqual(tarentula.__version__, '0.0.0')
        reload(tarentula)
