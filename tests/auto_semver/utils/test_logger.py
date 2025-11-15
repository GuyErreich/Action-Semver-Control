"""
Unit tests for the logger module in auto_semver.utils.logger.

This module contains tests for the logger configuration and record factory,
ensuring that log formatting is applied correctly with different debug levels.
"""

import logging
from collections.abc import Generator

import pytest

from auto_semver.utils.logger import record_factory, setup_logger


class TestLogger:
    """Test cases for the logger module."""

    @pytest.fixture
    def reset_logging_factory(self) -> Generator[None, None, None]:
        """Reset the logging record factory after each test."""
        original_factory = logging.getLogRecordFactory()
        yield
        logging.setLogRecordFactory(original_factory)

    @pytest.mark.unit
    def test_record_factory_adds_full_name(self) -> None:
        """Test that record_factory adds the 'full_name' attribute to log records."""
        # Create a mock record
        record_args = [
            "test_logger",  # name
            logging.INFO,  # level
            "file.py",  # pathname
            10,  # lineno
            "Test message",  # msg
            (),  # args
            None,  # exc_info
        ]

        record = record_factory(*record_args)

        # Verify full_name attribute exists and has expected format
        assert hasattr(record, "full_name")
        assert record.full_name == f"[{record.name}.{record.module}][{record.funcName}]"

    @pytest.mark.unit
    def test_setup_logger_debug_mode(self, reset_logging_factory: None) -> None:
        """Test logger setup in debug mode."""
        logger = setup_logger(debug=True)

        # Verify logger level is set to DEBUG
        assert logger.level == logging.DEBUG

        # Verify handler and formatter are properly configured
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.handlers[0].formatter is not None

    @pytest.mark.unit
    def test_setup_logger_info_mode(self, reset_logging_factory: None) -> None:
        """Test logger setup in info mode (non-debug)."""
        logger = setup_logger(debug=False)

        # Verify logger level is set to INFO
        assert logger.level == logging.INFO

        # Verify handler and formatter are properly configured
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.handlers[0].formatter is not None

    @pytest.mark.unit
    def test_logger_output_debug_mode(self, reset_logging_factory: None) -> None:
        """Test that logger outputs messages correctly in debug mode."""
        # Create a logger with a null handler to prevent console output during testing
        logger = setup_logger(debug=True)

        # Replace the handler with a null handler to prevent output
        null_handler = logging.NullHandler()
        logger.handlers.clear()
        logger.addHandler(null_handler)

        # Log a test message - this should work without errors
        test_message = "This is a debug test message"
        logger.debug(test_message)

        # Verify the logger is configured correctly
        assert logger.level == logging.DEBUG

    @pytest.mark.unit
    def test_logger_output_info_mode(self, reset_logging_factory: None) -> None:
        """Test that logger outputs messages correctly in info mode."""
        # Create a logger with a null handler to prevent console output during testing
        logger = setup_logger(debug=False)

        # Replace the handler with a null handler to prevent output
        null_handler = logging.NullHandler()
        logger.handlers.clear()
        logger.addHandler(null_handler)

        # Log a test message - this should work without errors
        test_message = "This is an info test message"
        logger.info(test_message)

        # Verify the logger is configured correctly
        assert logger.level == logging.INFO
