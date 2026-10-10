"""The published action installs this package and runs the CLI once."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_root_action_delegates_to_package_action() -> None:
    """Marketplace callers still use the repository root action.yml."""
    root = yaml.safe_load((_REPO_ROOT / "action.yml").read_text(encoding="utf-8"))
    steps = root["runs"]["steps"]
    assert len(steps) == 1
    assert steps[0]["uses"] == "./action"
    forwarded = steps[0]["with"]
    assert forwarded["github-token"] == "${{ inputs.github-token }}"
    assert forwarded["signed-commits"] == "${{ inputs.signed-commits }}"
    assert "Dockerfile" not in (_REPO_ROOT / "action.yml").read_text(encoding="utf-8")


def test_package_action_runs_checkout_venv() -> None:
    """The action installs this checkout and does not leave its uv on PATH."""
    text = (_REPO_ROOT / "action" / "action.yml").read_text(encoding="utf-8")
    action = yaml.safe_load(text)
    runs = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    assert "auto-semver-venv/bin/auto-semver" in runs
    assert "UV_NO_MODIFY_PATH=1" in runs
    assert "GITHUB_PATH" not in runs
    assert "Dockerfile" not in text
    assert "--frozen" in runs
    assert "env -u UV_PROJECT_ENVIRONMENT -u UV_FROZEN" in runs
