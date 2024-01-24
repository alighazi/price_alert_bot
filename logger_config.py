import logging,logging.handlers

def get_logger(name = ""):
    # create logger
    logger = logging.getLogger(name)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    th = logging.handlers.TimedRotatingFileHandler(filename="log/debug.log",when="midnight",encoding="utf-8",backupCount=90)
    th.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    th.setFormatter(formatter)
    logger.addHandler(th)

    rh = logging.handlers.RotatingFileHandler(filename="log/error.log",maxBytes=1024*1024, backupCount=30, encoding="utf-8")
    rh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    rh.setFormatter(formatter)
    logger.addHandler(rh)
    return logger

global instance
instance = get_logger(__name__)
instance.debug("logger instance created")
