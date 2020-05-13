import click
from tarentula.logger import add_syslog_handler, add_stdout_handler
from tarentula.tagging import Tagger
from tarentula.download import Download

@click.group()
@click.option('--syslog-address', help='Syslog address', default='localhost')
@click.option('--syslog-port', help='Syslog port', default=514)
@click.option('--syslog-facility', help='Syslog facility', default='local7')
def cli(syslog_address, syslog_port, syslog_facility):
    # Configure Syslog handler
    add_syslog_handler(syslog_address, syslog_port, syslog_facility)
    add_stdout_handler()

@click.command()
@click.option('--datashare-url', help='Datashare URL', default='http://localhost:8080')
@click.option('--datashare-project', help='Datashare project', default='local-datashare')
@click.option('--throttle', help='Request throttling (in ms)', default=0)
@click.option('--cookies', help='Key/value pair to add a cookie to each request to the API. You can separate semicolons: key1=val1;key2=val2;...')
@click.argument('csv-path', type=click.Path(exists=True))
def tagging(**options):
    # Instanciate a Tagger class with all the options
    tagger = Tagger(**options)
    # Print out the summary of tagging (number of tags, number of documents)
    tagger.summarize()
    # Proceed to tagging
    tagger.start()

@click.command()
@click.option('--datashare-url', help='Datashare URL', default='http://localhost:8080')
@click.option('--datashare-project', help='Datashare project', default='local-datashare')
@click.option('--elasticsearch-url', help='You can additionally pass the Elasticsearch URL in order to use scrolling capabilities of Elasticsearch (useful when dealing with a lot of results)', default=None)
@click.option('--query', help='The query string to filter documents', default='*')
@click.option('--destination-directory', help='Directory documents will be downloaded', default='./tmp')
@click.option('--throttle', help='Request throttling (in ms)', default=0)
@click.option('--cookies', help='Key/value pair to add a cookie to each request to the API. You can separate semicolons: key1=val1;key2=val2;...')
@click.option('--path-format', help='Downloaded document path template', default='{id_2b}/{id_4b}/{id}')
def download(**options):
    # Instanciate a Download class with all the options
    download = Download(**options)
    # Proceed to tagging
    download.start()

cli.add_command(tagging)
cli.add_command(download)

if __name__ == '__main__':
    cli()
