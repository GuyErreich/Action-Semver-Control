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
from typing import Any

import yaml
from pydantic import ValidationError

from .data import ConfigData

logger = logging.getLogger(__package__)

CONFIG_FILE: str = "auto_semver_config.yml"


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
        self.path = path
        self.path = path
        self.data = self._load_and_parse()

    def _load_and_parse(self) -> ConfigData:
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Configuration file '{self.path}' not found.")

        try:
            with open(self.path, encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}
            return ConfigData(**raw_config)
        except yaml.YAMLError as err:
            logger.error(f"Error parsing YAML configuration: {err}")
            raise
        except ValidationError as e:
            logger.error("Configuration validation failed.")
            for err in e.errors():
                loc = " -> ".join(str(i) for i in err["loc"])
                msg = err["msg"]
                typ = err["type"]
                logger.error(f"Missing or invalid config field: {loc} | {msg} [{typ}]")
            raise

    def __getattr__(self, item: str) -> Any:
        """Use for returning the named property in data."""
        return getattr(self.data, item)

    @staticmethod
    def generate_config_file(config_data: ConfigData, path: str = CONFIG_FILE) -> None:
        """
        Generate a YAML configuration file from a ConfigData object.

        Args:
            config_data (ConfigData): The configuration data to write to file.
            path (str): Path where the configuration file should be written.
                Defaults to 'auto_semver_config.yml'.

        Raises:
            OSError: If there is an error writing the configuration file.
            yaml.YAMLError: If there is an error dumping the configuration to YAML.

        """
        # Convert ConfigData to dict, excluding None values
        config_dict = config_data.model_dump(exclude_none=True)

        # Convert Version object to string for YAML serialization
        if "start_version" in config_dict:
            config_dict["start_version"] = str(config_dict["start_version"])

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration file generated at '{path}'")
        except (OSError, yaml.YAMLError) as err:
            logger.error(f"Error generating configuration file: {err}")
            raise
