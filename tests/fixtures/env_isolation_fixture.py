"""Fixture to isolate environment variables for tests."""

from collections.abc import Generator

import pytest


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Isolate environment variables for tests."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("CI", "true")
    yield
    # No cleanup needed
