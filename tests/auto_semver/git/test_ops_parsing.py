"""Tests for GitOps parsing functionality."""

import pytest
from git import Repo
from pytest_mock import MockerFixture

from auto_semver.git.ops import GitOps


class TestGitOpsParsing:
    """Test cases for repository parsing in GitOps class."""

    def test_parse_repository_name_ssh(self, mocker: MockerFixture) -> None:
        """Test parsing of SSH repository URL."""
        mock_repo = mocker.MagicMock(spec=Repo)
        mock_remote = mocker.MagicMock()
        mock_remote.url = "git@github.com:owner/repo.git"
        mock_repo.remote.return_value = mock_remote
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # We need to ensure we don't init the full object which might do other things,
        # but _parse_repository_name is called in __init__.
        # So we can just init GitOps.

        # We also need to mock Github auth probably if it happens in init
        mocker.patch("auto_semver.git.ops.Github")

        ops = GitOps()
        assert ops._repo_full_name == "owner/repo"

    def test_parse_repository_name_https(self, mocker: MockerFixture) -> None:
        """Test parsing of HTTPS repository URL."""
        mock_repo = mocker.MagicMock(spec=Repo)
        mock_remote = mocker.MagicMock()
        mock_remote.url = "https://github.com/owner/repo.git"
        mock_repo.remote.return_value = mock_remote
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch("auto_semver.git.ops.Github")

        ops = GitOps()
        assert ops._repo_full_name == "owner/repo"

    def test_parse_repository_name_https_with_token(self, mocker: MockerFixture) -> None:
        """Test parsing of HTTPS repository URL with token."""
        mock_repo = mocker.MagicMock(spec=Repo)
        mock_remote = mocker.MagicMock()
        mock_remote.url = "https://x-access-token:token@github.com/owner/repo.git"
        mock_repo.remote.return_value = mock_remote
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch("auto_semver.git.ops.Github")

        ops = GitOps()
        assert ops._repo_full_name == "owner/repo"

    def test_parse_repository_name_https_with_user_pass(self, mocker: MockerFixture) -> None:
        """Test parsing of HTTPS repository URL with username and password."""
        mock_repo = mocker.MagicMock(spec=Repo)
        mock_remote = mocker.MagicMock()
        mock_remote.url = "https://user:password@github.com/owner/repo.git"
        mock_repo.remote.return_value = mock_remote
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch("auto_semver.git.ops.Github")

        ops = GitOps()
        assert ops._repo_full_name == "owner/repo"

    def test_parse_repository_name_failure(self, mocker: MockerFixture) -> None:
        """Test parsing failure for non-GitHub URL."""
        mock_repo = mocker.MagicMock(spec=Repo)
        mock_remote = mocker.MagicMock()
        mock_remote.url = "https://gitlab.com/owner/repo.git"
        mock_repo.remote.return_value = mock_remote
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch("auto_semver.git.ops.Github")

        with pytest.raises(ValueError, match="Unable to parse GitHub repository"):
            GitOps()
