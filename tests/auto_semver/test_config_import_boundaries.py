# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Guard Config-first / ``_models``-as-types import boundaries (see AGENT.md)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from auto_semver import config as config_pkg

_SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "auto_semver"

# Modules allowed to construct schema value objects at runtime (AGENT.md).
_RUNTIME_MODELS_ALLOWLIST = frozenset(
    {
        "domain/commits/grouper.py",
    }
)

_MODELS_PREFIX = "auto_semver.config._models"


def _rel_src(path: Path) -> str:
    return path.relative_to(_SRC_ROOT).as_posix()


def _is_under_config(rel: str) -> bool:
    return rel == "config.py" or rel.startswith("config/")


def _runtime_model_imports(tree: ast.AST) -> list[str]:
    """Return ``_models`` import module names that are not under ``TYPE_CHECKING``."""
    type_checking_nodes: set[ast.AST] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
            type_checking_nodes.update(ast.walk(node))

    found: list[str] = []
    for node in ast.walk(tree):
        if node in type_checking_nodes:
            continue
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
            _MODELS_PREFIX
        ):
            found.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_MODELS_PREFIX):
                    found.append(alias.name)
    return found


def _non_config_package_imports(tree: ast.AST) -> list[str]:
    """Names imported from ``auto_semver.config`` other than ``Config``."""
    bad: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "auto_semver.config":
            continue
        for alias in node.names:
            if alias.name == "*":
                bad.append("*")
            elif alias.name != "Config":
                bad.append(alias.name)
    return bad


@pytest.mark.unit
def test_config_package_exports_only_config() -> None:
    """``config.__all__`` must be Config-only — models stay private."""
    assert list(config_pkg.__all__) == ["Config"]
    assert hasattr(config_pkg, "Config")
    assert not hasattr(config_pkg, "ConfigData")


@pytest.mark.unit
def test_src_imports_config_models_only_as_types() -> None:
    """Outside ``config/``, ``_models`` runtime imports need allowlist or TYPE_CHECKING."""
    violations: list[str] = []

    for path in sorted(_SRC_ROOT.rglob("*.py")):
        rel = _rel_src(path)
        if _is_under_config(rel):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        runtime = _runtime_model_imports(tree)
        if not runtime:
            continue
        if rel in _RUNTIME_MODELS_ALLOWLIST:
            continue
        violations.append(f"{rel}: runtime _models import(s) {sorted(set(runtime))}")

    assert violations == [], (
        "Import _models under TYPE_CHECKING (or add a documented allowlist entry):\n"
        + "\n".join(violations)
    )


@pytest.mark.unit
def test_src_does_not_reexport_models_via_config_package() -> None:
    """Production code must not ``from auto_semver.config import <Model>``."""
    violations: list[str] = []

    for path in sorted(_SRC_ROOT.rglob("*.py")):
        rel = _rel_src(path)
        if _is_under_config(rel):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bad = _non_config_package_imports(tree)
        if bad:
            violations.append(f"{rel}: {sorted(set(bad))}")

    assert violations == [], (
        "Import Config from auto_semver.config; import models from config._models:\n"
        + "\n".join(violations)
    )
