import json
import time
from datetime import datetime

import click
import matplotlib.pyplot as plt
import requests
from matplotlib import animation


@click.command()
@click.option('--query', help='Give a JSON query to filter documents. It can be a file with @path/to/file. Default to all.', default='{"query":{"match_all":{}}}')
@click.option('--index', help='Elasticsearch index', default='local-datashare')
@click.option('--refresh-interval', help='Graph refresh interval in seconds', default=5)
@click.option('--field', help='Field indicator to display over time', default='total')
@click.option('--elasticsearch-url', help='Elasticsearch URL which is used to perform update by query', default='http://elasticsearch:9200')
def graph(query: str, elasticsearch_url: str, index: str, field: str, refresh_interval: int):
    if query.startswith("@"):
        with open(query[1:]) as f:
            query_dict = json.loads(f.read())
    else:
        query_dict = json.loads(query)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs = []
    ys = []

    elasticsearch_endpoint = '%s/%s/_search?size=0' % (elasticsearch_url, index)
    ani = animation.FuncAnimation(fig, add_point, fargs=(xs, ys, elasticsearch_endpoint, query_dict, field, ax), interval=refresh_interval*1000)
    plt.gcf().autofmt_xdate()
    plt.show()


def add_point(i, xs, ys, elasticsearch_endpoint, query_dict, field, ax):
    result = requests.post(elasticsearch_endpoint, json=query_dict).json()
    x = datetime.now()
    y = result['hits'][field]

    xs.append(x)
    ys.append(y)
    ax.clear()
    ax.plot(xs, ys)

    plt.xticks(rotation=45, ha='right')
    plt.title("Dynamic Plot of %s" % field)
    plt.xlabel("Time")
    plt.ylabel(field)


if __name__ == '__main__':
    graph()
