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

    def test_dont_count(self):
        self.index_documents([{"name": "Antrodiaetidae", "type": "Document", "contentType": "audio/vnd.wave",
                               "_id": "id1"}
                              ])
        runner = CliRunner()
        result = runner.invoke(cli, ['list-metadata', 
                                    '--elasticsearch-url', self.elasticsearch_url, 
                                     '--datashare-project', self.datashare_project,
                                     '--not-count'])
        json_result = loads(result.output)
        self.assertGreater(len(json_result), 0)
        self.assertTrue(all(['field' in item for item in json_result]))
        self.assertTrue(all(['type' in item for item in json_result]))
        self.assertTrue(all(['count' not in item for item in json_result]))
        self.assertTrue(any(['name' in item['field'] for item in json_result]))
        self.assertTrue(any(['type' in item['field'] for item in json_result]))
        self.assertTrue(any(['contentType' in item['field'] for item in json_result]))
