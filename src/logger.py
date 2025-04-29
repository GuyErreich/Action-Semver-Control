import logging
import sys

def setup_logger(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    
    log_format_debug = '%(asctime)s | %(levelname)s | [%(funcName)s] %(message)s'
    log_format_basic = '%(asctime)s | %(levelname)s | %(message)s'

    formatter = logging.Formatter(
        fmt=log_format_debug if debug else log_format_basic,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger