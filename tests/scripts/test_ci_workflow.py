"""The Python CI matrix must report the required check names when tests are skipped."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
_RUN_WHEN = "steps.decide.outputs.run == 'true'"
_REQUIRED_CHECK_NAMES = ("Python 3.12", "Python 3.13")


def _workflow() -> dict[str, object]:
    """Load the CI workflow. PyYAML parses the ``on`` key as ``True``."""
    loaded = yaml.safe_load(_CI_WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _jobs() -> dict[str, dict[str, object]]:
    jobs = _workflow()["jobs"]
    assert isinstance(jobs, dict)
    return jobs


def _ci_job() -> dict[str, object]:
    job = _jobs()["ci"]
    assert isinstance(job, dict)
    return job


def _step_run(job_name: str, step_id: str | None = None, step_name: str | None = None) -> str:
    job = _jobs()[job_name]
    steps = job["steps"]
    assert isinstance(steps, list)
    for step in steps:
        assert isinstance(step, dict)
        if step_id is not None and step.get("id") == step_id:
            run = step["run"]
            assert isinstance(run, str)
            return run
        if step_name is not None and step.get("name") == step_name:
            run = step["run"]
            assert isinstance(run, str)
            return run
    message = f"step id={step_id!r} name={step_name!r} not found in {job_name}"
    raise AssertionError(message)


def _run_script(
    script: str, env: dict[str, str], output_path: Path
) -> subprocess.CompletedProcess[str]:
    """Run a workflow step script the way Actions does, with GITHUB_OUTPUT set."""
    full_env = os.environ.copy()
    full_env.update(env)
    full_env["GITHUB_OUTPUT"] = str(output_path)
    return subprocess.run(
        ["bash", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=full_env,
    )


def test_matrix_jobs_keep_required_check_names_when_python_is_unchanged() -> None:
    """Dev and staging require Python 3.12 and Python 3.13 by those exact names.

    Skipping the matrix job before it expands reports one check named
    ``Python ${{ matrix.python-version }}``. Those required checks then never
    start, and the pull request cannot merge.
    """
    job = _ci_job()
    assert job["name"] == "Python ${{ matrix.python-version }}"
    strategy = job["strategy"]
    assert isinstance(strategy, dict)
    matrix = strategy["matrix"]
    assert isinstance(matrix, dict)
    versions = matrix["python-version"]
    assert versions == ["3.12", "3.13"]
    assert tuple(f"Python {version}" for version in versions) == _REQUIRED_CHECK_NAMES
    job_if = job["if"]
    assert isinstance(job_if, str)
    assert "outputs.python" not in job_if
    assert "needs.changes.result == 'success'" in job_if
    assert "needs.changes.result == 'failure'" in job_if
    assert job_if.startswith("always()")

    steps = job["steps"]
    assert isinstance(steps, list)
    decide = steps[0]
    assert isinstance(decide, dict)
    assert decide["id"] == "decide"
    assert "if" not in decide
    for step in steps[1:]:
        assert isinstance(step, dict)
        assert step["if"] == _RUN_WHEN


def test_decide_reports_success_without_running_the_suite(tmp_path: Path) -> None:
    """No Python diff still writes run=false and exits 0 so the check succeeds."""
    script = _step_run("ci", step_id="decide")
    output = tmp_path / "github_output"
    result = _run_script(
        script,
        {
            "CHANGES_RESULT": "success",
            "PYTHON_CHANGES": "false",
            "PYTHON_VERSION": "3.12",
        },
        output,
    )
    assert result.returncode == 0, result.stderr
    assert "run=false" in output.read_text(encoding="utf-8")
    assert "Reporting Python 3.12 as success." in result.stdout


def test_decide_runs_the_suite_when_python_changed(tmp_path: Path) -> None:
    """A Python diff sets run=true so the matrix steps execute."""
    script = _step_run("ci", step_id="decide")
    output = tmp_path / "github_output"
    result = _run_script(
        script,
        {
            "CHANGES_RESULT": "success",
            "PYTHON_CHANGES": "true",
            "PYTHON_VERSION": "3.13",
        },
        output,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == "run=true\n"
    assert "Running Python 3.13." in result.stdout


def test_decide_fails_when_change_detection_fails(tmp_path: Path) -> None:
    """A failed detection job fails the required checks instead of leaving them pending."""
    script = _step_run("ci", step_id="decide")
    output = tmp_path / "github_output"
    result = _run_script(
        script,
        {
            "CHANGES_RESULT": "failure",
            "PYTHON_CHANGES": "",
            "PYTHON_VERSION": "3.12",
        },
        output,
    )
    assert result.returncode == 1
    assert "Change detection result: failure" in result.stdout
    assert not output.exists() or output.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("ci_result", ["skipped", "failure", "cancelled"])
def test_python_ci_rollup_rejects_a_matrix_that_did_not_succeed(
    tmp_path: Path,
    ci_result: str,
) -> None:
    """A skipped matrix must not look green. Required checks only count a success."""
    script = _step_run("python-ci", step_name="Evaluate Python CI")
    result = _run_script(script, {"CI_RESULT": ci_result}, tmp_path / "github_output")
    assert result.returncode == 1
    assert f"Python CI result: {ci_result}" in result.stdout


def test_python_ci_rollup_passes_when_the_matrix_succeeds(tmp_path: Path) -> None:
    """The rollup stays green when both matrix legs succeed, including the no-op path."""
    script = _step_run("python-ci", step_name="Evaluate Python CI")
    result = _run_script(script, {"CI_RESULT": "success"}, tmp_path / "github_output")
    assert result.returncode == 0, result.stderr
    assert "Python CI result: success" in result.stdout
