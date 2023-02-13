from datetime import datetime
from json import loads

from click.testing import CliRunner

from tarentula.cli import cli
from tests.test_abstract import TestAbstract


class TestMetadataFields(TestAbstract):
    def tearDown(self):
        self.datashare_client.delete_all(index=self.datashare_project)

    def test_basic_metadata_field_list(self):
        self.index_documents([{"name": "Antrodiaetidae", "type": "Document", "contentType": "audio/vnd.wave",
                               "_id": "id1"}
                              ])
        runner = CliRunner()
        result = runner.invoke(cli, ['list-metadata', '--elasticsearch-url',
                                     self.elasticsearch_url, '--datashare-project', self.datashare_project])
        json_result = loads(result.output)
        self.assertEqual([
            {"field": "contentType", "type": "keyword", "count": 1},
            {"field": "extractionDate", "type": "date", "count": 1},
            {"field": "name", "type": "text", "count": 1},
            {"field": "type", "type": "keyword", "count": 1}], json_result)

    def test_basic_metadata_field_list_with_tika_metadata(self):
        self.index_documents([{"name": "Antrodiaetidae", "type": "Document", "contentType": "audio/vnd.wave",
                               "_id": "id1",
                               "metadata": {"tika_metadata_dcterms_created": datetime.utcnow().isoformat()}}
                              ])
        runner = CliRunner()
        result = runner.invoke(cli, ['list-metadata', '--elasticsearch-url',
                                     self.elasticsearch_url, '--datashare-project', self.datashare_project])
        json_result = loads(result.output)
        self.assertEqual([{'count': 1, 'field': 'contentType', 'type': 'keyword'},
                          {'count': 1, 'field': 'extractionDate', 'type': 'date'},
                          {'count': 1,
                           'field': 'metadata.tika_metadata_dcterms_created',
                           'type': 'date'},
                          {'count': 1, 'field': 'name', 'type': 'text'},
                          {'count': 1, 'field': 'type', 'type': 'keyword'}], json_result)

    def test_metadata_field_filter_no_sum(self):
        self.index_documents([
            {"name": "Antrodiaetidae", "type": "Document", "contentType": "audio/vnd.wave", "_id": "id1"},
            {"name": "Antrodiaetidae", "type": "Document", "contentType": "message/rfc822", "subject": "hello world", "_id": "id2"}
        ])
        runner = CliRunner()
        result = runner.invoke(cli, ['list-metadata', 
                                    '--elasticsearch-url', self.elasticsearch_url, 
                                    '--datashare-project', self.datashare_project,
                                    '--query_filter', 'contentType=audio/vnd.wave', 
                                    ])
        json_result = loads(result.output)
        self.assertEqual([{'count': 1, 'field': 'contentType', 'type': 'keyword'},
                          {'count': 1, 'field': 'extractionDate', 'type': 'date'},
                          {'count': 1, 'field': 'name', 'type': 'text'},
                          {'count': 1, 'field': 'type', 'type': 'keyword'}], json_result)

    def test_metadata_field_filter_sum(self):
        self.index_documents([
            {"name": "Antrodiaetidae", "type": "Document", "contentType": "audio/vnd.wave", "_id": "id1"},
            {"name": "Antrodiaetidae", "type": "Document", "contentType": "message/rfc822", "subject": "Hello World", "_id": "id2"},
            {"name": "Antrodiaetidae", "type": "Document", "contentType": "message/rfc822", "subject": "Bye Moon", "_id": "id3"}
        ])
        runner = CliRunner()
        result = runner.invoke(cli, ['list-metadata', 
                                    '--elasticsearch-url', self.elasticsearch_url, 
                                    '--datashare-project', self.datashare_project,
                                    '--query_filter', 'contentType=message/rfc822', 
                                    ])
        json_result = loads(result.output)
        self.assertEqual([{'count': 2, 'field': 'contentType', 'type': 'keyword'},
                          {'count': 2, 'field': 'extractionDate', 'type': 'date'},
                          {'count': 2, 'field': 'name', 'type': 'text'},
                          {'count': 2, 'field': 'subject', 'type': 'text'},
                          {'count': 2, 'field': 'type', 'type': 'keyword'}], json_result)
