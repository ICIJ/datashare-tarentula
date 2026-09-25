import json
import os

from tempfile import mkdtemp
from unittest import TestCase

from click.testing import CliRunner

from tarentula.cli import cli
from tarentula.command import Command


class TestQueryOption(TestCase):
    elasticsearch_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')

    def setUp(self):
        self.query_path = os.path.join(mkdtemp(), 'matchall.json')
        with open(self.query_path, 'w') as json_file:
            json.dump({"query": {"match_all": {}}}, json_file)

    def count(self, *args):
        return CliRunner().invoke(cli, ['count', '--elasticsearch-url', self.elasticsearch_url, *args])

    def test_at_prefixed_query_string_does_not_raise_a_file_not_found_traceback(self):
        result = self.count('--query', '@icij.org')
        self.assertNotIsInstance(result.exception, FileNotFoundError)
        self.assertIn('no such query file: icij.org', result.output)

    def test_missing_query_file_is_a_bad_parameter(self):
        result = self.count('--query', '@nowhere/matchall.json')
        self.assertEqual(result.exit_code, 2)
        self.assertIn('nowhere/matchall.json', result.output)

    def test_type_filter_is_kept_with_a_file_query(self):
        from_string = Command('*', 'NamedEntity').query_body
        from_file = Command('@' + self.query_path, 'NamedEntity').query_body
        self.assertIn({"match": {"type": "NamedEntity"}}, from_file['query']['bool']['must'])
        self.assertIn({"match": {"type": "NamedEntity"}}, from_string['query']['bool']['must'])
        self.assertIn({"match_all": {}}, from_file['query']['bool']['must'])


class TestSyslogOptions(TestCase):
    def invoke(self, *args):
        return CliRunner().invoke(cli, [*args, 'count', '--help'])

    def test_unresolvable_syslog_address_does_not_kill_the_command(self):
        result = self.invoke('--syslog-address', 'syslog.invalid.example')
        self.assertEqual(result.exit_code, 0, result.exception)
        self.assertIn('--query', result.output)

    def test_non_numeric_syslog_port_is_a_bad_parameter(self):
        result = self.invoke('--syslog-port', 'abc')
        self.assertEqual(result.exit_code, 2)
        self.assertNotIsInstance(result.exception, ValueError)

    def test_unknown_syslog_facility_is_a_bad_parameter(self):
        result = self.invoke('--syslog-facility', 'local8')
        self.assertEqual(result.exit_code, 2)
        self.assertNotIn('Logging error', result.output)
