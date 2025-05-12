"""
Entry point for the semantic version automation tool.

This script performs version bumping, changelog updating, git operations, and GitHub PR creation
based on CI/CD context and branch strategy (e.g., single-branch release workflows).
"""

import argparse

from auto_semver.gh import GitHubEvent
from auto_semver.changelog import ChangelogManager
from auto_semver.config import Config
from auto_semver.git import GitOps
from auto_semver.utils import setup_logger
from auto_semver.semver import SemverLock
from auto_semver.semver import Version
from auto_semver.semver import VersionFileUpdater


def main() -> None:
    """
    Automating semantic versioning and release processes.

    This script performs the following tasks:
        1. Parse CLI args
        2. Setup logging/config
        3. Determine branch + SHA from GitHub if missing
        4. Bump version + set suffix
        5. Update version files
        6. Create release branch + commit changes
        7. Update changelog
        8. Push branch + open PR

    Command-line Arguments:
    - `--branch-name`: Name of the branch triggering the release process.
    - `--target-branch`: Target branch for the release pull request.
    - `--github-token`: GitHub token for authentication.
    - `--repo-full-name`: Full name of the repository (e.g., `owner/repo`).
    - `--debug`: Enables debug logging if specified.

    Raises:
    - FileNotFoundError: If `version.txt` is not found and no start version is configured.
    - Other exceptions may be raised by Git operations or API calls.

    Note:
    - Ensure that the `version.txt` file exists or a start version is configured in the `Config` class.
    - The `CHANGELOG.md` file is updated with recent commits, and its handling should be
      encapsulated in a dedicated class in the future.

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--branch-name", required=True, type=str)
    parser.add_argument("--target-branch", required=True, type=str)
    parser.add_argument("--github-token", required=True, type=str)
    parser.add_argument("--repo-full-name", required=True, type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logger = setup_logger(args.debug)
    config = Config() # TODO: make it a data class
    changelog = ChangelogManager.from_config(config)
    gitops = GitOps(ensure_safe=True)

    current_branch: str = args.branch_name
    current_commit_sha: str = ""
    target_branch: str = args.target_branch

    # Fallback to GitHub event context if no branch is passed
    if not current_branch:
        logger.info("Branch name not provided. Extracting from GITHUB_EVENT_PATH...")
        event = GitHubEvent()
        current_branch = event.get_source_branch_name()
        current_commit_sha = event.get_source_commit_sha()

    if not target_branch:
        logger.info("Target branch not provided. Extracting from GITHUB_EVENT_PATH...")
        target_branch = event.get_target_branch_name()

    logger.info(f"Branch name: {current_branch}")

    version = gitops.get_highest_release_lock_version_for_target(target_branch)

    if not version:
        try:
            with open("version.txt") as f:
                current_version_line = f.read().strip()
                version = Version.parse(current_version_line)
        except FileNotFoundError:
            version = config.get_start_version()

    logger.info(f"Current version: {version}")

    version.bump(branch_name=current_branch)
    suffix: str = config.get_suffix(args.target_branch)
    version.set_suffix(suffix=suffix)
    new_version: str = str(version)

    logger.info(f"New version: {new_version}")

    for path in config.get_files_to_update():
        VersionFileUpdater(file_path=path, version=version).update()

    release_branch_name = f"release/{new_version}"
    branch_strategy = config.get_branch_strategy()

    gitops.create_branch(branch_name=release_branch_name, force=(branch_strategy == "single"))
    gitops.add(config.get_files_to_update())

    # Update the lockfile with the new version
    lockfile = SemverLock(
        version=version,
        source_branch=current_branch,
        target_branch=target_branch,
    )
    lockfile.save_to_file()
    gitops.add([lockfile.path])

    commit_messages = gitops.get_recent_commits(current_commit_sha)
    changelog.update(version=new_version, messages=commit_messages)

    gitops.add([changelog.path])  # TODO: make sure the changelog is a class and hold this param

    gitops.commit(f"Release {new_version}")
    gitops.push(branch_name=release_branch_name, force=(branch_strategy == "single"))

    # Get commits for changelog

    if branch_strategy == "single":
        logger.info("Closing old release PRs (branch_strategy=single)...")
        gitops.close_old_release_prs(
            github_token=args.github_token,
            repo_full_name=args.repo_full_name,
            target_branch=args.target_branch,
            labels=config.get_pr_labels(),
        )

    gitops.create_pr(
        repo_full_name=args.repo_full_name,
        title=f"Release {new_version}",
        source=release_branch_name,
        target=args.target_branch,
        github_token=args.github_token,
        label="semver-bump",
    )


if __name__ == "__main__":
    main()
