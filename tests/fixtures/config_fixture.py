"""
Configuration fixtures for testing.

This module provides a fixture class for creating configuration files for testing.
"""

from pathlib import Path
from typing import Any

from pyfakefs.fake_filesystem import FakeFilesystem

from auto_semver.config import Config, ConfigData


# TODO: make this better by using Config instead of kwargs
class ConfigFixture:
    """
    A fixture class that provides configuration files for tests using fakefs.

    This class provides methods to create configuration files with various
    configurations, making it easier to test different scenarios.
    """

    def __init__(self, fs: FakeFilesystem):
        """
        Initialize the fixture.

        Args:
            fs: Fake filesystem for testing
        """
        self.fs = fs

        # Ensure the current directory exists in the fake filesystem
        current_dir = Path.cwd()
        if not self.fs.exists(current_dir):
            self.fs.create_dir(current_dir)

            # Set the config path using pathlib for proper path joining
        self.config_path = current_dir / "shit-test.yml"

    # TODO: use ConfigData instead of kwargs
    def create(self, **kwargs: Any) -> None:
        """
        Create a configuration file with the specified settings.

        Args:
            **kwargs: Configuration settings as keyword arguments.
                     These will be passed to ConfigData for validation.
        """
        # Provide sensible defaults for required fields if not specified
        defaults = {
            "suffixes": {"main": ""},
            "promotions": [],
            "pull_request": {
                "title": "Release {{version}}",
                "body": "Version: {{version}}",
                "labels": ["release"],
            },
            "changelog": {
                "file": "CHANGELOG.md",
                "truncate": False,
                "template": (
                    "## [{{version}}] - {{date}}\n"
                    "{% for msg in messages -%}\n- {{ msg }}\n{%- endfor %}\n"
                ),
            },
        }

        # Merge defaults with provided kwargs (kwargs take precedence)
        config_kwargs = {**defaults, **kwargs}

        config_data = ConfigData(**config_kwargs)

        # Use the Config class's generate_config_file method to create the file
        # This ensures proper serialization handling
        # The pyfakefs should intercept the file operations
        Config.generate_config_file(config_data=config_data, path=self.config_path)

    def create_minimal(self) -> None:
        """Create a minimal configuration file with only required fields."""
        self.create(
            suffixes={"main": ""},
            commit_groups=[],
            promotions=[],
        )

    def create_with_complex_commit_groups(self) -> None:
        """Create a configuration with complex commit group patterns for testing."""
        complex_groups = [
            {
                "title": "Breaking Changes",
                "patterns": [r"^feat.*!:", r"^fix.*!:", r"^BREAKING CHANGE"],
                "priority": 1,
            },
            {"title": "Features", "patterns": [r"^feat(?:\(.*?\))?:"], "priority": 2},
            {"title": "Bug Fixes", "patterns": [r"^fix(?:\(.*?\))?:"], "priority": 3},
            {"title": "Documentation", "patterns": [r"^docs(?:\(.*?\))?:"], "priority": 4},
            {"title": "Performance", "patterns": [r"^perf(?:\(.*?\))?:"], "priority": 5},
            {"title": "Refactoring", "patterns": [r"^refactor(?:\(.*?\))?:"], "priority": 6},
            {"title": "Tests", "patterns": [r"^test(?:\(.*?\))?:"], "priority": 7},
            {
                "title": "Build & CI",
                "patterns": [r"^build(?:\(.*?\))?:", r"^ci(?:\(.*?\))?:"],
                "priority": 8,
            },
            {"title": "Other Changes", "patterns": [".*"], "priority": 999},
        ]
        self.create(
            suffixes={"main": ""},
            commit_groups=complex_groups,
            promotions=[],
        )

    def create_with_simple_patterns(self) -> None:
        """Create a configuration with simple commit group patterns for testing."""
        simple_groups = [
            {"title": "Features", "patterns": ["feat"], "priority": 1},
            {"title": "Bug Fixes", "patterns": ["fix"], "priority": 2},
        ]
        self.create(
            suffixes={"main": ""},
            commit_groups=simple_groups,
            promotions=[],
        )

    def create_with_regex_patterns(self) -> None:
        """Create a configuration with explicit regex patterns for testing."""
        regex_groups = [
            {"title": "Features", "patterns": [r"^feat"], "priority": 1},
            {"title": "Bug Fixes", "patterns": [r"^fix"], "priority": 2},
        ]
        self.create(
            suffixes={"main": ""},
            commit_groups=regex_groups,
            promotions=[],
        )

    def create_empty_commit_groups(self) -> None:
        """Create a configuration with no commit groups for testing."""
        self.create(
            suffixes={"main": ""},
            commit_groups=[],
            promotions=[],
        )

    def __call__(self) -> None:
        """
        Sets up the default configuration file.

        This method allows the fixture to be used as a callable that sets up
        the default configuration.
        """
        self.create_minimal()
