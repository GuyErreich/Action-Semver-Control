"""
Logger configuration module.

This module provides a function to set up a logger with a specified logging level and format.
It allows for easy debugging and tracking of events in the application.
The logger can be configured to display detailed debug information or a more concise info format.

Typical use case::
    logger = setup_logger(debug=True)
    logger.info("This is an info message.")
    logger.debug("This is a debug message.")
"""

import logging
import sys
from logging import LogRecord
from typing import Any

old_factory = logging.getLogRecordFactory()


def record_factory(*args: Any, **kwargs: dict[str, Any]) -> LogRecord:
    """
    Create a custom log record with additional formatting.

    This factory function enhances the default log record by adding a 'full_name'
    attribute that combines the logger name, module, and function name for more
    detailed logging output.

    Args:
        *args: Variable length argument list passed to the original log record factory.
        **kwargs: Arbitrary keyword arguments passed to the original log record factory.

    Returns:
        LogRecord: A log record with the additional 'full_name' attribute.

    """

    record = old_factory(*args, **kwargs)
    record.full_name = f"[{record.name}.{record.module}][{record.funcName}]"
    return record


logging.setLogRecordFactory(record_factory)


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

    # log_format_debug = "%(asctime)s | %(levelname)-5s | [%(name)s.%(funcName)s] %()-5s | %(message)s"
    log_format_debug = "{asctime} | {levelname:^7} | {full_name:>59} | {message}"
    log_format_basic = "{asctime} | {levelname:^7} | {message}"

    formatter = logging.Formatter(
        fmt=log_format_debug if debug else log_format_basic, datefmt="%Y-%m-%d %H:%M:%S", style="{"
    )

    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger
