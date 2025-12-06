"""
Entry point for the semantic version automation tool.

This script performs version bumping, changelog updating, git operations, and GitHub PR creation
based on CI/CD context and branch strategy (e.g., single-branch release workflows).
"""

import argparse
import logging
import sys

from auto_semver.cli import bump, finalize, promote
from auto_semver.cli.utils import is_finalized
from auto_semver.config import Config
from auto_semver.gh import GitHubEvent
from auto_semver.git import GitOps
from auto_semver.utils import setup_logger

logger = logging.getLogger(__name__)


# TODO: Research about click package for CLI
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
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--github-token", required=True, type=str)
        parser.add_argument("--debug", action="store_true")

        subparsers = parser.add_subparsers(dest="command")

        # Promote command
        promote_parser = subparsers.add_parser("promote", help="Manually promote version between branches")
        promote_parser.add_argument("--from-branch", required=True, help="Source branch")
        promote_parser.add_argument("--to-branch", required=True, help="Target branch")
        promote_parser.add_argument(
            "--dry-run", action="store_true", help="Validate promotion without creating PR"
        )

        args = parser.parse_args()

        setup_logger(args.debug)
        config = Config()
        gitops = GitOps(ensure_safe=True)

        if args.command == "promote":
            promote.run(
                gitops=gitops,
                config=config,
                github_token=args.github_token,
                from_branch=args.from_branch,
                to_branch=args.to_branch,
                dry_run=args.dry_run,
            )
            return

        event = GitHubEvent()

        if is_finalized(config=config, event=event):
            finalize.run(gitops=gitops, event=event, config=config, github_token=args.github_token)
        else:
            bump.run(gitops=gitops, event=event, config=config, github_token=args.github_token)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.debug:
            logger.exception("Full traceback:")
        sys.exit(1)
