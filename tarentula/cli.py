import click
import logging
from tarentula.logger import add_syslog_handler, add_stdout_handler
from tarentula.tagging import Tagger
from tarentula.download import Download

def validate_loglevel(ctx, param, value):
    try:
        if isinstance(value, str):
            return getattr(logging, value)
        return int(value)
    except (AttributeError, ValueError):
        raise click.BadParameter('must be a valid log level (CRITICAL, ERROR, WARNING, INFO, DEBUG or NOTSET)')

def validate_progressbar(ctx, param, value):
    # If no value given, we activate the progress bar only when the
    # stdout_loglevel value is higher than INFO (20)
    return value if value is not None else ctx.obj['stdout_loglevel'] > 20

@click.group()
@click.pass_context
@click.option('--syslog-address', help='Syslog address', default='localhost')
@click.option('--syslog-port', help='Syslog port', default=514)
@click.option('--syslog-facility', help='Syslog facility', default='local7')
@click.option('--stdout-loglevel', help='Change the default log level for stdout error handler', default='ERROR', callback=validate_loglevel)
def cli(ctx, **options):
    # Configure Syslog handler
    add_syslog_handler(options['syslog_address'], options['syslog_port'], options['syslog_facility'])
    add_stdout_handler(options['stdout_loglevel'])
    # Pass all option to context
    ctx.ensure_object(dict)
    ctx.obj.update(options)

@click.command()
@click.option('--datashare-url', help='Datashare URL', default='http://localhost:8080')
@click.option('--datashare-project', help='Datashare project', default='local-datashare')
@click.option('--throttle', help='Request throttling (in ms)', default=0)
@click.option('--cookies', help='Key/value pair to add a cookie to each request to the API. You can separate semicolons: key1=val1;key2=val2;...')
@click.option('--traceback/--no-traceback', help='Display a traceback in case of error', default=False)
@click.option('--progressbar/--no-progressbar', help='Display a progressbar', default=None, callback=validate_progressbar)
@click.argument('csv-path', type=click.Path(exists=True))
def tagging(**options):
    # Instanciate a Tagger class with all the options
    tagger = Tagger(**options)
    # Proceed to tagging
    tagger.start()

@click.command()
@click.pass_context
@click.option('--datashare-url', help='Datashare URL', default='http://localhost:8080')
@click.option('--datashare-project', help='Datashare project', default='local-datashare')
@click.option('--elasticsearch-url', help='You can additionally pass the Elasticsearch URL in order to use scrolling capabilities of Elasticsearch (useful when dealing with a lot of results)', default=None)
@click.option('--query', help='The query string to filter documents', default='*')
@click.option('--destination-directory', help='Directory documents will be downloaded', default='./tmp')
@click.option('--throttle', help='Request throttling (in ms)', default=0)
@click.option('--cookies', help='Key/value pair to add a cookie to each request to the API. You can separate semicolons: key1=val1;key2=val2;...')
@click.option('--path-format', help='Downloaded document path template', default='{id_2b}/{id_4b}/{id}')
@click.option('--scroll', help='Scroll duration', default=None)
@click.option('--source', help='A commat-separated list of field to include in the downloaded document from the index', default=None)
@click.option('--once/--not-once', help='Download file only once', default=False)
@click.option('--traceback/--no-traceback', help='Display a traceback in case of error', default=False)
@click.option('--progressbar/--no-progressbar', help='Display a progressbar', default=None, callback=validate_progressbar)
@click.option('--raw-file/--no-raw-file', help='Download raw file from Datashare', default=True)
@click.option('--type', help='Type of indexed documents to download', default='Document', type=click.Choice(['Document', 'NamedEntity'], case_sensitive=True))
def download(ctx, **options):
    # Instanciate a Download class with all the options
    download = Download(**options)
    # Proceed to tagging
    download.start()

cli.add_command(tagging)
cli.add_command(download)

if __name__ == '__main__':
    cli()
