"""
semver_lock.py.

Defines SemverLock, a utility class for reading and writing .semver.lock metadata files.
These lockfiles live on release branches and track bump state to avoid version regressions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import yaml

from .version import Version

logger = logging.getLogger(__package__)


FILE_NAME: str = ".semver.lock"


# TODO: improve docs
@dataclass
class SemverLock:
    """
    Represents the state of a semantic version bump in progress.

    The lockfile captures the in-progress release metadata, including the version,
    source and target branches, and the base SHA used to compute changelog entries.
    This helps ensure consistency between the bump and finalize steps.

    Attributes:
        version (Version): The semantic version being prepared.
        source_branch (str): The name of the branch where the release PR originated.
        target_branch (str): The base branch the PR targets (e.g., `main` or `dev`).
        target_base_sha (str | None): The SHA from which commit messages were collected.
        finalized (bool): Whether the bump has been finalized (i.e., merged and tagged).
        path (str): The file path of the lockfile on disk.

    """

    version: Version
    source_branch: str
    target_branch: str
    target_base_sha: str | None = None
    finalized: bool = False
    path: str = FILE_NAME

    @classmethod
    def load_from_file(cls) -> SemverLock:
        """
        Load and parse the lockfile from disk.

        Returns:
            SemverLock: An instance populated from the lockfile.

        Raises:
            FileNotFoundError: If the lockfile does not exist.
            yaml.YAMLError: If the lockfile content is invalid.
        """
        logger.info(f"Loading lockfile from: {FILE_NAME}")

        try:
            with open(FILE_NAME, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            return cls.from_dict(raw)
        except FileNotFoundError:
            logger.debug(f"Lockfile not found at: {FILE_NAME}")
            raise
        except Exception as err:
            logger.error(f"Failed to load lockfile at {FILE_NAME}: {err}")
            raise

    @classmethod
    def get_or_create(
        cls,
        version: Version,
        source_branch: str,
        target_branch: str,
    ) -> SemverLock:
        """
        Retrieve existing lockfile or create a new instance if missing.

        This method acts as a safe factory that handles FileNotFoundError internally.

        Args:
            version: The version to initialize with if creating new.
            source_branch: Source branch name.
            target_branch: Target branch name.

        Returns:
            SemverLock: The loaded or newly created lock object.
        """
        try:
            return cls.load_from_file()
        except FileNotFoundError:
            logger.info("No lockfile found. Creating a new one.")
            return cls(
                version=version,
                source_branch=source_branch,
                target_branch=target_branch,
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemverLock:
        """Build a SemverLock instance from a parsed dict."""
        return cls(
            version=Version.parse(data["version"]),
            source_branch=data["source_branch"],
            target_branch=data["target_branch"],
            target_base_sha=data.get("target_base_sha"),
            finalized=data.get("finalized", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this object to a dict for YAML serialization."""
        return {
            "version": str(self.version),
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "target_base_sha": self.target_base_sha,
            "finalized": self.finalized,
        }

    def save_to_file(self) -> None:
        """Write this lockfile to disk."""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved lockfile to: {self.path}")
        except Exception as err:
            logger.error(f"Failed to write lockfile: {err}")
            raise
