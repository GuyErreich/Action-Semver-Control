"""Tests for repository scaffolding helpers."""

import pytest

from auto_semver.setup.scaffold import parse_github_remote


@pytest.mark.unit
@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        ("git@github.com:acme/demo.git", ("acme", "demo")),
        ("https://github.com/acme/demo.git", ("acme", "demo")),
        ("https://github.com/acme/demo", ("acme", "demo")),
    ],
)
def test_parse_github_remote(remote: str, expected: tuple[str, str]) -> None:
    """Parse owner and repo from common GitHub remote URL formats."""
    assert parse_github_remote(remote) == expected


@pytest.mark.unit
def test_parse_github_remote_invalid() -> None:
    """Non-GitHub remotes raise ValueError."""
    with pytest.raises(ValueError, match="Could not parse"):
        parse_github_remote("git@gitlab.com:acme/demo.git")
