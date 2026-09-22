# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Python / uv lock sync strategy."""

from __future__ import annotations

from auto_semver.lock_sync.strategy import LockStrategy


class UvLockStrategy(LockStrategy):
    """Regenerate ``uv.lock`` when present via ``uv lock``."""

    @property
    def name(self) -> str:
        """Ecosystem id."""
        return "uv"

    @property
    def lockfile(self) -> str:
        """Lockfile path relative to the repo root."""
        return "uv.lock"

    def command(self) -> list[str]:
        """Return ``uv lock``."""
        return ["uv", "lock"]
