import logging
import sys


def setup_logger(debug: bool = False) -> logging.Logger:
    """
    Configure and returns a logger instance with a specified logging level and format.

    Args:
        debug (bool): If True, sets the logging level to DEBUG and uses a detailed log format.
                      If False, sets the logging level to INFO and uses a basic log format.

    Returns:
        logging.Logger: A configured logger instance.

    """
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    log_format_debug = "%(asctime)s | %(levelname)s | [%(funcName)s] %(message)s"
    log_format_basic = "%(asctime)s | %(levelname)s | %(message)s"

    formatter = logging.Formatter(
        fmt=log_format_debug if debug else log_format_basic, datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
