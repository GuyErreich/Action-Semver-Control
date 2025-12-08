"""Tests for promote CLI command."""

from unittest.mock import MagicMock, patch

import pytest

from auto_semver.cli.promote import run
from auto_semver.config import Config, PromotionRule
from auto_semver.git import GitOps
from auto_semver.semver import Version


class TestPromoteCLI:
    """Tests for the promote CLI command."""

    @patch("auto_semver.git.GitOps.get_lock_version_from_branch")
    @patch("auto_semver.git.GitOps.create_pr")
    def test_successful_promotion(
        self, mock_create_pr: MagicMock, mock_get_version: MagicMock
    ) -> None:
        """Test successful promotion PR creation."""
        # Setup mocks
        mock_rule = PromotionRule(from_branch="dev", to_branch="staging", auto_promote=True)
        mock_get_version.return_value = Version.parse("1.2.3-dev")

        # Create mock objects
        gitops = MagicMock(spec=GitOps)
        gitops.get_lock_version_from_branch = mock_get_version
        gitops.create_pr = mock_create_pr

        # Mock the config with proper data attribute
        config = MagicMock(spec=Config)
        mock_data = MagicMock()
        mock_data.validate_promotion.return_value = mock_rule
        config.data = mock_data

        # Run the function
        run(
            gitops=gitops,
            config=config,
            github_token="test-token",
            from_branch="dev",
            to_branch="staging",
        )

        # Verify calls
        config.data.validate_promotion.assert_called_once_with(
            from_branch="dev", to_branch="staging", require_auto_promote=False
        )
        mock_get_version.assert_called_once_with(branch_name="dev")
        mock_create_pr.assert_called_once()

        # Check PR creation parameters (repo_full_name is no longer a parameter)
        call_args = mock_create_pr.call_args
        assert call_args[1]["source"] == "dev"
        assert call_args[1]["target"] == "staging"
        assert call_args[1]["github_token"] == "test-token"
        assert "1.2.3-dev" in call_args[1]["title"]
        assert "manual-promotion" in call_args[1]["labels"]

    def test_promotion_validation_failure(self) -> None:
        """Test handling of promotion validation failure."""
        gitops = MagicMock(spec=GitOps)

        # Mock the config with proper data attribute
        config = MagicMock(spec=Config)
        mock_data = MagicMock()
        mock_data.validate_promotion.side_effect = ValueError("No promotion rule found")
        config.data = mock_data

        # Should raise the validation error
        with pytest.raises(ValueError, match="No promotion rule found"):
            run(
                gitops=gitops,
                config=config,
                github_token="test-token",
                from_branch="dev",
                to_branch="invalid",
            )

    @patch("auto_semver.git.GitOps.get_lock_version_from_branch")
    def test_no_version_found(self, mock_get_version: MagicMock) -> None:
        """Test handling when no version is found for source branch."""
        mock_rule = PromotionRule(from_branch="dev", to_branch="staging")
        mock_get_version.return_value = None

        gitops = MagicMock(spec=GitOps)
        gitops.get_lock_version_from_branch = mock_get_version

        # Mock the config with proper data attribute
        config = MagicMock(spec=Config)
        mock_data = MagicMock()
        mock_data.validate_promotion.return_value = mock_rule
        config.data = mock_data

        with pytest.raises(ValueError, match="No version found for branch 'dev'"):
            run(
                gitops=gitops,
                config=config,
                github_token="test-token",
                from_branch="dev",
                to_branch="staging",
            )
