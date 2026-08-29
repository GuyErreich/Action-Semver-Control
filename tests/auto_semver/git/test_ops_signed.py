"""Tests for verified (API-backed) GitOps commits."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from auto_semver.git.ops import GitOps


class TestSignedGitOps:
    """Verify API-backed commit/merge/tag paths."""

    @pytest.fixture
    def mock_repo(self, mocker: MockerFixture) -> Any:
        """Provide a minimal GitPython repo double."""
        mock = mocker.MagicMock()
        mock.git = mocker.MagicMock()
        mock.git.diff.return_value = "pyproject.toml\n"
        mock.active_branch.name = "release/1.0.0-dev"
        mock.working_tree_dir = "/github/workspace"
        mock_remote = mocker.MagicMock()
        mock_remote.url = "git@github.com:owner/repo.git"
        mock.remote.return_value = mock_remote
        return mock

    @pytest.fixture(autouse=True)
    def patch_repo(self, mocker: MockerFixture, mock_repo: Any) -> None:
        """Patch Repo construction for every signed GitOps test."""
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch(
            "auto_semver.git.ops.GitOps._parse_repository_name",
            return_value="owner/repo",
        )

    @pytest.mark.unit
    def test_signed_commits_requires_token(self) -> None:
        """Reject signed mode without a GitHub token."""
        with pytest.raises(ValueError, match="github_token is required"):
            GitOps(signed_commits=True)

    @pytest.mark.unit
    def test_api_commit_uses_github_api(
        self, mocker: MockerFixture, mock_repo: Any, tmp_path: Any
    ) -> None:
        """Signed commit should call the Git Data API and update the branch ref."""
        mock_repo.working_tree_dir = str(tmp_path)
        file_path = tmp_path / "pyproject.toml"
        file_path.write_text('version = "1.0.0"\n', encoding="utf-8")

        mock_gh_repo = mocker.MagicMock()
        mock_ref = mocker.MagicMock()
        mock_ref.object.sha = "abc123"
        mock_gh_repo.get_git_ref.return_value = mock_ref
        mock_tree = mocker.MagicMock()
        mock_commit = mocker.MagicMock()
        mock_commit.sha = "def456"
        mock_commit.tree = mock_tree
        mock_gh_repo.get_git_commit.return_value = mock_commit
        mock_blob = mocker.MagicMock()
        mock_blob.sha = "blobsha"
        mock_gh_repo.create_git_blob.return_value = mock_blob
        mock_new_tree = mocker.MagicMock()
        mock_gh_repo.create_git_tree.return_value = mock_new_tree
        mock_new_commit = mocker.MagicMock()
        mock_new_commit.sha = "commitsha"
        mock_gh_repo.create_git_commit.return_value = mock_new_commit

        gitops = GitOps(signed_commits=True, github_token="token")
        mocker.patch.object(gitops, "_gh_repo", return_value=mock_gh_repo)
        mocker.patch.object(gitops, "fetch")

        gitops.commit("Release 1.0.0-dev", force=True)

        mock_gh_repo.create_git_commit.assert_called_once()
        mock_ref.edit.assert_called_once_with(sha="commitsha", force=True)

    @pytest.mark.unit
    def test_api_merge_promotion(self, mocker: MockerFixture, mock_repo: Any) -> None:
        """Signed auto-promote should merge and tag via the GitHub API."""
        gitops = GitOps(signed_commits=True, github_token="token")
        mock_merge = mocker.patch.object(
            gitops,
            "_api_merge",
            return_value="merge-sha",
        )
        mock_tag = mocker.patch.object(
            gitops,
            "_api_create_lightweight_tag",
            return_value="1.0.0-rc",
        )
        mocker.patch.object(gitops, "fetch")

        result = gitops._auto_promote_api(
            source_branch="dev",
            target_branch="staging",
            version="1.0.0-rc",
            source_version="1.0.0-dev",
            merge_message="chore: promote",
            is_source_tag=False,
            post_merge_hook=None,
        )

        assert result == "1.0.0-rc"
        mock_merge.assert_called_once_with(
            base="staging", head="dev", message="chore: promote"
        )
        mock_tag.assert_called_once_with(tag="1.0.0-rc", sha="merge-sha")
