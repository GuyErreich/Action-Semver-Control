"""Extended GitOps tests for release branch lifecycle."""

import pytest
from git import GitCommandError
from pytest_mock import MockerFixture

from auto_semver.config.constants import PR_HIDDEN_MARKER
from auto_semver.git.ops import GitOps
from auto_semver.semver import Version
from auto_semver.semver.lock import SemverLock


@pytest.mark.unit
def test_get_open_release_version_returns_highest(mocker: MockerFixture) -> None:
    """Pick the highest semver among open owned release PRs."""
    gitops = GitOps()
    mocker.patch.object(gitops, "get_repository_name", return_value="owner/repo")

    mock_pr_low = mocker.MagicMock()
    mock_pr_low.base.ref = "dev"
    mock_pr_low.head.ref = "auto-semver/release/1.3.0-dev"
    mock_pr_low.labels = [mocker.MagicMock(name="semver-bump")]
    mock_pr_low.labels[0].name = "semver-bump"
    mock_pr_low.body = PR_HIDDEN_MARKER

    mock_pr_high = mocker.MagicMock()
    mock_pr_high.base.ref = "dev"
    mock_pr_high.head.ref = "auto-semver/release/1.4.0-dev"
    mock_pr_high.labels = mock_pr_low.labels
    mock_pr_high.body = PR_HIDDEN_MARKER

    mock_repo = mocker.MagicMock()
    mock_repo.get_pulls.return_value = [mock_pr_low, mock_pr_high]
    mocker.patch("auto_semver.git.ops.Github").return_value.get_repo.return_value = mock_repo

    def lock_side_effect(ref: str) -> SemverLock | None:
        version_str = ref.split("/")[-1]
        return SemverLock(
            version=Version.parse(version_str),
            source_branch="feature/x",
            target_branch="dev",
        )

    mocker.patch.object(gitops, "get_lock_at_ref", side_effect=lock_side_effect)

    result = gitops.get_open_release_version(
        github_token="token",
        target_branch="dev",
        branch_prefix="auto-semver/release/",
        labels=["semver-bump"],
    )

    assert result is not None
    assert str(result) == "1.4.0-dev"


@pytest.mark.unit
def test_get_merged_source_branches_since(mocker: MockerFixture) -> None:
    """Collect merged PR branch names after base_sha."""
    mock_repo = mocker.MagicMock()
    mock_repo.remote.return_value.url = "git@github.com:owner/repo.git"
    mock_repo.git.merge_base.return_value = "ok"
    mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
    gitops = GitOps()
    mocker.patch.object(gitops, "get_repository_name", return_value="owner/repo")

    mock_pr = mocker.MagicMock()
    mock_pr.merged = True
    mock_pr.merge_commit_sha = "sha1"
    mock_pr.head.ref = "feature/one"

    gh_repo = mocker.MagicMock()
    gh_repo.get_pulls.return_value = [mock_pr]
    mocker.patch("auto_semver.git.ops.Github").return_value.get_repo.return_value = gh_repo

    branches = gitops.get_merged_source_branches_since(
        base_sha="base",
        target_branch="dev",
        github_token="token",
    )

    assert branches == ["feature/one"]


@pytest.mark.unit
def test_get_merged_source_branches_skips_non_ancestor(mocker: MockerFixture) -> None:
    """PRs not descended from base_sha are excluded."""
    mock_repo = mocker.MagicMock()
    mock_repo.remote.return_value.url = "git@github.com:owner/repo.git"
    mock_repo.git.merge_base.side_effect = GitCommandError("merge-base", "not ancestor")
    mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
    gitops = GitOps()
    mocker.patch.object(gitops, "get_repository_name", return_value="owner/repo")

    mock_pr = mocker.MagicMock()
    mock_pr.merged = True
    mock_pr.merge_commit_sha = "sha1"
    mock_pr.head.ref = "feature/old"

    gh_repo = mocker.MagicMock()
    gh_repo.get_pulls.return_value = [mock_pr]
    mocker.patch("auto_semver.git.ops.Github").return_value.get_repo.return_value = gh_repo

    branches = gitops.get_merged_source_branches_since(
        base_sha="base",
        target_branch="dev",
        github_token="token",
    )

    assert branches == []


@pytest.mark.unit
def test_branch_matches_prefix() -> None:
    """Release branch prefix regex accepts semver suffixes."""
    assert GitOps._branch_matches_prefix("auto-semver/release/1.4.0-dev", "auto-semver/release/")
    assert not GitOps._branch_matches_prefix("release/manual-hotfix", "auto-semver/release/")
