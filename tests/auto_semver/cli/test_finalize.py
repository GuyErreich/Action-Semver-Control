"""
Unit tests for the finalize module in auto_semver.cli.finalize.

This module contains tests for the run function in the finalize module,
which handles creating and pushing Git tags for finalized releases.
"""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from auto_semver.cli.finalize import run
from auto_semver.config import Config
from auto_semver.config.data import ConfigData
from auto_semver.gh.event import GitHubEvent
from auto_semver.git import GitOps
from auto_semver.semver import Version
from auto_semver.semver.lock import SemverLock


class TestFinalize:
    """Test cases for the finalize.run function."""

    @pytest.fixture
    def mock_gitops(self, mocker: MockerFixture) -> Any:
        """Create a mock GitOps object."""
        mock = mocker.Mock(spec=GitOps)
        # Set default behaviors
        mock.tag.return_value = "v1.0.0"
        return mock

    @pytest.fixture
    def mock_event(self, github_event: Any, mocker: MockerFixture) -> Any:
        """Create a GitHubEvent object for finalization tests."""
        # Use the github_event.for_finalize() method for a finalization-specific configuration
        github_event.for_finalize()
        # Create and return the GitHubEvent instance
        event = mocker.Mock(spec=GitHubEvent)
        # Set up necessary methods that are used in finalize.py
        event.get_target_branch_name.return_value = "main"  # Default to main branch
        return event

    @pytest.fixture
    def mock_config(self, mocker: MockerFixture) -> Any:
        """Create a mock Config object."""
        mock = mocker.Mock(spec=Config)
        mock_data = mocker.Mock(spec=ConfigData)
        mock.data = mock_data

        # Set default behavior
        mock.data.suffixes = {"main": "", "develop": "-dev"}
        return mock

    @pytest.fixture
    def mock_semver_lock(self, mocker: MockerFixture) -> Any:
        """Create a mock SemverLock."""
        mock = mocker.Mock(spec=SemverLock)
        mock.version = Version.parse("1.0.0")
        # Mock the class method
        mocker.patch.object(SemverLock, "load_from_file", return_value=mock)
        return mock

    @pytest.mark.unit
    def test_finalize_tags_and_pushes(
        self,
        mock_gitops: Any,
        mock_event: Any,
        mock_config: Any,
        mock_semver_lock: Any,
    ) -> None:
        """Test that finalize creates and pushes a tag when target branch is valid."""
        # Run the finalize function
        run(gitops=mock_gitops, event=mock_event, config=mock_config)

        # Verify version was loaded from lock file
        # The SemverLock.load_from_file method was mocked and called

        # Verify tag was created with the correct version
        mock_gitops.tag.assert_called_once_with(tag="1.0.0", branch="main")

        # Verify tag was pushed
        mock_gitops.push.assert_called_once_with(branch_name="v1.0.0")

    @pytest.mark.unit
    def test_finalize_fails_with_invalid_target_branch(
        self,
        mock_gitops: Any,
        mock_event: Any,
        mock_config: Any,
        mock_semver_lock: Any,
    ) -> None:
        """Test that finalize raises error when target branch is not allowed."""
        # Set target branch to something not in allowed targets
        mock_event.get_target_branch_name.return_value = "feature"

        # Run the finalize function and expect ValueError
        with pytest.raises(ValueError, match=r"Tagging not allowed on branch 'feature'"):
            run(gitops=mock_gitops, event=mock_event, config=mock_config)

        # Verify version was loaded from lock file
        # The SemverLock.load_from_file method was mocked and called

        # Verify tag was NOT created
        mock_gitops.tag.assert_not_called()

        # Verify tag was NOT pushed
        mock_gitops.push.assert_not_called()

    @pytest.mark.unit
    def test_finalize_with_develop_branch(
        self,
        mock_gitops: Any,
        mock_event: Any,
        mock_config: Any,
        mock_semver_lock: Any,
    ) -> None:
        """Test finalize works with a non-main branch that is allowed."""
        # Set target branch to develop (which is allowed)
        mock_event.get_target_branch_name.return_value = "develop"

        # Run the finalize function
        run(gitops=mock_gitops, event=mock_event, config=mock_config)

        # Verify tag was created with the correct version
        mock_gitops.tag.assert_called_once_with(tag="1.0.0", branch="develop")

        # Verify tag was pushed
        mock_gitops.push.assert_called_once_with(branch_name="v1.0.0")
