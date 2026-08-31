"""Tests for promotion metadata helpers."""

from pathlib import Path

import pytest

from auto_semver.cli.utils import apply_promotion_metadata
from auto_semver.config import Config
from auto_semver.semver import SemverLock


@pytest.mark.unit
def test_apply_promotion_metadata_updates_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Promotion should rewrite changelog, version files, and lock for the target channel."""
    monkeypatch.chdir(tmp_path)

    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [1.4.6-dev] - 30-08-2026\n\n### Changes\n- Example\n",
        encoding="utf-8",
    )
    version_file = tmp_path / "version.txt"
    version_file.write_text("1.4.6-dev\n", encoding="utf-8")
    (tmp_path / ".semver.lock").write_text(
        "version: 1.4.6-dev\nsource_branch: dev\ntarget_branch: dev\nfinalized: false\n",
        encoding="utf-8",
    )
    (tmp_path / "auto_semver_config.yml").write_text(
        """
start_version: "0.1.0"
suffixes:
  dev: "-dev"
  staging: "-rc"
promotions:
  - from_branch: dev
    to_branch: staging
    auto_promote: true
version_files:
  - "version.txt"
changelog:
  file: "CHANGELOG.md"
  truncate: true
  template: "## [{{version}}]\\n"
commit_groups:
  - title: "Changes"
    patterns: ["^feat:"]
    priority: 1
pull_request:
  title: "Release {{version}}"
  body: "Release"
  labels: ["release"]
""",
        encoding="utf-8",
    )

    config = Config()

    apply_promotion_metadata(
        config=config,
        source_version="1.4.6-dev",
        target_version="1.4.6-rc",
        target_branch="staging",
        merge_sha="abc123",
    )

    assert "[1.4.6-rc]" in changelog.read_text(encoding="utf-8")
    assert version_file.read_text(encoding="utf-8").strip() == "1.4.6-rc"

    lock = SemverLock.load_from_file()
    assert str(lock.version) == "1.4.6-rc"
    assert lock.target_branch == "staging"
    assert lock.finalized is True
    assert lock.branch_role is None
