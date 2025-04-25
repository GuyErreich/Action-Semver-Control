import logging


def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    format_str = (
        "[%(levelname)s] [%(name)s.%(funcName)s] %(message)s"
        if debug
        else "[%(levelname)s] %(message)s"
    )
    logging.basicConfig(level=level, format=format_str)
