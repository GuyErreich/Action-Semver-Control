# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Unit tests for package lock sync."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from auto_semver.config._models._lock_sync import LockSyncConfig
from auto_semver.lock_sync.registry import LockStrategyRegistry
from auto_semver.lock_sync.runner import (
    CommandResult,
    LockSyncCommandError,
    LockSyncMissingToolError,
    run_lock_command,
)
from auto_semver.lock_sync.strategies import NpmLockStrategy, UvLockStrategy
from auto_semver.lock_sync.strategy import LockStrategy
from auto_semver.lock_sync.sync import LockSyncOrchestrator, sync_package_locks


@pytest.mark.unit
def test_lock_sync_config_defaults() -> None:
    """Omitted lock_sync uses safe defaults."""
    config = LockSyncConfig()
    assert config.enabled is True
    assert config.on_missing == "skip"
    assert config.ecosystems is None


@pytest.mark.unit
def test_lock_sync_config_rejects_unknown_ecosystem() -> None:
    """Unknown ecosystem names fail validation."""
    with pytest.raises(ValidationError, match="Unknown lock_sync ecosystems"):
        LockSyncConfig.model_validate({"ecosystems": ["cargo"]})


@pytest.mark.unit
def test_lock_sync_config_rejects_non_list_ecosystems() -> None:
    """Ecosystems must be a list when provided."""
    with pytest.raises(ValidationError, match="must be a list"):
        LockSyncConfig.model_validate({"ecosystems": "uv"})


@pytest.mark.unit
def test_sync_disabled_returns_empty(tmp_path: Path) -> None:
    """enabled=false never runs commands."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")
    calls: list[list[str]] = []

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        calls.append(list(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

    synced = sync_package_locks(
        repo_root=tmp_path,
        config=LockSyncConfig(enabled=False),
        run_command=runner,
    )
    assert synced == []
    assert calls == []


@pytest.mark.unit
def test_sync_detects_uv_and_npm(tmp_path: Path) -> None:
    """Auto-detect runs for each lockfile present."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    calls: list[list[str]] = []

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        calls.append(list(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

    synced = sync_package_locks(
        repo_root=tmp_path,
        config=LockSyncConfig(),
        run_command=runner,
    )
    assert synced == ["uv.lock", "package-lock.json"]
    assert calls == [["uv", "lock"], ["npm", "install", "--package-lock-only"]]


@pytest.mark.unit
def test_sync_skips_absent_lockfile(tmp_path: Path) -> None:
    """Never invents a lockfile that is not already present."""
    calls: list[list[str]] = []

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        calls.append(list(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

    synced = sync_package_locks(
        repo_root=tmp_path,
        config=LockSyncConfig(),
        run_command=runner,
    )
    assert synced == []
    assert calls == []


@pytest.mark.unit
def test_sync_allow_list_filters_ecosystems(tmp_path: Path) -> None:
    """Allow-list runs only the named strategies."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    calls: list[list[str]] = []

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        calls.append(list(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

    synced = sync_package_locks(
        repo_root=tmp_path,
        config=LockSyncConfig(ecosystems=["uv"]),
        run_command=runner,
    )
    assert synced == ["uv.lock"]
    assert calls == [["uv", "lock"]]


@pytest.mark.unit
def test_sync_missing_tool_skips_by_default(tmp_path: Path) -> None:
    """on_missing=skip warns and continues when the CLI is absent."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        return CommandResult(
            argv=tuple(argv),
            returncode=-1,
            stdout="",
            stderr="",
            missing_tool=True,
        )

    synced = sync_package_locks(
        repo_root=tmp_path,
        config=LockSyncConfig(on_missing="skip"),
        run_command=runner,
    )
    assert synced == []


@pytest.mark.unit
def test_sync_missing_tool_fails_when_configured(tmp_path: Path) -> None:
    """on_missing=fail aborts when the CLI is absent."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        return CommandResult(
            argv=tuple(argv),
            returncode=-1,
            stdout="",
            stderr="",
            missing_tool=True,
        )

    with pytest.raises(LockSyncMissingToolError, match="not found"):
        sync_package_locks(
            repo_root=tmp_path,
            config=LockSyncConfig(on_missing="fail"),
            run_command=runner,
        )


@pytest.mark.unit
def test_sync_nonzero_exit_raises(tmp_path: Path) -> None:
    """Non-zero lock command exit fails the bump (stale lock is the bug)."""
    (tmp_path / "uv.lock").write_text("x", encoding="utf-8")

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        return CommandResult(
            argv=tuple(argv),
            returncode=1,
            stdout="",
            stderr="lock failed",
        )

    with pytest.raises(LockSyncCommandError, match="failed with exit 1"):
        sync_package_locks(
            repo_root=tmp_path,
            config=LockSyncConfig(),
            run_command=runner,
        )


@pytest.mark.unit
def test_strategies_commands() -> None:
    """Strategies expose bounded argv lists (no shell)."""
    assert UvLockStrategy().command() == ["uv", "lock"]
    assert NpmLockStrategy().command() == ["npm", "install", "--package-lock-only"]


@pytest.mark.unit
def test_registry_extension_point(tmp_path: Path) -> None:
    """A new ecosystem plugs in via subclass + register without orchestrator changes."""

    class CargoLockStrategy(LockStrategy):
        @property
        def name(self) -> str:
            return "cargo"

        @property
        def lockfile(self) -> str:
            return "Cargo.lock"

        def command(self) -> list[str]:
            return ["cargo", "generate-lockfile"]

    (tmp_path / "Cargo.lock").write_text("x", encoding="utf-8")
    registry = LockStrategyRegistry()
    registry.register(CargoLockStrategy())
    calls: list[list[str]] = []

    def runner(argv: Sequence[str], cwd: Path) -> CommandResult:
        calls.append(list(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="", stderr="")

    synced = LockSyncOrchestrator(registry=registry, run_command=runner).sync(
        repo_root=tmp_path,
        config=LockSyncConfig(),
    )
    assert synced == ["Cargo.lock"]
    assert calls == [["cargo", "generate-lockfile"]]
    # Config validation uses the default (builtin) registry — cargo is unknown there.
    with pytest.raises(ValidationError, match="Unknown lock_sync ecosystems"):
        LockSyncConfig.model_validate({"ecosystems": ["cargo"]})


@pytest.mark.unit
def test_run_lock_command_never_uses_shell(mocker: MockerFixture, tmp_path: Path) -> None:
    """Runner passes shell=False always."""
    completed = mocker.Mock(returncode=0, stdout="", stderr="")
    run = mocker.patch("auto_semver.lock_sync.runner.subprocess.run", return_value=completed)

    result = run_lock_command(["uv", "lock"], cwd=tmp_path)

    assert result.returncode == 0
    assert result.missing_tool is False
    run.assert_called_once()
    assert run.call_args.kwargs["shell"] is False
    assert run.call_args.args[0] == ["uv", "lock"]


@pytest.mark.unit
def test_run_lock_command_missing_binary(mocker: MockerFixture, tmp_path: Path) -> None:
    """FileNotFoundError is reported as missing_tool."""
    mocker.patch(
        "auto_semver.lock_sync.runner.subprocess.run",
        side_effect=FileNotFoundError("uv"),
    )
    result = run_lock_command(["uv", "lock"], cwd=tmp_path)
    assert result.missing_tool is True
