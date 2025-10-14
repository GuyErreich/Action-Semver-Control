"""Unit tests for GitHubPRBuilder."""

import pytest

from auto_semver.pr.github_builder import GitHubPRBuilder, GitHubPRTemplateVariables


@pytest.fixture
def builder() -> GitHubPRBuilder:
    """Create a GitHubPRBuilder instance for testing."""
    return GitHubPRBuilder()


def test_build_title(builder: GitHubPRBuilder) -> None:
    """Test building PR title from template."""
    data = GitHubPRTemplateVariables(
        version="1.2.3",
        previous_version="1.2.2",
        commit_groups=[],
        breaking_changes=[],
        author="",
        repository="",
        date="",
        branch="",
        base_branch="",
        labels=None,
        groups=None,
    )
    assert builder.build_title(data) == "Release 1.2.3"


def test_build_body(builder: GitHubPRBuilder) -> None:
    """Test building PR body from template."""
    builder.body_template = (
        "This PR releases version {{ version }} on {{ date }}.\nCommits: fix: bug, feat: new"
    )
    data = GitHubPRTemplateVariables(
        version="1.2.3",
        previous_version="1.2.2",
        commit_groups=[],
        breaking_changes=[],
        author="",
        repository="",
        date="2025-10-08",
        branch="",
        base_branch="",
        labels=None,
        groups=None,
    )
    expected = "This PR releases version 1.2.3 on 2025-10-08.\nCommits: fix: bug, feat: new"
    assert builder.build_body(data) == expected


def test_build_labels(builder: GitHubPRBuilder) -> None:
    """Test building PR labels from template."""
    builder.labels_template = "release, {{ version }}"
    data = GitHubPRTemplateVariables(
        version="1.2.3",
        previous_version="1.2.2",
        commit_groups=[],
        breaking_changes=[],
        author="",
        repository="",
        date="",
        branch="",
        base_branch="",
        labels=None,
        groups=None,
    )
    assert builder.build_labels(data) == ["release", "1.2.3"]


def test_build_labels_none_template() -> None:
    """Test build_labels returns empty list when labels_template is None."""
    builder = GitHubPRBuilder()
    builder.title_template = "Release {{ version }}"
    builder.body_template = "Release notes"
    data = GitHubPRTemplateVariables(
        version="1.2.3",
        previous_version="1.2.2",
        commit_groups=[],
        breaking_changes=[],
        author="",
        repository="",
        date="",
        branch="",
        base_branch="",
        labels=None,
        groups=None,
    )
    assert builder.build_labels(data) == []
