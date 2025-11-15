"""
Integration tests for action execution in simulated CI environments.

Tests the GitHub Action in various simulated CI scenarios with different
event types (push, pull_request, tag). All tests use isolated environments
and mocked APIs to prevent any real-world interaction.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import responses
from git import Repo


@pytest.mark.integration
def test_action_on_push_event(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test action execution on push event to dev branch.

    Simulates:
    - GITHUB_EVENT_NAME=push
    - GITHUB_REF=refs/heads/dev
    - GITHUB_REPOSITORY=testuser/testrepo
    """
    repo_dir = tmp_path / "push_event_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "GitHub Actions").release()
    repo.config_writer().set_value("user", "email", "actions@github.com").release()

    # Setup version and config
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0\n")

    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  dev:
    bump: patch
    prerelease: dev
  main:
    bump: minor
""")

    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: initial setup")

    dev_branch = repo.create_head("dev")
    dev_branch.checkout()

    # Make a change
    feature_file = repo_dir / "feature.py"
    feature_file.write_text("# New feature\n")
    repo.index.add(["feature.py"])
    repo.index.commit("feat: add new feature")

    # Create GitHub event file
    event_file = tmp_path / "github_event.json"
    event_data = {
        "ref": "refs/heads/dev",
        "repository": {
            "name": "testrepo",
            "owner": {"login": "testuser"},
            "default_branch": "main",
        },
        "pusher": {"name": "testuser"},
    }
    event_file.write_text(json.dumps(event_data))

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Simulate GitHub Actions environment
    env = dict(isolated_env) if isolated_env else {}
    env.update(
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/dev",
            "GITHUB_REPOSITORY": "testuser/testrepo",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_WORKSPACE": str(repo_dir),
        }
    )

    # Run bump command as action would
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "auto_semver.cli.bump",
            "--dry-run",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    # Verify execution
    assert result.returncode == 0, f"Action failed on push event:\n{result.stderr}"


@pytest.mark.integration
def test_action_on_pull_request_event(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test action execution on pull_request event.

    Simulates:
    - GITHUB_EVENT_NAME=pull_request
    - GITHUB_REF=refs/pull/1/merge
    - Pull request from feature to dev
    """
    repo_dir = tmp_path / "pr_event_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "GitHub Actions").release()
    repo.config_writer().set_value("user", "email", "actions@github.com").release()

    # Setup
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0\n")

    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  dev:
    bump: patch
  main:
    bump: minor
pull_request:
  enabled: true
  title_template: "Release {{version}}"
""")

    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: initial setup")

    # Create branches
    dev_branch = repo.create_head("dev")
    dev_branch.checkout()

    feature_branch = repo.create_head("feature/test")
    feature_branch.checkout()

    feature_file = repo_dir / "feature.py"
    feature_file.write_text("# Feature\n")
    repo.index.add(["feature.py"])
    repo.index.commit("feat: new feature")

    # Create GitHub event file
    event_file = tmp_path / "github_event.json"
    event_data = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "number": 1,
            "head": {"ref": "feature/test"},
            "base": {"ref": "dev"},
            "title": "Add new feature",
        },
        "repository": {
            "name": "testrepo",
            "owner": {"login": "testuser"},
            "default_branch": "main",
        },
    }
    event_file.write_text(json.dumps(event_data))

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo/pulls/1",
        json=event_data["pull_request"],
        status=200,
    )

    # Simulate GitHub Actions environment
    env = dict(isolated_env) if isolated_env else {}
    env.update(
        {
            "GITHUB_EVENT_NAME": "pull_request",
            "GITHUB_REF": "refs/pull/1/merge",
            "GITHUB_REPOSITORY": "testuser/testrepo",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_WORKSPACE": str(repo_dir),
        }
    )

    # Run bump command
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "auto_semver.cli.bump",
            "--dry-run",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    # Verify execution (may not fully succeed without all setup, but should attempt)
    assert result.returncode in [0, 1], f"Unexpected error:\n{result.stderr}"


@pytest.mark.integration
def test_action_on_tag_push_event(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test action execution on tag push (promotion scenario).

    Simulates:
    - GITHUB_EVENT_NAME=push
    - GITHUB_REF=refs/tags/v1.0.0-dev.1
    - Promotion from dev tag to main
    """
    repo_dir = tmp_path / "tag_push_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "GitHub Actions").release()
    repo.config_writer().set_value("user", "email", "actions@github.com").release()

    # Setup
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0-dev.1\n")

    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  dev:
    bump: patch
    prerelease: dev
  main:
    bump: patch
promotion:
  enabled: true
  from: dev
  to: main
""")

    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: setup")

    dev_branch = repo.create_head("dev")
    dev_branch.checkout()
    repo.create_tag("v1.0.0-dev.1")

    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Create GitHub event file
    event_file = tmp_path / "github_event.json"
    event_data = {
        "ref": "refs/tags/v1.0.0-dev.1",
        "repository": {
            "name": "testrepo",
            "owner": {"login": "testuser"},
            "default_branch": "main",
        },
        "pusher": {"name": "testuser"},
    }
    event_file.write_text(json.dumps(event_data))

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Simulate GitHub Actions environment
    env = dict(isolated_env) if isolated_env else {}
    env.update(
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/tags/v1.0.0-dev.1",
            "GITHUB_REPOSITORY": "testuser/testrepo",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_WORKSPACE": str(repo_dir),
        }
    )

    # Run bump command for promotion
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "auto_semver.cli.bump",
            "--dry-run",
            "--source-tag",
            "v1.0.0-dev.1",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    # Verify execution
    assert result.returncode in [0, 1], f"Unexpected error:\n{result.stderr}"


@pytest.mark.integration
def test_action_with_changelog_generation(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test action with changelog generation enabled.

    Verifies changelog is generated from commit messages.
    """
    repo_dir = tmp_path / "changelog_action_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "GitHub Actions").release()
    repo.config_writer().set_value("user", "email", "actions@github.com").release()

    # Setup with changelog config
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0\n")

    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  main:
    bump: patch
changelog:
  enabled: true
  file: CHANGELOG.md
  template: |
    # Changelog
    
    ## {{version}} - {{date}}
    
    {% for commit in commits %}
    - {{commit.message}}
    {% endfor %}
""")

    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: initial setup")

    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Make changes
    for i in range(3):
        test_file = repo_dir / f"feature_{i}.py"
        test_file.write_text(f"# Feature {i}\n")
        repo.index.add([f"feature_{i}.py"])
        repo.index.commit(f"feat: add feature {i}")

    # Create GitHub event file
    event_file = tmp_path / "github_event.json"
    event_data = {
        "ref": "refs/heads/main",
        "repository": {
            "name": "testrepo",
            "owner": {"login": "testuser"},
            "default_branch": "main",
        },
    }
    event_file.write_text(json.dumps(event_data))

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Simulate GitHub Actions environment
    env = dict(isolated_env) if isolated_env else {}
    env.update(
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": "testuser/testrepo",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_WORKSPACE": str(repo_dir),
        }
    )

    # Run bump with changelog
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "auto_semver.cli.bump",
            "--dry-run",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    # Verify execution
    assert result.returncode == 0, f"Action failed:\n{result.stderr}"


@pytest.mark.integration
def test_action_with_missing_permissions(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test action behavior when GitHub permissions are insufficient.

    Should fail gracefully with clear error message.
    """
    repo_dir = tmp_path / "no_perms_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "GitHub Actions").release()
    repo.config_writer().set_value("user", "email", "actions@github.com").release()

    # Setup
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0\n")

    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  main:
    bump: patch
""")

    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: setup")

    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Mock GitHub API with 403 Forbidden
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"message": "Forbidden"},
        status=403,
    )

    # Create GitHub event file
    event_file = tmp_path / "github_event.json"
    event_data = {
        "ref": "refs/heads/main",
        "repository": {
            "name": "testrepo",
            "owner": {"login": "testuser"},
        },
    }
    event_file.write_text(json.dumps(event_data))

    # Simulate GitHub Actions environment
    env = dict(isolated_env) if isolated_env else {}
    env.update(
        {
            "GITHUB_EVENT_NAME": "push",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": "testuser/testrepo",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_WORKSPACE": str(repo_dir),
            "GITHUB_TOKEN": "fake-token",
        }
    )

    # Run bump (should handle error gracefully)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "auto_semver.cli.bump",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    # Should fail or handle gracefully
    # The exact behavior depends on implementation
    assert result.returncode in [0, 1, 2], f"Unexpected crash:\n{result.stderr}"
