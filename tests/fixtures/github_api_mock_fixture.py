"""Fixture to mock GitHub API calls using responses."""

from collections.abc import Generator

import pytest
import responses


@pytest.fixture
def mock_github_api() -> Generator[responses.RequestsMock, None, None]:
    """Activate responses to mock GitHub API calls for all tests."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
