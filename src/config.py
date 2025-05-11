"""
Configuration management for auto-semver-bump.

This module provides a class for loading and validating configuration
settings from a YAML file. It ensures that required keys are present
and provides methods to access various configuration options.

Typical usage::
    config = Config()
    version_files = config.get_files_to_update()
    start_version = config.get_start_version()
    suffix = config.get_suffix("main")
    branch_strategy = config.get_branch_strategy()
    label = config.get_pr_labels()
    changelog_file = config.get_changelog_file()
    should_truncate_changelog = config.should_truncate_changelog()
    changelog_template = config.get_changelog_template()
    changelog_header = config.get_changelog_header()
    changelog_footer = config.get_changelog_footer()
"""

import logging
import os
from typing import Any, cast

import yaml

from src.version import Version

logger = logging.getLogger(__name__)

CONFIG_FILE: str = "auto_semver_config.yml"
DEFAULT_CHANGELOG: str = "CHANGELOG.md"

_REQUIRED_KEYS: list[str] = [
    "suffixes",    
]


class Config:

    """
    Configuration management class for auto-semver-bump.

    This class loads configuration settings from a YAML file and provides
    methods to access various configuration options. It ensures that
    required keys are present and provides default values for optional
    settings.
    """

    def __init__(self, path: str = CONFIG_FILE) -> None:
        """
        Initialize the configuration manager.

        Args:
            path (str): Path to the configuration file. Defaults to 'auto_semver_config.yml'.

        Raises:
            RuntimeError: If the configuration file is invalid or missing required keys.
            KeyError: If a required key is missing in the configuration file.

        """    
        self._config: dict[str, Any] = {}
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._config = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError) as err:
                logger.error(f"Failed to load configuration file '{path}': {err}")
                raise RuntimeError(f"Invalid configuration file: {err}") from err
        else:
            logger.warning(f"Configuration file '{path}' not found. Using defaults.")

        for key in _REQUIRED_KEYS:
            if key not in self._config:
                logger.error(f"Missing required configuration key: '{key}'")
                raise KeyError(f"Missing required configuration key: '{key}'")

    def _get(self, *keys: str, default: Any = None) -> Any:
        """
        Retrieve a value from the configuration using a list of keys.

        Args:
            *keys (str): Keys to traverse the configuration dictionary.
            default: Default value to return if the key is not found.

        Returns:
            The value from the configuration if found, otherwise the default value.

        Raises:
            KeyError: If the key is not found and no default value is provided.

        """
        logger.debug(f"Accessing config key path: {' -> '.join(keys)}")

        try:
            value = self._config
            for key in keys:
                value = value[key]
            logger.debug(f"Found value for key path {' -> '.join(keys)}: {value}")
            return value
        except KeyError:
            if default is not None:
                logger.warning(f"Key path {' -> '.join(keys)} not found. Using default: {default}")
                return default
            logger.error(f"Missing key in config: {' -> '.join(keys)}")
            raise

    def get_files_to_update(self) -> list[str]:
        """Get the list of files to update with the new version."""
        return list[str](self._get("version_files", default=["version.txt"]))

    def get_start_version(self) -> Version:
        """Get the starting version for the versioning process."""
        return Version.parse(self._get("start_version", default="0.1.0"))

    def get_suffix(self, target_branch: str) -> str:
        """Get the suffix for the specified target branch."""
        return cast(str, self._get("suffixes", target_branch, default=None))

    def get_branch_strategy(self) -> str:
        """Get the branch strategy for versioning."""
        return str(self._get("branch_strategy", default="single"))

    def get_pr_labels(self) -> list[str]:
        """Get the labels to add to the pull request."""
        return list[str](self._get("pull_request", "labels", default=["semver-bump"]))

    def get_changelog_file(self) -> str:
        """Get the path to the changelog file."""
        return str(self._get("changelog", "file", default=DEFAULT_CHANGELOG))

    def should_truncate_changelog(self) -> bool:
        """Get if the changelog should be truncated."""
        return bool(self._get("changelog", "truncate", default=False))

    def get_changelog_template(self) -> str:
        """Get the template for the changelog entry."""
        value: str = self._get(
            "changelog",
            "template",
            default="## [{{version}}] - {{date}}\n- {{message}}"
        )

        return value

    def get_changelog_header(self) -> str:
        """Get the header content for the changelog file."""
        return str(self._get("changelog", "header", default=""))

    def get_changelog_footer(self) -> str:
        """Get the footer content for the changelog file."""
        return str(self._get("changelog", "footer", default=""))
