# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Orchestrate package lock sync after version-file rewrites."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from auto_semver.config._models._lock_sync import LockSyncConfig
from auto_semver.lock_sync.runner import (
    CommandResult,
    LockSyncCommandError,
    LockSyncMissingToolError,
    run_lock_command,
)
from auto_semver.lock_sync.strategies import STRATEGIES, LockStrategy

logger = logging.getLogger(__name__)

RunCommand = Callable[[Sequence[str], Path], CommandResult]


def _default_run(argv: Sequence[str], cwd: Path) -> CommandResult:
    return run_lock_command(argv, cwd=cwd)


def sync_package_locks(
    *,
    repo_root: Path,
    config: LockSyncConfig,
    strategies: Sequence[LockStrategy] = STRATEGIES,
    run_command: RunCommand | None = None,
) -> list[str]:
    """
    Sync known package lockfiles that already exist at the repo root.

    Never creates a lockfile that is not already present. Missing tools are
    skipped (or fail when ``on_missing`` is ``fail``). Non-zero lock command
    exits always raise — a stale lock is the failure mode this feature fixes.

    Args:
        repo_root: Repository working tree root.
        config: Lock sync configuration.
        strategies: Ecosystem strategies to consider (defaults to built-ins).
        run_command: Optional injectable runner for tests.

    Returns:
        Relative lockfile paths that were successfully synced (for git add).
    """
    if not config.enabled:
        logger.debug("lock_sync.enabled is false — skipping package lock sync")
        return []

    runner = run_command or _default_run
    allow = set(config.ecosystems) if config.ecosystems is not None else None
    synced: list[str] = []

    for strategy in strategies:
        if allow is not None and strategy.name not in allow:
            logger.debug("Skipping ecosystem %s (not in allow-list)", strategy.name)
            continue
        if not strategy.detect(repo_root):
            logger.debug(
                "Skipping ecosystem %s — lockfile %s not found",
                strategy.name,
                strategy.lockfile,
            )
            continue

        argv = strategy.command()
        result = runner(argv, repo_root)

        if result.missing_tool:
            message = (
                f"lock_sync: tool for ecosystem '{strategy.name}' not found "
                f"(command: {' '.join(argv)})"
            )
            if config.on_missing == "fail":
                raise LockSyncMissingToolError(message)
            logger.warning("%s — skipping", message)
            continue

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise LockSyncCommandError(
                f"lock_sync: {' '.join(argv)} failed with exit {result.returncode}"
                + (f": {detail}" if detail else "")
            )

        logger.info("Synced %s via %s", strategy.lockfile, strategy.name)
        synced.append(strategy.lockfile)

    return synced
