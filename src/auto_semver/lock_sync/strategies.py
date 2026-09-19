# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Lockfile sync strategies for known package ecosystems."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class LockStrategy(Protocol):
    """Detect a lockfile and describe how to regenerate it."""

    @property
    def name(self) -> str:
        """Ecosystem identifier (e.g. ``uv``, ``npm``)."""
        ...

    @property
    def lockfile(self) -> str:
        """Repo-root relative lockfile path."""
        ...

    def detect(self, repo_root: Path) -> bool:
        """Return True when the ecosystem lockfile exists at the repo root."""
        ...

    def command(self) -> list[str]:
        """Return the argv for the official lock sync command (no shell)."""
        ...


@dataclass(frozen=True)
class UvLockStrategy:
    """Python / uv — regenerate uv.lock when present."""

    name: str = "uv"
    lockfile: str = "uv.lock"

    def detect(self, repo_root: Path) -> bool:
        """Return True when uv.lock exists at the repo root."""
        return (repo_root / self.lockfile).is_file()

    def command(self) -> list[str]:
        """Return ``uv lock``."""
        return ["uv", "lock"]


@dataclass(frozen=True)
class NpmLockStrategy:
    """Node / npm — regenerate package-lock.json when present."""

    name: str = "npm"
    lockfile: str = "package-lock.json"

    def detect(self, repo_root: Path) -> bool:
        """Return True when package-lock.json exists at the repo root."""
        return (repo_root / self.lockfile).is_file()

    def command(self) -> list[str]:
        """Return ``npm install --package-lock-only``."""
        return ["npm", "install", "--package-lock-only"]


STRATEGIES: list[LockStrategy] = [
    UvLockStrategy(),
    NpmLockStrategy(),
]
