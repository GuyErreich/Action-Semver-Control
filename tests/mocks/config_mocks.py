import json
from typing import Any

from pytest import Config
from pytest_mock import MockerFixture

from auto_semver.config.data import ChangelogConfig, ConfigData, PullRequestConfig


def get_mock_event_dict(version: str, pr_body: str, pr_labels: list[str]) -> str:
    event: dict[str, Any] = {
      "pull_request": {
        "head": {
          "ref": "feature/add-login",
          "sha": "abc123source"
        },
        "base": {
          "ref": "main",
          "sha": "def456target"
        },
        "merged": True,
        "merge_commit_sha": "deadbeefmerged",
        "title": f"Release {version}",
        "body": pr_body,
        "labels": [
            {
                "id": i + 1,
                "name": label,
                "color": "f29513" if i == 0 else "5319e7",
                "default": i == 0,
                "description": f"Mock label: {label}"
            }
            for i, label in enumerate(pr_labels)
        ]
      }
    }

    return json.dumps(event, sort_keys=True, indent=4)


def patch_mock_gitops(mocker: MockerFixture):
    gitops = mocker.patch("auto_semver.cli.main.GitOps").return_value
    gitops.get_highest_release_lock_version_for_target.return_value = None
    gitops.create_branch.return_value = None
    gitops.add.return_value = None
    gitops.commit.return_value = None
    gitops.push.return_value = None
    gitops.close_old_release_prs.return_value = None
    gitops.get_current_commit_sha.return_value = "deadbeef"
    gitops.get_recent_commits.return_value = ["Added test"]
    gitops.create_pr.return_value = 123
    return gitops

def patch_mock_config(mocker: MockerFixture, pr_body: str, labels: list[str]) -> Config:
    config_data = ConfigData(
        start_version="0.2.0-dev",
        suffixes={"dev": "-dev"},
        version_files=["version.txt"],
        branch_strategy="single",
        pull_request=PullRequestConfig(
            labels=labels,
            body=pr_body
        ),
        changelog=ChangelogConfig(
            file="CHANGELOG.md",
            truncate=True,
            header="# Changelog",
            footer=""
        )
    )

    mocker.patch("auto_semver.cli.main.Config._load_and_parse", return_value=config_data)

    config: Config = mocker.patch("auto_semver.cli.main.Config").return_value
    config.data = config_data
    
    return config
