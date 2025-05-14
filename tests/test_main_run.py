import sys
import pytest
from pytest import MonkeyPatch, TempPathFactory, LogCaptureFixture
from pytest_mock import MockerFixture

from auto_semver.changelog import ChangelogManager
from auto_semver.cli import main
from auto_semver.config.data import ChangelogConfig, ConfigData, PullRequestConfig
from auto_semver.semver.version import Version
from tests.mocks.config_mocks import patch_mock_config, patch_mock_gitops, get_mock_event_dict

VERSION: Version = Version.parse("1.2.3-dev")
PR_BODY: str = "Testing PR Body  {{guy}}"
PR_LABELS: list[str] = ["semver-bump"] 

def test_main_run_logs(fake_args, tmp_path: TempPathFactory, monkeypatch: MonkeyPatch, mocker: MockerFixture, caplog: LogCaptureFixture):
    version_file = tmp_path / "version.txt"
    version_file.write_text(str(VERSION))

    changlog_file = tmp_path / "CHANGELOG.md"
    changlog_file.write_text("## testing - 11-22-3333\n- testing")

    changlog_file = tmp_path / ".semver.lock"
    changlog_file.write_text(f"""
    version: {str(VERSION)}
    source_branch: feature/lockfile
    target_branch: dev
    finalized: false
    """)

    event_file = tmp_path / "event.json"
    event_file.write_text(get_mock_event_dict(str(VERSION), pr_body=PR_BODY, pr_labels=PR_LABELS + ["testing"]))  # or paste the JSON above directly

    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))
    
    monkeypatch.setattr(sys, "argv", ["main.py"] + fake_args)
    monkeypatch.chdir(tmp_path)

    mocked_config = patch_mock_config(mocker, pr_body=PR_BODY + "s", labels=PR_LABELS + ["bad"])
    patch_mock_gitops(mocker)

    # mock_changelog = mocker.patch("main.ChangelogManager").return_value
    mocker.patch("auto_semver.cli.main.ChangelogManager", wraps=ChangelogManager.from_config(mocked_config))

    mock_semver_lock = mocker.patch("auto_semver.cli.main.SemverLock").return_value
    # mock_semver_lock.return_value = mocker.Mock()
    mock_semver_lock.return_value.save_to_file.return_value = None


    with caplog.at_level("DEBUG"):
        main()

    assert "Branch name: feature/test" in caplog.text
    assert "New version:" in caplog.text