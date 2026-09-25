from .test_abstract import TestAbstract
from tarentula.config_file_reader import ConfigFileReader
from tempfile import mkdtemp
from unittest import mock

import os

class TestConfigFileReader(TestAbstract):

    def test_load_from_env_with_relative_path(self):
        with mock.patch.dict(os.environ, {'TARENTULA_CONFIG': './tests/fixtures/tarentula.ini'}):
            reader = ConfigFileReader('datashare_url')
            self.assertEqual(reader.config_path, os.path.abspath('./tests/fixtures/tarentula.ini'))

    def test_load_from_env_with_absolute_path(self):
        with mock.patch.dict(os.environ, {'TARENTULA_CONFIG': os.path.abspath('./tests/fixtures/tarentula.ini')}):
            reader = ConfigFileReader('datashare_url')
            self.assertEqual(reader.config_path, os.path.abspath('./tests/fixtures/tarentula.ini'))

    def test_load_from_current_directory(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('datashare_url')
            self.assertEqual(reader.config_path, os.path.abspath('./tarentula.ini'))

    def test_load_datashare_url_in_working_directory(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('datashare_url')
            self.assertEqual(reader(), 'http://here:8080')

    def test_load_non_case_sensitive(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('datashare_URL')
            self.assertEqual(reader(), 'http://here:8080')

    def test_load_default_datashare_project_in_working_directory(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('datashare_project', 'local-datashare')
            self.assertEqual(reader(), 'local-datashare')

    def test_load_default_datashare_url(self):
        reader = ConfigFileReader('datashare_url', 'http://localhost:8080')
        self.assertEqual(reader(), 'http://localhost:8080')

    def test_load_section_in_working_directory(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('stdout_loglevel', section='logger')
            self.assertEqual(reader(), 'DEBUG')

    def test_load_section_default_in_working_directory(self):
        with self.working_directory('./tests/fixtures/'):
            reader = ConfigFileReader('syslog_address', 'here', section='logger')
            self.assertEqual(reader(), 'here')

    def test_load_default_section_without_logger_section(self):
        config_path = os.path.join(mkdtemp(), 'tarentula.ini')
        with open(config_path, 'w') as config_file:
            config_file.write('[DEFAULT]\nstdout_loglevel = DEBUG\n')
        with mock.patch.dict(os.environ, {'TARENTULA_CONFIG': config_path}):
            reader = ConfigFileReader('stdout_loglevel', 'ERROR', 'logger')
            self.assertEqual(reader(), 'DEBUG')

    def test_config_is_not_cached_across_directories(self):
        reader = ConfigFileReader('datashare_url', 'http://localhost:8080')
        with self.working_directory('./tests/fixtures/'):
            first = reader()
        second = reader()
        self.assertEqual((first, second), ('http://here:8080', 'http://localhost:8080'))
