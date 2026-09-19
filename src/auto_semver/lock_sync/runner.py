# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Subprocess runner for official package-manager lock commands."""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class CommandResult:
    """Outcome of a lock sync command."""

    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    missing_tool: bool = False


class LockSyncCommandError(RuntimeError):
    """Raised when a lock sync command exits non-zero."""


class LockSyncMissingToolError(RuntimeError):
    """Raised when the lock CLI is not on PATH and on_missing is fail."""


def run_lock_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> CommandResult:
    """
    Run a lock sync command without a shell.

    Args:
        argv: Exact command argv (never passed through a shell).
        cwd: Working directory (repo root).
        timeout: Seconds before the process is killed.

    Returns:
        CommandResult with stdout/stderr and return code.
        ``missing_tool`` is True when the executable is not found.
    """
    argv_list = list(argv)
    logger.info("Running lock sync: %s (cwd=%s)", " ".join(argv_list), cwd)
    try:
        completed = subprocess.run(
            argv_list,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except FileNotFoundError:
        logger.warning("Lock sync tool not found: %s", argv_list[0] if argv_list else argv)
        return CommandResult(
            argv=tuple(argv_list),
            returncode=-1,
            stdout="",
            stderr="",
            missing_tool=True,
        )

    return CommandResult(
        argv=tuple(argv_list),
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        missing_tool=False,
    )
