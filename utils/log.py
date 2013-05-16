import logging

class NullHandler(logging.Handler): #exists in python 3.1
    def emit(self, record):
        pass

def getlogger():
    logger = logging.getLogger('feedcraft')
    return logger

def error(msg):
    logger = getlogger()
    logger.error(msg)

def debug(msg):
    logger = getlogger()
    logger.debug(msg)

def warn(msg):
    logger = getlogger()
    logger.warn(msg)

def info(msg):
    logger = getlogger()
    logger.info(msg)