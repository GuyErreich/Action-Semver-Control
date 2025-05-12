"""
semver_lock.py.

Defines SemverLock, a utility class for reading and writing .semver.lock metadata files.
These lockfiles live on release branches and track bump state to avoid version regressions.
"""

import logging
from dataclasses import dataclass
from typing import Any

import yaml

from auto_semver.semver import Version

logger = logging.getLogger(__name__)


FILE_NAME: str = ".semver.lock"

@dataclass
class SemverLock:
    version: Version
    source_branch: str
    target_branch: str
    finalized: bool = False
    path: str = FILE_NAME

    @classmethod
    def load_from_file(cls) -> 'SemverLock':
        """Load and parse a .semver.lock file from disk."""
        logger.info(f"Loading lockfile from: {FILE_NAME}")
        
        try:
            with open(FILE_NAME, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            return cls.from_dict(raw)
        except Exception as err:
            logger.error(f"Failed to load lockfile at {FILE_NAME}: {err}")
            raise

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SemverLock':
        """Build a SemverLock instance from a parsed dict."""
        return cls(
            version=Version.parse(data["version"]),
            source_branch=data["source_branch"],
            target_branch=data["target_branch"],
            finalized=data.get("finalized", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert this object to a dict for YAML serialization."""
        return {
            "version": str(self.version),
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
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