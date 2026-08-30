"""Tests for setup check run_check entrypoint."""

from pathlib import Path

import pytest

from auto_semver.setup.check import run_check


@pytest.mark.unit
def test_run_check_fails_without_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run_check returns False when config file is missing."""
    monkeypatch.chdir(tmp_path)
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "auto-semver.yml").write_text(
        """
concurrency:
  group: auto-semver-bump-${{ github.repository }}-${{ github.event.pull_request.base.ref }}
  cancel-in-progress: false
jobs:
  bump:
    uses: GuyErreich/Action-Semver-Control/.github/workflows/semver-bump.reusable.yml@v1
""".strip(),
        encoding="utf-8",
    )

    assert run_check() is False
