# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pending release state shared by the composite action's steps."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypedDict, cast


class PlannedLock(TypedDict):
    """One lockfile the host step may refresh before the release commit."""

    ecosystem: str
    path: str
    tool: str
    command: list[str]


class PendingState(TypedDict, total=False):
    """JSON document written before the host lock step."""

    workflow: str
    new_version: str
    previous_version: str
    release_branch: str
    target_branch: str
    source_branch: str
    files_to_update: list[str]
    changelog_path: str
    semver_lock_path: str
    locks: list[PlannedLock]
    commit_messages: list[str]
    feature_count: int
    fix_count: int
    author: str
    repository: str
    release_strategy: str
    base_sha: str | None
    merge_message: str | None
    remote: str
    signed: bool


PENDING_NAME = "auto-semver-pending.json"


def pending_path() -> Path:
    """Return the pending-state path for this process.

    ``AUTO_SEMVER_PENDING`` wins. Otherwise the file lives in ``RUNNER_TEMP``
    so it is not committed with the release.

    Returns:
        Path of ``auto-semver-pending.json``.
    """
    explicit = os.environ.get("AUTO_SEMVER_PENDING")
    if explicit:
        return Path(explicit)
    runner = os.environ.get("RUNNER_TEMP")
    if runner:
        return Path(runner) / PENDING_NAME
    return Path(PENDING_NAME)


def write_pending(payload: PendingState) -> Path:
    """Write pending release state as JSON.

    Args:
        payload: Fields the commit phase and the host lock step need.

    Returns:
        The path that was written.
    """
    path = pending_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def read_pending() -> PendingState:
    """Load pending release state.

    Returns:
        The parsed pending document.

    Raises:
        FileNotFoundError: When prepare did not write the file.
    """
    path = pending_path()
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Pending state at {path} is not a JSON object")
    return cast(PendingState, data)
