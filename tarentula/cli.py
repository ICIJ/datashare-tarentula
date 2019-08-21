import click
from tarentula.logger import add_syslog_handler, add_stdout_handler
from tarentula.tagging import Tagger

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
@click.argument('csv-path', type=click.Path(exists=True))
def tagging(**options):
    # Instanciate a Tagger class with all the open and
    tagger = Tagger(**options)
    # Print out the summary of tagging (number of tags, number of documents)
    tagger.summarize()
    # Proceed to tagging
    tagger.start()

cli.add_command(tagging)
