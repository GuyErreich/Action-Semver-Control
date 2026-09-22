# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Orchestrate package lock sync after version-file rewrites."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from auto_semver.config._models._lock_sync import LockSyncConfig
from auto_semver.lock_sync.registry import LockStrategyRegistry, default_registry
from auto_semver.lock_sync.runner import (
    CommandResult,
    LockCommandRunner,
    LockSyncCommandError,
    LockSyncMissingToolError,
)
from auto_semver.lock_sync.strategy import LockStrategy

logger = logging.getLogger(__name__)

RunCommand = Callable[[Sequence[str], Path], CommandResult]


class LockSyncOrchestrator:
    """
    Runs registered lock strategies for a repo after version-file rewrites.

    Depends on a ``LockStrategyRegistry`` and a command runner so tests and
    future ecosystems plug in without changing this class.
    """

    def __init__(
        self,
        *,
        registry: LockStrategyRegistry | None = None,
        runner: LockCommandRunner | None = None,
        run_command: RunCommand | None = None,
    ) -> None:
        """
        Create an orchestrator.

        Args:
            registry: Strategy source (defaults to the process default registry).
            runner: Preferred command runner.
            run_command: Legacy injectable callable (tests); overrides ``runner`` when set.
        """
        self._registry = registry if registry is not None else default_registry
        self._runner = runner if runner is not None else LockCommandRunner()
        self._run_command = run_command

    def sync(self, *, repo_root: Path, config: LockSyncConfig) -> list[str]:
        """
        Sync known package lockfiles that already exist at the repo root.

        Never creates a lockfile that is not already present. Missing tools are
        skipped (or fail when ``on_missing`` is ``fail``). Non-zero lock command
        exits always raise — a stale lock is the failure mode this feature fixes.
        """
        if not config.enabled:
            logger.debug("lock_sync.enabled is false — skipping package lock sync")
            return []

        strategies = self._registry.resolve(config.ecosystems)
        synced: list[str] = []

        for strategy in strategies:
            if not strategy.detect(repo_root):
                logger.debug(
                    "Skipping ecosystem %s — lockfile %s not found",
                    strategy.name,
                    strategy.lockfile,
                )
                continue

            argv = strategy.command()
            result = self._execute(argv, repo_root)

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

    def _execute(self, argv: Sequence[str], repo_root: Path) -> CommandResult:
        if self._run_command is not None:
            return self._run_command(argv, repo_root)
        return self._runner.run(argv, cwd=repo_root)


def sync_package_locks(
    *,
    repo_root: Path,
    config: LockSyncConfig,
    strategies: Sequence[LockStrategy] | None = None,
    run_command: RunCommand | None = None,
    registry: LockStrategyRegistry | None = None,
) -> list[str]:
    """
    Sync package locks using the default orchestrator.

    ``strategies`` remains supported for tests: when provided, a temporary
    registry containing only those strategies is used.
    """
    if strategies is not None:
        temp = LockStrategyRegistry()
        for strategy in strategies:
            temp.register(strategy)
        registry = temp

    return LockSyncOrchestrator(registry=registry, run_command=run_command).sync(
        repo_root=repo_root,
        config=config,
    )
