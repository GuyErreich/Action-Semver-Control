import sys
import pytest
from pytest import MonkeyPatch, TempPathFactory, LogCaptureFixture
from pytest_mock import MockerFixture

from auto_semver.changelog import ChangelogManager
from auto_semver.cli import main

@pytest.fixture
def fake_args():
    return [
        "--branch-name", "bufix/test",
        "--target-branch", "dev",
        "--github-token", "ghp_mocktoken",
        "--repo-full-name", "example/repo",
        "--debug",
    ]


def test_main_run_logs(fake_args, tmp_path: TempPathFactory, monkeypatch: MonkeyPatch, mocker: MockerFixture, caplog: LogCaptureFixture):
    version_file = tmp_path / "version.txt"
    version_file.write_text("0.2.0-dev")

    changlog_file = tmp_path / "CHANGELOG.md"
    changlog_file.write_text("## testing - 11-22-3333\n- testing")
    
    monkeypatch.setattr(sys, "argv", ["main.py"] + fake_args)
    monkeypatch.chdir(tmp_path)

    # Patch all external dependencies
    mock_config = mocker.patch("auto_semver.cli.main.Config").return_value
    mock_config.get_suffix.return_value = "-dev"
    mock_config.get_start_version.return_value = "0.2.0-dev"
    mock_config.get_files_to_update.return_value = ["version.txt"]
    mock_config.get_branch_strategy.return_value = "single"
    mock_config.get_changelog_file.return_value = "CHANGELOG.md"
    mock_config.should_truncate_changelog.return_value = True
    mock_config.get_changelog_template.return_value = "## [{{version}}] - {{date}}\n- {{message}}"
    mock_config.get_changelog_header.return_value = "# Changelog"
    mock_config.get_changelog_footer.return_value = ""

    mock_gitops = mocker.patch("auto_semver.cli.main.GitOps").return_value
    mock_gitops.get_highest_release_lock_version_for_target.return_value = None
    mock_gitops.create_branch.return_value = None
    mock_gitops.add.return_value = None
    mock_gitops.commit.return_value = None
    mock_gitops.push.return_value = None
    mock_gitops.close_old_release_prs.return_value = None
    mock_gitops.get_current_commit_sha.return_value = "deadbeef"
    mock_gitops.get_recent_commits.return_value = ["Added test"]
    mock_gitops.create_pr.return_value = 123

    # mock_changelog = mocker.patch("main.ChangelogManager").return_value
    mocker.patch("auto_semver.cli.main.ChangelogManager", wraps=ChangelogManager.from_config(mock_config))

    mock_semver_lock = mocker.patch("auto_semver.cli.main.SemverLock").return_value
    # mock_semver_lock.return_value = mocker.Mock()
    mock_semver_lock.return_value.save_to_file.return_value = None


    with caplog.at_level("DEBUG"):
        main()

    assert "Branch name: feature/test" in caplog.text
    assert "New version:" in caplog.text