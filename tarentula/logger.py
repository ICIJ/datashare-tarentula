import logging
import coloredlogs
from logging.handlers import SysLogHandler

logger = logging.getLogger('tarentula')
logger.setLevel(logging.INFO)

def default_log_formatter():
    return logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')

def add_syslog_handler(address = 'localhost', port = 514, facility = 'local7'):
    sysLogFormatter = default_log_formatter()
    sysLogHandler = SysLogHandler(address = (address, port), facility = facility)
    sysLogHandler.setLevel(logging.INFO)
    sysLogHandler.setFormatter(sysLogFormatter)
    logger.addHandler(sysLogHandler)

def add_stdout_handler(level = logging.ERROR):
    fmt = '%(levelname)s %(message)s'
    coloredlogs.install(level=level, logger=logger, fmt=fmt)
