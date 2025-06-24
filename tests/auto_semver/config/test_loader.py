"""
Unit tests for the loader module in auto_semver.config.loader.

This module contains comprehensive tests for the Config class, which handles loading
and validating configuration from YAML files.
"""

import os
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from auto_semver.config import Config
from auto_semver.config.data import (
    ChangelogConfig,
    ConfigData,
    PromotionRule,
    PullRequestConfig,
)
from auto_semver.config.loader import CONFIG_FILE
from auto_semver.semver import Version


class TestConfig:
    """Tests for the Config class."""

    @pytest.fixture
    def mock_yaml_file(self, tmp_path: Path) -> Path:
        """Create a mock YAML config file."""
        yaml_content = """
        start_version: "0.1.0"
        suffixes:
          dev: "-dev"
          staging: "-rc"
          main: ""
        branch_strategy: "single"
        version_files:
          - "version.txt"
        promotions:
          - from_branch: dev
            to_branch: staging
          - from_branch: staging
            to_branch: main
        pull_request:
          title: "Release {{version}}"
          body: |
            ## Release Notes
            - Version: {{version}}
            - Date: {{date}}
          labels:
            - "semver-bump"
        changelog:
          file: "CHANGELOG.md"
          truncate: false
          template: |
            ## [{{version}}] - {{date}}
            {% for msg in messages %}
            - {{ msg }}
            {% endfor %}
        """
        config_file = tmp_path / "auto_semver_config.yml"
        config_file.write_text(yaml_content)
        return config_file

    @pytest.mark.unit
    def test_init_loads_config_from_default_path(
        self, mocker: MockerFixture, mock_yaml_file: Path
    ) -> None:
        """Test Config initialization loads from the default path."""
        # Mock os.path.exists to return True for the default path
        mocker.patch("os.path.exists", return_value=True)

        # Mock open to return our mock YAML file
        mock_open = mocker.patch(
            "builtins.open", mocker.mock_open(read_data=mock_yaml_file.read_text())
        )

        config = Config()

        # Verify open was called with the default path
        # Note that the mock_open is called differently in newer Python versions
        # and may not include the 'r' mode explicitly
        assert mock_open.call_args.args[0] == CONFIG_FILE

        # Check a few values to verify the config was loaded correctly
        assert config.data.branch_strategy == "single"
        assert isinstance(config.data, ConfigData)

    @pytest.mark.unit
    def test_init_with_custom_path(self, mock_yaml_file: Path) -> None:
        """Test Config initialization with a custom path."""
        config = Config(path=str(mock_yaml_file))

        # Verify the config was loaded correctly from the custom path
        assert config.data.branch_strategy == "single"
        assert isinstance(config.data, ConfigData)

    @pytest.mark.unit
    def test_init_with_missing_file(self) -> None:
        """Test initialization handles missing config file gracefully."""
        non_existent_path = "/path/to/non/existent/config.yml"

        with pytest.raises(FileNotFoundError, match="Configuration file .* not found"):
            Config(path=non_existent_path)

    @pytest.mark.unit
    def test_init_with_invalid_yaml(self, tmp_path: Path) -> None:
        """Test initialization handles invalid YAML format."""
        invalid_yaml_file = tmp_path / "invalid_config.yml"
        # Create valid YAML syntax but with invalid structure
        invalid_yaml_file.write_text("invalid_key: true\nno_required_fields: true")

        with pytest.raises(ValueError):
            Config(path=str(invalid_yaml_file))

    @pytest.mark.unit
    def test_init_with_incomplete_config(self, tmp_path: Path) -> None:
        """Test initialization handles incomplete config data."""
        incomplete_yaml_file = tmp_path / "incomplete_config.yml"
        incomplete_yaml_file.write_text("""
        # Missing required fields like suffixes and promotions
        start_version: "0.1.0"
        branch_strategy: "single"
        """)

        with pytest.raises(ValueError, match="validation error"):
            Config(path=str(incomplete_yaml_file))

    @pytest.mark.unit
    def test_generate_config_file(self, tmp_path: Path) -> None:
        """Test generating a config file from ConfigData."""
        output_path = str(tmp_path / "generated_config.yml")

        # Create a minimal ConfigData object
        config_data = ConfigData(
            start_version=str(Version.parse("1.0.0")),  # type: ignore[arg-type]
            suffixes={"main": "", "dev": "-dev"},
            branch_strategy="single",
            version_files=["version.txt"],
            promotions=[PromotionRule(from_branch="dev", to_branch="main")],
            pull_request=PullRequestConfig(
                title="Release {{version}}", body="Release notes", labels=["release"]
            ),
            changelog=ChangelogConfig(
                file="CHANGELOG.md", truncate=False, template="## {{version}}"
            ),
        )

        # Generate the config file
        Config.generate_config_file(config_data, output_path)

        # Verify file was created
        assert os.path.exists(output_path)

        # Load the generated file and verify contents
        generated_config = Config(path=output_path)
        assert str(generated_config.data.start_version) == "1.0.0"
        assert generated_config.data.branch_strategy == "single"
        assert "version.txt" in generated_config.data.version_files
