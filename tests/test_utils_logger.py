import logging

import pytest

from utils.logger import setup_logging


@pytest.mark.parametrize(
    "debug, expected_level, expected_format",
    [
        (True, logging.DEBUG, "[%(levelname)s] [%(name)s.%(funcName)s] %(message)s"),
        (False, logging.INFO, "[%(levelname)s] %(message)s"),
    ],
)
def test_setup_logging(mocker, debug, expected_level, expected_format):
    mock_basic_config = mocker.patch("logging.basicConfig")
    setup_logging(debug=debug)
    mock_basic_config.assert_called_once_with(level=expected_level, format=expected_format)
