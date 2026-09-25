import os
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

import click
import matplotlib.pyplot as plt

from tarentula.datashare_client import DatashareClient
from tarentula.graph_realtime import GraphRealTime


class TestGraphRealTime(TestCase):
    es_url = os.environ.get('TEST_ELASTICSEARCH_URL', 'http://elasticsearch:9200')
    ds_client = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.ds_client = DatashareClient(elasticsearch_url=cls.es_url)
        cls.ds_client.create_project('test-datashare')
        cls.ds_client.create('test-datashare')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ds_client.delete_project('test-datashare')
        cls.ds_client.delete_index('test-datashare')

    def test_field(self):
        xs = []
        ys = []
        graph = GraphRealTime(query='{"query":{"match_all":{}}}', elasticsearch_url=self.es_url,
                              index='test-datashare', field='hits.total.value', refresh_interval=5,
                              xs_param=xs, ys_param=ys)
        graph.add_point(0)
        self.addCleanup(plt.close, 'all')

        self.assertEqual(ys, [0])

    def test_unknown_field_raises_a_readable_error(self):
        # GraphRealTime cannot be instantiated here: matplotlib 3.9 recurses on Python 3.14
        graph = SimpleNamespace(query={"query": {"match_all": {}}}, field='hits.totals.value',
                                elasticsearch_endpoint=f'{self.es_url}/test-datashare/_search?size=0',
                                xs=[], ys=[], ax=Mock())

        with self.assertRaises(click.BadParameter) as context:
            GraphRealTime.add_point(graph, 0)
        self.assertIn('hits.totals.value', str(context.exception))
