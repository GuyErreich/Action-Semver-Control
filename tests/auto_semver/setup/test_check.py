"""Tests for setup validation helpers."""

from pathlib import Path

import pytest

from auto_semver.setup.check import check_workflow_concurrency


@pytest.mark.unit
def test_check_workflow_concurrency_passes_with_valid_caller(tmp_path: Path) -> None:
    """Valid caller workflow with queue concurrency passes check."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "auto-semver.yml").write_text(
        """
name: Auto Semver Bump
on:
  pull_request:
    types: [closed]
concurrency:
  group: auto-semver-bump-${{ github.repository }}-${{ github.event.pull_request.base.ref }}
  cancel-in-progress: false
jobs:
  bump:
    uses: GuyErreich/Action-Semver-Control/.github/workflows/semver-bump.reusable.yml@v1
""".strip(),
        encoding="utf-8",
    )

    errors = check_workflow_concurrency(workflows)
    assert errors == []


@pytest.mark.unit
def test_check_workflow_concurrency_fails_without_block(tmp_path: Path) -> None:
    """Missing concurrency block produces actionable error."""
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "auto-semver.yml").write_text(
        """
jobs:
  bump:
    uses: GuyErreich/Action-Semver-Control/.github/workflows/semver-bump.reusable.yml@v1
""".strip(),
        encoding="utf-8",
    )

    errors = check_workflow_concurrency(workflows)
    assert any("concurrency" in err for err in errors)
