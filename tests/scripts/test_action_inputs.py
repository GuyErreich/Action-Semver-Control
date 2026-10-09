"""The composite action must forward inputs into the engine script."""

from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REQUIRED_INPUT_ENV = (
    "INPUT_ACTION",
    "INPUT_TO_BRANCH",
    "INPUT_FROM_TAG",
    "INPUT_DRY_RUN",
    "INPUT_GITHUB_TOKEN",
    "INPUT_DEBUG",
    "INPUT_SIGNED_COMMITS",
)


def test_composite_steps_forward_action_inputs() -> None:
    """Every composite step maps inputs to the env names action-engine.sh reads.

    GitHub does not inject INPUT_* for composite run steps. The host lock
    script can also start the engine, so it needs the same mapping.
    """
    action = yaml.safe_load((_REPO_ROOT / "action.yml").read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    assert steps, "action.yml has no composite steps"

    for step in steps:
        env = step.get("env") or {}
        missing = [name for name in _REQUIRED_INPUT_ENV if name not in env]
        assert not missing, f"{step.get('name')!r} is missing {missing}"
        assert env["INPUT_GITHUB_TOKEN"] == "${{ inputs.github-token }}"
        assert env["INPUT_SIGNED_COMMITS"] == "${{ inputs.signed-commits }}"
