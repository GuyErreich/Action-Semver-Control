# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Abstract lock-sync strategy (Strategy pattern)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class LockStrategy(ABC):
    """
    One package-manager ecosystem's lockfile sync behavior.

    To add a new ecosystem:
    1. Subclass ``LockStrategy`` with ``name``, ``lockfile``, and ``command()``.
    2. Register an instance on the default registry (see ``strategies`` package).
    3. Config ``ecosystems`` allow-list accepts the new ``name`` automatically.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable ecosystem id used in config (e.g. ``uv``, ``npm``)."""

    @property
    @abstractmethod
    def lockfile(self) -> str:
        """Repo-root relative lockfile path that must already exist."""

    @abstractmethod
    def command(self) -> list[str]:
        """Bounded argv for the official lock sync CLI (never shell-interpolated)."""

    def detect(self, repo_root: Path) -> bool:
        """Return True when this ecosystem's lockfile exists at the repo root."""
        return (repo_root / self.lockfile).is_file()
