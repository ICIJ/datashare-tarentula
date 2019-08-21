import sys
import logging
from logging.handlers import SysLogHandler

logger = logging.getLogger('tarentula')
logger.setLevel(logging.DEBUG)

def default_log_formatter():
    return logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')

def add_syslog_handler(address = 'localhost', port = 514, facility = 'local7'):
    sysLogFormatter = default_log_formatter()
    sysLogHandler = SysLogHandler(address = (address, port), facility = facility)
    sysLogHandler.setLevel(logging.DEBUG)
    sysLogHandler.setFormatter(sysLogFormatter)
    logger.addHandler(sysLogHandler)

def add_stdout_handler():
    stdoutFormatter = default_log_formatter()
    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    stdoutHandler.setFormatter(stdoutFormatter)
    logger.addHandler(stdoutHandler)
