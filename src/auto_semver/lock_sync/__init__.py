# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Sync language package lockfiles after version bumps."""

from __future__ import annotations

from typing import Any

# Register built-ins on import. Do not import ``sync`` here — it depends on
# config models that import this package for registry validation.
import auto_semver.lock_sync.strategies as _builtin_strategies  # noqa: F401
from auto_semver.lock_sync.registry import LockStrategyRegistry, default_registry
from auto_semver.lock_sync.strategy import LockStrategy

__all__ = [
    "LockStrategy",
    "LockStrategyRegistry",
    "LockSyncOrchestrator",
    "default_registry",
    "sync_package_locks",
]


def __getattr__(name: str) -> Any:
    """Lazy-load orchestrator exports to avoid import cycles with config."""
    if name == "sync_package_locks":
        from auto_semver.lock_sync.sync import sync_package_locks  # noqa: PLC0415

        return sync_package_locks
    if name == "LockSyncOrchestrator":
        from auto_semver.lock_sync.sync import LockSyncOrchestrator  # noqa: PLC0415

        return LockSyncOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
