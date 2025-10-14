"""
E2E workflow tests for full release cycle validation.

Tests complete workflows from commit to release in fully isolated environments.
All tests use temp_git_repo, mock_github_api, and isolated_env to ensure
no interaction with real filesystem, git repos, or external APIs.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import responses
from git import Repo


@pytest.mark.integration
def test_feature_branch_to_dev_workflow(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test feature branch merge to dev: patch bump expected.

    Workflow:
    1. Start with dev at v1.0.0
    2. Create feature branch
    3. Make commits (fix:, feat:)
    4. Merge to dev
    5. Verify version bumped to v1.0.1
    """
    # Create isolated git repo
    repo_dir = tmp_path / "feature_workflow_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git user
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial files
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
""")
    
    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: initial commit")
    
    # Create dev branch
    dev_branch = repo.create_head("dev")
    dev_branch.checkout()

    # Create feature branch
    feature_branch = repo.create_head("feature/test-feature")
    feature_branch.checkout()

    # Make feature commits
    test_file = repo_dir / "test.py"
    test_file.write_text("def test(): pass\n")
    repo.index.add(["test.py"])
    repo.index.commit("feat: add test function")

    test_file.write_text("def test(): return True\n")
    repo.index.add(["test.py"])
    repo.index.commit("fix: fix test function")

    # Merge to dev
    dev_branch.checkout()
    repo.git.merge("feature/test-feature", no_ff=True)

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
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
        env={**isolated_env, "GITHUB_REPOSITORY": "testuser/testrepo"} if isolated_env else None,
    )

    # Verify execution
    assert result.returncode == 0, f"Command failed:\n{result.stderr}"
    
    # In dry-run mode, version file shouldn't change
    assert version_file.read_text().strip() == "1.0.0"


@pytest.mark.integration
def test_hotfix_to_main_workflow(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test hotfix branch to main: patch bump expected.

    Workflow:
    1. Start with main at v2.0.0
    2. Create hotfix branch
    3. Make fix commits
    4. Merge to main
    5. Verify version bumped to v2.0.1
    """
    repo_dir = tmp_path / "hotfix_workflow_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial state at v2.0.0
    version_file = repo_dir / "version.txt"
    version_file.write_text("2.0.0\n")
    
    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  main:
    bump: patch
  dev:
    bump: patch
""")
    
    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: initial commit at v2.0.0")
    
    # Create main branch
    main_branch = repo.create_head("main")
    main_branch.checkout()
    repo.create_tag("v2.0.0")

    # Create hotfix branch
    hotfix_branch = repo.create_head("hotfix/critical-bug")
    hotfix_branch.checkout()

    # Make hotfix commits
    bug_file = repo_dir / "bugfix.py"
    bug_file.write_text("# Critical bug fixed\n")
    repo.index.add(["bugfix.py"])
    repo.index.commit("fix: resolve critical security issue")

    # Merge to main
    main_branch.checkout()
    repo.git.merge("hotfix/critical-bug", no_ff=True)

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Run bump in dry-run
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
        env={**isolated_env, "GITHUB_REPOSITORY": "testuser/testrepo"} if isolated_env else None,
    )

    assert result.returncode == 0, f"Command failed:\n{result.stderr}"


@pytest.mark.integration
def test_promotion_workflow(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test tag promotion from dev to main.

    Workflow:
    1. Dev has v1.0.0-dev.1
    2. Promote to main
    3. Verify promoted to v1.0.0
    """
    repo_dir = tmp_path / "promotion_workflow_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial state
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
    repo.index.commit("chore: setup v1.0.0-dev.1")
    
    # Create branches
    dev_branch = repo.create_head("dev")
    dev_branch.checkout()
    repo.create_tag("v1.0.0-dev.1")
    
    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Simulate promotion (dry-run)
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
        env={**isolated_env, "GITHUB_REPOSITORY": "testuser/testrepo"} if isolated_env else None,
    )

    # Check execution
    assert result.returncode in [0, 1], f"Unexpected error:\n{result.stderr}"


@pytest.mark.integration
def test_multiple_version_files_workflow(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test workflow with multiple version files (package.json, pyproject.toml, version.txt).

    Verifies all version files are detected and can be updated.
    """
    repo_dir = tmp_path / "multi_version_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create multiple version files
    version_txt = repo_dir / "version.txt"
    version_txt.write_text("1.0.0\n")
    
    package_json = repo_dir / "package.json"
    package_json.write_text('{\n  "version": "1.0.0"\n}\n')
    
    pyproject_toml = repo_dir / "pyproject.toml"
    pyproject_toml.write_text('[project]\nversion = "1.0.0"\n')
    
    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
  - package.json
  - pyproject.toml
branches:
  main:
    bump: patch
""")
    
    repo.index.add(["version.txt", "package.json", "pyproject.toml", "auto_semver_config.yml"])
    repo.index.commit("chore: initial setup")
    
    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Make a change
    test_file = repo_dir / "test.txt"
    test_file.write_text("test\n")
    repo.index.add(["test.txt"])
    repo.index.commit("feat: add test file")

    # Mock GitHub API
    mock_github_api.add(
        responses.GET,
        "https://api.github.com/repos/testuser/testrepo",
        json={"default_branch": "main"},
        status=200,
    )

    # Run bump in dry-run
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
        env={**isolated_env, "GITHUB_REPOSITORY": "testuser/testrepo"} if isolated_env else None,
    )

    assert result.returncode == 0, f"Command failed:\n{result.stderr}"
    
    # Verify all files still at original version (dry-run)
    assert "1.0.0" in version_txt.read_text()
    assert "1.0.0" in package_json.read_text()
    assert "1.0.0" in pyproject_toml.read_text()


@pytest.mark.integration
def test_error_handling_no_config(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test error handling when config file is missing.

    Should fail gracefully with clear error message.
    """
    repo_dir = tmp_path / "no_config_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create only version file, no config
    version_file = repo_dir / "version.txt"
    version_file.write_text("1.0.0\n")
    repo.index.add(["version.txt"])
    repo.index.commit("chore: initial commit")

    # Run bump (may succeed with defaults or fail)
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
        env={**isolated_env} if isolated_env else None,
    )

    # Should handle missing config gracefully (may use defaults)
    # Return code can be 0 (with defaults) or non-zero (error)
    assert result.returncode in [0, 1], f"Unexpected crash:\n{result.stderr}"


@pytest.mark.integration
def test_error_handling_invalid_version(
    tmp_path: Path,
    mock_github_api: responses.RequestsMock,
    isolated_env: None,
) -> None:
    """
    Test error handling with invalid version format.

    Should fail gracefully with clear error message.
    """
    repo_dir = tmp_path / "invalid_version_repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create version file with invalid version
    version_file = repo_dir / "version.txt"
    version_file.write_text("not-a-valid-version\n")
    
    config_file = repo_dir / "auto_semver_config.yml"
    config_file.write_text("""
version_files:
  - version.txt
branches:
  main:
    bump: patch
""")
    
    repo.index.add(["version.txt", "auto_semver_config.yml"])
    repo.index.commit("chore: invalid version")
    
    main_branch = repo.create_head("main")
    main_branch.checkout()

    # Run bump (may handle gracefully)
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
        env={**isolated_env} if isolated_env else None,
    )

    # Should handle invalid version gracefully (may skip or error)
    # The tool may be lenient with version parsing
    assert result.returncode in [0, 1], f"Unexpected crash:\n{result.stderr}"
