import functools
import json
from datetime import datetime

import click
import matplotlib.pyplot as plt
import requests
from matplotlib import animation


class GraphRealTime:
    def __init__(self, query: str, elasticsearch_url: str, index: str, field: str, refresh_interval: int,
                 xs_param: list = None, ys_param: list = None):
        if query.startswith("@"):
            with open(query[1:]) as f:
                self.query = json.loads(f.read())
        else:
            self.query = json.loads(query)
        self.field = field
        self.elasticsearch_endpoint = '%s/%s/_search?size=0' % (elasticsearch_url, index)
        self.refresh_interval = refresh_interval
        self.xs = [] if xs_param is None else xs_param
        self.ys = [] if xs_param is None else ys_param

        fig = plt.figure()
        self.ani = animation.FuncAnimation(fig, self.add_point, interval=self.refresh_interval * 1000)
        self.ax = fig.add_subplot(1, 1, 1)
        plt.gcf().autofmt_xdate()

    def show_graph(self):
        plt.show()

    def add_point(self, _i):
        result = requests.post(self.elasticsearch_endpoint, json=self.query).json()
        x = datetime.now()
        # call get on result while there are dots in self.field
        y = functools.reduce(dict.get, [result] + self.field.split('.'))

        self.xs.append(x)
        self.ys.append(y)
        self.ax.clear()
        self.ax.plot(self.xs, self.ys)

        plt.xticks(rotation=45, ha='right')
        plt.title("Dynamic Plot of %s" % self.field)
        plt.xlabel("Time")
        plt.ylabel(self.field)


@click.command()
@click.option('--query', help='Give a JSON query to filter documents. It can be a file with @path/to/file. Default to all.', default='{"query":{"match_all":{}}}')
@click.option('--index', help='Elasticsearch index (default local-datashare)', default='local-datashare')
@click.option('--refresh-interval', help='Graph refresh interval in seconds (default 5)', default=5)
@click.option('--field', help='Field indicator to display over time (default hits.total.value)', default='hits.total.value')
@click.option('--elasticsearch-url', help='Elasticsearch URL which is used to perform update by query', default='http://elasticsearch:9200')
def graph(**options) -> None:
    GraphRealTime(**options).show_graph()


if __name__ == '__main__':
    graph()
