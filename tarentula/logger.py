import logging
import sys

from syslog import LOG_LOCAL7
from logging.handlers import SysLogHandler
import coloredlogs

logger = logging.getLogger('tarentula')
logger.setLevel(logging.INFO)


def default_log_formatter() -> logging.Formatter:
    return logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')


def add_syslog_handler(address: str = 'localhost', port: int = 514, facility: int = LOG_LOCAL7) -> None:
    syslog_formatter = default_log_formatter()
    syslog_handler = SysLogHandler(address = (address, port), facility = facility)
    syslog_handler.setLevel(logging.INFO)
    syslog_handler.setFormatter(syslog_formatter)
    logger.addHandler(syslog_handler)


def add_stdout_handler(level: int = logging.ERROR) -> None:
    fmt = '%(levelname)s %(message)s'
    logger.addHandler(logging.StreamHandler(sys.stdout))
    coloredlogs.install(level=level, logger=logger, fmt=fmt, field_styles={ 'levelname': { 'faint': True } })
