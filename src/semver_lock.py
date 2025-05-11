"""
semver_lock.py

Defines SemverLock, a utility class for reading and writing .semver.lock metadata files.
These lockfiles live on release branches and track bump state to avoid version regressions.
"""

import logging
import yaml
from dataclasses import dataclass
from pathlib import Path
from src.version import Version

logger = logging.getLogger(__name__)


FILE_NAME: str = ".semver.lock"

@dataclass
class SemverLock:
    version: Version
    source_branch: str
    target_branch: str
    finalized: bool = False

    @classmethod
    def load_from_file(cls, path: str | Path) -> 'SemverLock':
        """Load and parse a .semver.lock file from disk."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            return cls.from_dict(raw)
        except Exception as e:
            logger.error("Failed to load lockfile at %s: %s", path, e)
            raise

    @classmethod
    def from_dict(cls, data: dict) -> 'SemverLock':
        """Build a SemverLock instance from a parsed dict."""
        return cls(
            version=Version.parse(data["version"]),
            source_branch=data["source_branch"],
            target_branch=data["target_branch"],
            finalized=data.get("finalized", False),
        )

    def to_dict(self) -> dict:
        """Convert this object to a dict for YAML serialization."""
        return {
            "version": str(self.version),
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "finalized": self.finalized,
        }

    def save_to_file(self, path: str | Path | None = None) -> None:
        """Write this lockfile to disk."""
        path = Path(path or self.FILE_NAME)
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            logger.info("Saved lockfile to: %s", path)
        except Exception as e:
            logger.error("Failed to write lockfile: %s", e)
            raise