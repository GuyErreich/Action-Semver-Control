"""Python CI reports the required check names and skips the suite from a path match."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_ACTION = _REPO_ROOT / ".github" / "actions" / "changed-paths" / "action.yml"
_MATCH_PATHS = _REPO_ROOT / ".github" / "actions" / "changed-paths" / "match_paths.py"
_RUN_WHEN = "steps.python.outputs.matched == 'true'"
_REQUIRED_CHECK_NAMES = ("Python 3.12", "Python 3.13")


def _load_yaml(path: Path) -> dict[str, object]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _ci_job() -> dict[str, object]:
    workflow = _load_yaml(_CI_WORKFLOW)
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    job = jobs["ci"]
    assert isinstance(job, dict)
    return job


def _patterns() -> str:
    job = _ci_job()
    steps = job["steps"]
    assert isinstance(steps, list)
    for step in steps:
        assert isinstance(step, dict)
        if step.get("id") == "python":
            with_inputs = step["with"]
            assert isinstance(with_inputs, dict)
            patterns = with_inputs["patterns"]
            assert isinstance(patterns, str)
            return patterns
    raise AssertionError("changed-paths step not found")


def _match(paths: str, patterns: str) -> str:
    result = subprocess.run(
        [sys.executable, str(_MATCH_PATHS)],
        input=paths,
        text=True,
        capture_output=True,
        env={**os.environ, "PATTERNS": patterns},
        check=True,
    )
    return result.stdout.strip()


def test_matrix_jobs_always_start_under_the_required_names() -> None:
    """Dev and staging require Python 3.12 and Python 3.13 by those exact names.

    A job-level skip reports one check named ``Python ${{ matrix.python-version }}``
    and the required checks never start.
    """
    workflow = _load_yaml(_CI_WORKFLOW)
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert list(jobs) == ["ci"]
    job = _ci_job()
    assert "if" not in job
    assert job["name"] == "Python ${{ matrix.python-version }}"
    strategy = job["strategy"]
    assert isinstance(strategy, dict)
    matrix = strategy["matrix"]
    assert isinstance(matrix, dict)
    versions = matrix["python-version"]
    assert versions == ["3.12", "3.13"]
    assert tuple(f"Python {version}" for version in versions) == _REQUIRED_CHECK_NAMES

    steps = job["steps"]
    assert isinstance(steps, list)
    checkout, detect, *rest = steps
    assert isinstance(checkout, dict)
    assert isinstance(detect, dict)
    assert checkout["uses"].startswith("actions/checkout@")
    assert "if" not in checkout
    assert detect["id"] == "python"
    assert detect["uses"] == "./.github/actions/changed-paths"
    assert "if" not in detect
    for step in rest:
        assert isinstance(step, dict)
        assert step["if"] == _RUN_WHEN


def test_changed_paths_action_matches_everything_outside_a_pull_request(tmp_path: Path) -> None:
    """workflow_dispatch and push have no pull request diff, so the suite runs."""
    action = _load_yaml(_ACTION)
    runs = action["runs"]
    assert isinstance(runs, dict)
    steps = runs["steps"]
    assert isinstance(steps, list)
    step = steps[0]
    assert isinstance(step, dict)
    script = step["run"]
    assert isinstance(script, str)
    output = tmp_path / "github_output"
    env = os.environ.copy()
    env.update(
        {
            "PR_NUMBER": "",
            "PATTERNS": "*.py",
            "REPO": "GuyErreich/Action-Semver-Control",
            "GITHUB_OUTPUT": str(output),
            "GH_TOKEN": "",
        }
    )
    result = subprocess.run(
        ["bash", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8").strip() == "matched=true"
    assert "not a pull request" in result.stderr


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        ("src/auto_semver/cli/main.py\n", "matched=true"),
        (".github/workflows/ci.yml\n", "matched=true"),
        ("pyproject.toml\n", "matched=true"),
        ("packages/demo/uv.lock\n", "matched=true"),
        (".wtp.yml\nREADME.md\n", "matched=false"),
        ("", "matched=false"),
    ],
)
def test_ci_patterns_match_python_toolchain_paths(paths: str, expected: str) -> None:
    """The workflow patterns cover Python source and the toolchain files."""
    assert _match(paths, _patterns()) == expected


def test_match_paths_supports_double_star_and_ignores_comments() -> None:
    """``**`` crosses directories, and ``#`` lines are not patterns."""
    patterns = "# comment\n**/*.py\n"
    assert _match("a/b/c.py\n", patterns) == "matched=true"
    assert _match("a/b/c.yml\n", patterns) == "matched=false"
