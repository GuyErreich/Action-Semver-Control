"""The published action installs the production package and runs the CLI once."""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_root_action_runs_script_from_action_path() -> None:
    """Marketplace callers use the root action without a relative ``uses`` path."""
    text = (_REPO_ROOT / "action.yml").read_text(encoding="utf-8")
    root = yaml.safe_load(text)
    steps = root["runs"]["steps"]
    assert all(step.get("uses") != "./action" for step in steps)
    run_step = next(step for step in steps if step.get("run"))
    assert run_step["run"] == 'bash "${{ github.action_path }}/action/run.sh"'
    env = run_step["env"]
    assert env["AUTO_SEMVER_TOKEN"] == "${{ inputs.github-token }}"
    assert env["AUTO_SEMVER_SIGNED"] == "${{ inputs.signed-commits }}"
    assert "Dockerfile" not in text


def test_package_action_installs_published_version_or_checkout() -> None:
    """The action pins auto-semver-control and falls back to this checkout."""
    text = (_REPO_ROOT / "action" / "action.yml").read_text(encoding="utf-8")
    action = yaml.safe_load(text)
    runs = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    runs += "\n" + (_REPO_ROOT / "action" / "run.sh").read_text(encoding="utf-8")
    assert 'bash "${{ github.action_path }}/run.sh"' in runs
    assert "auto-semver-venv/bin/auto-semver" in runs
    assert "pip install" in runs
    assert "auto-semver-control==" in runs
    assert "--prerelease explicit" in runs
    assert "sync --frozen" in runs
    assert "--frozen" in runs
    assert 'spec="auto-semver"' not in runs
    assert "UV_NO_MODIFY_PATH=1" in runs
    assert "GITHUB_PATH" not in runs
    assert "Dockerfile" not in text
    assert "env -u UV_PROJECT_ENVIRONMENT -u UV_FROZEN" in runs


def test_release_workflows_publish_each_channel() -> None:
    """Dev, staging, and production tags publish to PyPI, then create a release."""
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
        assert uses.index("./.github/actions/publish-pypi") < uses.index(
            "./.github/actions/gh-release"
        )
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
    assert "File already exists" in publish


def test_pyproject_declares_pypi_project_metadata() -> None:
    """The next PyPI upload includes links, classifiers, and the author."""
    project = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["description"]
    assert project["authors"][0]["name"] == "Guy Erreich"
    assert project["authors"][0]["email"] == "gerreich.dev@gmail.com"
    assert project["license"] == "GPL-3.0-or-later"
    assert "Typing :: Typed" in project["classifiers"]
    assert "Programming Language :: Python :: 3.14" in project["classifiers"]
    assert "Topic :: Software Development :: Libraries :: Python Modules" in project["classifiers"]
    assert all(not item.startswith("License ::") for item in project["classifiers"])
    urls = project["urls"]
    assert urls["Homepage"] == "https://github.com/GuyErreich/Action-Semver-Control"
    assert urls["Source"] == urls["Homepage"]
    assert urls["Download"].endswith("/releases")
    assert urls["Issues"].endswith("/issues")
    assert urls["Security"].endswith("/security/policy")
    assert urls["GitHub Marketplace"].endswith("/auto-semver-bumper")
    assert "CHANGELOG.md" in urls["Changelog"]
    assert "docs/SETUP.md" in urls["Documentation"]
