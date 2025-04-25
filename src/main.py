#!/usr/bin/env python3

import argparse
import logging

from git import GitCommandError, Repo

from .changelog.write import prepend_changelog
from .fileops.update import update_version_file
from .gitops.pr import create_or_update_pr
from .gitops.push import push_with_retry
from .utils.logger import setup_logging
from .versioning.bump import bump_version, extract_version, parse_bump


def main():
    parser = argparse.ArgumentParser(description="Auto-versioning GitHub Action")
    parser.add_argument(
        "--version-files",
        required=True,
        help="Comma-separated list of files to update with new version",
    )
    parser.add_argument(
        "--changelog-file",
        default="CHANGELOG.md",
        help="File to update or create for changelog",
    )
    parser.add_argument(
        "--default-bump",
        default="patch",
        choices=["major", "minor", "patch"],
        help="Default version bump if no prefix match",
    )
    parser.add_argument("--base-branch", default="dev", help="PR target branch")
    parser.add_argument(
        "--suffix", default="", help="Optional version suffix like 'dev' or 'staging'"
    )
    parser.add_argument("--github-token", required=True, help="GitHub token with repo access")
    parser.add_argument("--repo", required=True, help="GitHub repository in the form 'owner/repo'")
    parser.add_argument("--branch", required=True, help="Current Git branch name")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(debug=args.debug)
    logger = logging.getLogger(__name__)
    logger.info("Starting semver-pr action")

    if args.branch != args.base_branch:
        logger.info("Not on base branch. Skipping release PR generation.")
        return

    version_files = [f.strip() for f in args.version_files.split(",")]
    bump_type = parse_bump(args.branch, args.default_bump)
    logger.info(f"Branch: {args.branch}, bump type: {bump_type}")

    updated = False
    current_version = None
    for version_file in version_files:
        with open(version_file) as f:
            content = f.read()
        current_version = extract_version(content)
        if not current_version:
            logger.warning(f"No version found in {version_file}, skipping")
            continue
        new_version = bump_version(current_version, bump_type, args.suffix or args.branch)
        logger.info(f"Bumping version in {version_file}: {current_version} -> {new_version}")
        update_version_file(version_file, new_version)
        updated = True

    if not updated:
        logger.error("No version files were updated")
        raise SystemExit(1)

    release_branch = f"release/{new_version}"
    repo = Repo(".")
    try:
        repo.git.checkout(b=release_branch)
    except GitCommandError as e:
        logger.error(f"Failed to create branch: {e}")
        raise

    repo.git.config("user.name", "github-actions")
    repo.git.config("user.email", "github-actions@github.com")
    repo.index.add(version_files + [args.changelog_file])
    repo.index.commit(f"chore: release {new_version}")
    push_with_retry(repo.remote(name="origin"), release_branch)

    prepend_changelog(new_version, args.branch, args.changelog_file)
    create_or_update_pr(
        token=args.github_token,
        repo=args.repo,
        branch=release_branch,
        base_branch=args.base_branch,
        title=f"chore: release {new_version}",
        body=f"This PR updates the version to {new_version} based on `{args.branch}`.",
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Action failed: {e}")
        raise
