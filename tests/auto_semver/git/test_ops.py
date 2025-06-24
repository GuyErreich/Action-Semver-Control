"""
Unit tests for the GitOps class in auto_semver.git.ops module.

This module tests the functionality of the GitOps class which handles Git operations
such as branch creation, commit, push, tag, PR creation, and related operations.
"""

from pathlib import Path
from typing import Any

import pytest
from git import Repo
from pytest_mock import MockerFixture

from auto_semver.git.ops import GitOps
from auto_semver.semver import Version


class TestGitOps:
    """Test cases for the GitOps class."""

    @pytest.fixture
    def mock_repo(self, mocker: MockerFixture) -> Any:
        """Create a mock Git repository."""
        mock = mocker.MagicMock(spec=Repo)
        mock.git = mocker.MagicMock()
        return mock

    @pytest.fixture
    def mock_config_writer(self, mocker: MockerFixture, mock_repo: Any) -> Any:
        """Create a mock Git config writer."""
        mock = mocker.MagicMock()
        mock.get_values.return_value = []
        mock_repo.config_writer.return_value = mock
        return mock

    @pytest.fixture
    def mock_github_repo(self, mocker: MockerFixture) -> Any:
        """Create a mock GitHub repository."""
        return mocker.MagicMock()

    @pytest.fixture
    def mock_github(self, mocker: MockerFixture, mock_github_repo: Any) -> Any:
        """Create a mock GitHub API client."""
        mock = mocker.MagicMock()
        mock.get_repo.return_value = mock_github_repo
        return mock

    @pytest.fixture(autouse=True)
    def patch_github(self, mocker: MockerFixture, mock_github: Any) -> Any:
        """Patch the Github class."""
        return mocker.patch("auto_semver.git.ops.Github", return_value=mock_github)

    @pytest.mark.unit
    def test_init_with_ensure_safe(self, mocker: MockerFixture, mock_repo: Any) -> None:
        """Test that initializing with ensure_safe=True calls __ensure_git_safe_directory."""
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Setup the repo working directory path
        mock_repo.working_tree_dir = "/mock/path"

        # Create GitOps instance with ensure_safe=True
        GitOps(ensure_safe=True)

        # Check that config_writer was called
        mock_repo.config_writer.assert_called_once_with(config_level="global")

        # Check that the safe directory was added
        config_writer = mock_repo.config_writer.return_value
        config_writer.set_value.assert_called_once_with(
            section="safe", option="directory", value="/mock/path"
        )

    @pytest.mark.unit
    def test_create_branch(self, mocker: MockerFixture) -> None:
        """Test creating a branch with the create_branch method."""
        # Create mocks
        mock_repo = mocker.MagicMock()
        mock_head = mocker.MagicMock()
        mock_repo.create_head.return_value = mock_head

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call create_branch
        gitops = GitOps()
        gitops.create_branch(branch_name="test-branch")

        # Check that create_head and checkout were called correctly
        mock_repo.create_head.assert_called_once_with(path="test-branch")
        mock_head.checkout.assert_called_once()

    @pytest.mark.unit
    def test_create_branch_with_force(self, mocker: MockerFixture) -> None:
        """Test creating a branch with force=True."""
        # Create mocks
        mock_repo = mocker.MagicMock()
        mock_head = mocker.MagicMock()
        mock_existing_branch = mocker.MagicMock()
        mock_repo.create_head.return_value = mock_head

        # Setup branch exists and mock the existing branch
        mock_repo.heads.__contains__.return_value = True
        mock_repo.heads.__getitem__.return_value = mock_existing_branch

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call create_branch with force=True
        gitops = GitOps()
        gitops.create_branch(branch_name="test-branch", force=True)

        # Check that the existing branch was deleted with force=True
        mock_existing_branch.delete.assert_called_once_with(repo=mock_repo, force=True)

        # Verify branch was created
        mock_repo.create_head.assert_called_once_with(path="test-branch")
        mock_head.checkout.assert_called_once()

    @pytest.mark.unit
    def test_add(self, mocker: MockerFixture) -> None:
        """Test adding files with the add method."""
        # Create mock repo
        mock_repo = mocker.MagicMock()
        # Mock the index to prevent 'add' from actually checking file existence
        mock_repo.index = mocker.MagicMock()
        # Mock is_dirty to return True (files need to be added)
        mock_repo.is_dirty.return_value = True

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call add with file paths
        gitops = GitOps()
        files_list = ["file1.txt", Path("file2.txt")]  # List with mix of str and Path

        gitops.add(files=files_list)  # type: ignore

        # Check that index.add was called for each file
        assert mock_repo.index.add.call_count == 2
        # Check the first call (these should be the stringified versions of the paths)
        mock_repo.index.add.assert_any_call(items=["file1.txt"])
        mock_repo.index.add.assert_any_call(items=["file2.txt"])

    @pytest.mark.unit
    def test_commit(self, mocker: MockerFixture) -> None:
        """Test committing changes with the commit method."""
        # Create mock repo
        mock_repo = mocker.MagicMock()
        # Mock index.diff() to return some changes
        mock_repo.index.diff.return_value = ["some_change"]

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call commit
        gitops = GitOps()
        message = "Test commit message"
        gitops.commit(message=message)

        # Check that index.commit was called with the message
        mock_repo.index.commit.assert_called_once_with(message=message)

    @pytest.mark.unit
    def test_push(self, mocker: MockerFixture) -> None:
        """Test pushing changes with the push method."""
        # Create mock repo and remote
        mock_repo = mocker.MagicMock()
        mock_remote = mocker.MagicMock()
        mock_repo.remote.return_value = mock_remote

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call push
        gitops = GitOps()
        gitops.push(branch_name="test-branch")

        # Check that remote and push were called correctly
        mock_repo.remote.assert_called_once_with(name="origin")
        mock_remote.push.assert_called_once_with(refspec="test-branch", force=False)

    @pytest.mark.unit
    def test_tag(self, mocker: MockerFixture) -> None:
        """Test tagging with the tag method."""
        # Create mock repo and tag
        mock_repo = mocker.MagicMock()
        mock_tag = mocker.MagicMock()
        mock_tag.name = "v1.0.0"
        mock_repo.create_tag.return_value = mock_tag

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance and call tag
        gitops = GitOps()
        tag_name = gitops.tag(tag="v1.0.0", branch="main")

        # Check that create_tag was called correctly
        mock_repo.create_tag.assert_called_once_with(path="v1.0.0", ref="main", message="")
        assert tag_name == "v1.0.0"

    @pytest.mark.unit
    def test_create_pr_success(self, mocker: MockerFixture, mock_github_repo: Any) -> None:
        """Test creating a pull request with create_pr method."""
        # Set up the PR mock
        mock_pr = mocker.MagicMock()
        mock_pr.number = 123
        mock_github_repo.create_pull.return_value = mock_pr
        mock_github_repo.get_pulls.return_value = []

        # Patch the Github class (already done in patch_github fixture)

        # Create GitOps instance
        gitops = GitOps()

        # Call create_pr
        pr_number = gitops.create_pr(
            github_token="token",
            repo_full_name="owner/repo",
            title="Test PR",
            body="Test body",
            source="feature-branch",
            target="main",
            labels=["label1", "label2"],
        )

        # Check results
        assert pr_number == 123
        mock_github_repo.create_pull.assert_called_once_with(
            title="Test PR", body="Test body", head="feature-branch", base="main"
        )
        mock_pr.add_to_labels.assert_called_once_with("label1", "label2")

    @pytest.mark.unit
    def test_create_pr_existing(self, mocker: MockerFixture, mock_github_repo: Any) -> None:
        """Test create_pr when a PR already exists."""
        # Set up the existing PR mock
        mock_existing_pr = mocker.MagicMock()
        mock_existing_pr.number = 123
        mock_existing_pr.head.ref = "feature-branch"
        mock_existing_pr.base.ref = "main"
        mock_github_repo.get_pulls.return_value = [mock_existing_pr]

        # Create GitOps instance
        gitops = GitOps()

        # Call create_pr
        pr_number = gitops.create_pr(
            github_token="token",
            repo_full_name="owner/repo",
            title="Test PR",
            body="Test body",
            source="feature-branch",
            target="main",
        )

        # Check results
        assert pr_number == 123
        mock_github_repo.create_pull.assert_not_called()  # Should not create a new PR

    @pytest.mark.unit
    def test_close_old_release_prs(self, mocker: MockerFixture, mock_github_repo: Any) -> None:
        """Test closing old release PRs with close_old_release_prs method."""
        # Set up mock PRs
        mock_pr1 = mocker.MagicMock()
        mock_pr1.number = 1
        mock_pr1.head.ref = "release/v1.0.0"
        mock_pr1.base.ref = "main"

        # Create label object with name attribute
        mock_label = mocker.MagicMock()
        mock_label.name = "semver-bump"
        mock_pr1.labels = [mock_label]

        mock_pr2 = mocker.MagicMock()
        mock_pr2.number = 2
        mock_pr2.head.ref = "feature/something"  # Should be skipped
        mock_pr2.base.ref = "main"
        mock_pr2.labels = []

        mock_github_repo.get_pulls.return_value = [mock_pr1, mock_pr2]

        # Create GitOps instance
        gitops = GitOps()

        # Call close_old_release_prs
        gitops.close_old_release_prs(
            github_token="token",
            repo_full_name="owner/repo",
            target_branch="main",
            labels=["semver-bump"],
        )

        # Check that the correct PR was closed
        mock_pr1.edit.assert_called_once_with(state="closed")
        mock_pr2.edit.assert_not_called()

    @pytest.mark.unit
    def test_get_recent_commits(self, mocker: MockerFixture) -> None:
        """Test getting recent commits with get_recent_commits method."""
        # Create mock repo and commits
        mock_repo = mocker.MagicMock()
        mock_commit1 = mocker.MagicMock()
        mock_commit1.message = "Commit 1"
        mock_commit2 = mocker.MagicMock()
        mock_commit2.message = "Commit 2"
        mock_repo.iter_commits.return_value = [mock_commit2, mock_commit1]  # In reverse order

        # Patch the Repo constructor
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

        # Create GitOps instance
        gitops = GitOps()

        # Call get_recent_commits
        commits = gitops.get_recent_commits(commit_sha="abc123")

        # Check results
        assert commits == ["Commit 1", "Commit 2"]  # Should be in correct order
        mock_repo.git.rev_parse.assert_called_once_with("abc123")
        mock_repo.iter_commits.assert_called_once_with("abc123..HEAD")

    @pytest.mark.unit
    def test_get_highest_release_lock_version_for_target(self, mocker: MockerFixture) -> None:
        """Test getting the highest release lock version with get_highest_release_lock_version_for_target."""
        # Create mock repo and remote
        mock_repo = mocker.MagicMock()
        mock_remote = mocker.MagicMock()
        mock_repo.remote.return_value = mock_remote

        # Create mock refs
        mock_ref1 = mocker.MagicMock()
        mock_ref1.name = "origin/release/v1.0.0"
        mock_ref2 = mocker.MagicMock()
        mock_ref2.name = "origin/release/v1.1.0"
        mock_ref3 = mocker.MagicMock()
        mock_ref3.name = "origin/develop"  # Should be skipped
        mock_remote.refs = [mock_ref1, mock_ref2, mock_ref3]

        # Set up mock lock files - must include all required fields
        lock1 = {"version": "1.0.0", "target_branch": "main", "source_branch": "develop"}
        lock2 = {"version": "1.1.0", "target_branch": "main", "source_branch": "develop"}

        # Patch functions
        mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)
        mocker.patch("auto_semver.git.ops.yaml.safe_load", side_effect=[lock1, lock2])
        # Create a mock Version object to return in SemverLock
        mock_version = mocker.MagicMock(spec=Version)
        mock_version.__str__.return_value = "1.1.0"

        # Mock SemverLock creation
        mocker.patch(
            "auto_semver.git.ops.SemverLock.from_dict",
            side_effect=lambda x: mocker.MagicMock(
                version=mock_version, target_branch=x["target_branch"]
            ),
        )

        # Set up show behavior for lock files
        def mock_show(path: str) -> str:
            if "v1.0.0" in path:
                return "v1.0.0 lock"
            if "v1.1.0" in path:
                return "v1.1.0 lock"
            raise Exception("Not found")

        mock_repo.git.show.side_effect = mock_show

        # Create GitOps instance
        gitops = GitOps()

        # Call get_highest_release_lock_version_for_target
        highest_version = gitops.get_highest_release_lock_version_for_target(target_branch="main")

        # Check results - should have a Version object now
        assert highest_version is not None
        assert isinstance(highest_version, Version)
        mock_remote.fetch.assert_called_once_with(prune=True)
