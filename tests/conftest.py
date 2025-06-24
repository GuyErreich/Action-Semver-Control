"""
Global fixtures for pytest.

This module contains global fixtures that are available to all test files.
"""

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from tests.fixtures.file_fixture import FileFixture
from tests.fixtures.github_event_fixture import GitHubEventFixture


@pytest.fixture
def github_event(tmp_path: Path, mocker: MockerFixture, fs: FakeFilesystem) -> GitHubEventFixture:
    """
    Create a GitHubEventFixture instance.

    This fixture sets up the GitHub event environment and provides methods
    to customize it for different test scenarios.

    Args:
        tmp_path: Pytest fixture that provides a temporary directory
        mocker: Pytest fixture for mocking
        fs: Fake filesystem for testing

    Returns:
        A GitHubEventFixture instance for further configuration
    """
    return GitHubEventFixture(tmp_path, mocker, fs)


@pytest.fixture
def file_fixture(tmp_path: Path, fs: FakeFilesystem) -> FileFixture:
    """
    Create a FileFixture instance.

    This fixture provides methods to create different types of files with version strings
    for testing version detection, parsing, and updating.

    Args:
        tmp_path: Pytest fixture that provides a temporary directory
        fs: Fake filesystem for testing

    Returns:
        A FileFixture instance for creating test files
    """
    return FileFixture(tmp_path, fs)
