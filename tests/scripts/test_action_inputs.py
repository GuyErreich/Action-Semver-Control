"""The published action installs the production package and runs the CLI once."""

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


def test_package_action_installs_production_release() -> None:
    """The action installs production from PyPI and does not leave its uv on PATH."""
    text = (_REPO_ROOT / "action" / "action.yml").read_text(encoding="utf-8")
    action = yaml.safe_load(text)
    runs = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    assert "auto-semver-venv/bin/auto-semver" in runs
    assert "pip install" in runs
    assert "auto-semver==" in runs
    assert "--prerelease" not in runs
    assert "uv sync" not in runs
    assert "UV_NO_MODIFY_PATH=1" in runs
    assert "GITHUB_PATH" not in runs
    assert "Dockerfile" not in text
    assert "env -u UV_PROJECT_ENVIRONMENT -u UV_FROZEN" in runs


def test_release_workflows_publish_each_channel() -> None:
    """Dev, staging, and production tags each create a release and publish to PyPI."""
    expected = {
        "publish-dev.yml": ("*.*.*-dev", "dev"),
        "publish-staging.yml": ("*.*.*-rc", "staging"),
        "publish-production.yml": ("*.*.*", "production"),
    }
    for name, (tag, environment) in expected.items():
        workflow = yaml.safe_load(
            (_REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        )
        job = workflow["jobs"]["release"]
        # PyYAML parses the workflow key "on" as boolean true.
        trigger = workflow["on"] if "on" in workflow else workflow[True]
        assert tag in trigger["push"]["tags"]
        assert job["environment"] == environment
        assert job["permissions"]["id-token"] == "write"
        uses = [step.get("uses") for step in job["steps"]]
        assert "./.github/actions/publish-pypi" in uses
        text = (_REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
        if name == "publish-production.yml":
            assert "refs/tags/v1" in text
        else:
            assert "refs/tags/v1" not in text

    publish = (_REPO_ROOT / ".github" / "actions" / "publish-pypi" / "action.yml").read_text(
        encoding="utf-8"
    )
    assert "uv version" in publish
    assert "uv publish" in publish
