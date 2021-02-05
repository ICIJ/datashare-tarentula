import os
from unittest import TestCase

from tarentula.datashare_client import DatashareClient
from tarentula.graph_realtime import GraphRealTime


class TestGraphRealTime(TestCase):
    es_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')
    ds_client = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.ds_client = DatashareClient(elasticsearch_url=cls.es_url)
        cls.ds_client.create('test-datashare')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ds_client.delete_index('test-datashare')

    def test_field(self):
        xs = []
        ys = []
        GraphRealTime(query='{"query":{"match_all":{}}}', elasticsearch_url=self.es_url,
                      index='test-datashare', field='hits.total.value', refresh_interval=5, xs_param=xs, ys_param=ys).add_point(0)

        self.assertEqual(ys, [0])
