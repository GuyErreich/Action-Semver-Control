# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Node / npm lock sync strategy."""

from __future__ import annotations

from auto_semver.lock_sync.strategy import LockStrategy


class NpmLockStrategy(LockStrategy):
    """Regenerate ``package-lock.json`` when present via ``npm install --package-lock-only``."""

    @property
    def name(self) -> str:
        """Ecosystem id."""
        return "npm"

    @property
    def lockfile(self) -> str:
        """Lockfile path relative to the repo root."""
        return "package-lock.json"

    def command(self) -> list[str]:
        """Return ``npm install --package-lock-only``."""
        return ["npm", "install", "--package-lock-only"]
