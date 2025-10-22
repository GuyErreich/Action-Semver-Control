"""Unit tests for GitHubPRBuilder."""

from auto_semver.config._models._commit_group import Commit, CommitGroup
from auto_semver.pr.github_builder import GitHubPRBuilder, GitHubPRTemplateVariables


def test_build_title() -> None:
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
    builder = GitHubPRBuilder(data=data)
    assert builder.title == "Release 1.2.3"


def test_build_body() -> None:
    """Test building PR body from template."""
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
    builder = GitHubPRBuilder(
        data=data,
        body_template="This PR releases version {{ version }} on {{ date }}.\nCommits: fix: bug, feat: new",
    )
    expected = "This PR releases version 1.2.3 on 2025-10-08.\nCommits: fix: bug, feat: new"
    assert builder.body == expected


def test_build_body_with_commit_groups() -> None:
    """Test building PR body with commit_groups variable."""
    # Create test commit groups
    commit1 = Commit(title="add new feature", body=None)
    commit2 = Commit(title="fix bug", body=None)
    group1 = CommitGroup(title="Features", commits=[commit1], priority=1)
    group2 = CommitGroup(title="Bug Fixes", commits=[commit2], priority=2)
    
    data = GitHubPRTemplateVariables(
        version="1.2.3",
        previous_version="1.2.2",
        commit_groups=[group1, group2],
        breaking_changes=[],
        author="",
        repository="",
        date="2025-10-22",
        branch="",
        base_branch="",
        labels=None,
        groups=[group1, group2],
    )
    
    # Use template similar to config file
    body_template = """## Release {{ version }}
{% for group in commit_groups -%}
### {{ group.title }}
{% for commit in group.commits -%}
- {{ commit.title }}
{% endfor -%}
{% endfor -%}"""
    
    builder = GitHubPRBuilder(data=data, body_template=body_template)
    
    assert "## Release 1.2.3" in builder.body
    assert "### Features" in builder.body
    assert "### Bug Fixes" in builder.body
    assert "- add new feature" in builder.body
    assert "- fix bug" in builder.body


def test_build_labels() -> None:
    """Test building PR labels from template."""
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
    builder = GitHubPRBuilder(data=data, labels_template="release, {{ version }}")
    assert builder.labels == ["release", "1.2.3"]


def test_build_labels_none_template() -> None:
    """Test build_labels returns empty list when labels_template is empty."""
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
    builder = GitHubPRBuilder(data=data, labels_template="")
    assert builder.labels == []
