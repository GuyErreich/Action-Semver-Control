"""
CLI command for manually promoting versions between branches.

This command allows users to create promotion PRs manually, with validation
against the configured promotion rules.
"""

import logging

from auto_semver.config import Config
from auto_semver.git import GitOps

logger = logging.getLogger(__name__)


# Think about moving this as a function in finalize.py since it's similar to auto-promotion PRs
def run(
    *, gitops: GitOps, config: Config, github_token: str, from_branch: str, to_branch: str
) -> None:
    """
    Create a promotion PR from one branch to another.

    Args:
        gitops (GitOps): Git operations handler.
        config (Config): Loaded configuration object.
        github_token (str): GitHub token for creating PRs.
        from_branch (str): Source branch name.
        to_branch (str): Target branch name.

    Raises:
        ValueError: If promotion is not allowed by configuration.
    """
    logger.info(f"Initiating manual promotion: {from_branch} → {to_branch}")

    # Validate promotion is allowed
    promotion_rule = config.data.validate_promotion(
        from_branch=from_branch,
        to_branch=to_branch,
        require_auto_promote=False,  # Manual promotions don't require auto_promote=True
    )

    logger.info(f"Promotion validated: {promotion_rule.from_branch} → {promotion_rule.to_branch}")

    # Get the latest tag/version from the source branch
    try:
        version = gitops.get_highest_release_lock_version_for_target(from_branch)
        if not version:
            raise ValueError(
                f"No version found for branch '{from_branch}'. Ensure the branch is tagged."
            )
    except Exception as e:
        raise ValueError(f"Failed to get version from branch '{from_branch}': {e}") from e

    logger.info(f"Found version {version} on branch '{from_branch}'")

    # Create promotion PR
    pr_title = f"🚀 Promote {version} from {from_branch} to {to_branch}"
    pr_body = (
        f"This is a manual promotion PR to promote version `{version}` "
        f"from `{from_branch}` to `{to_branch}`.\n\n"
        f"**Promotion**: `{from_branch}` → `{to_branch}`\n"
        f"**Version**: `{version}`\n"
        f"**Created by**: Manual promotion command\n"
        f"**Auto-promotion enabled**: {promotion_rule.auto_promote}\n\n"
        "Merging this PR will trigger the semver workflow to create a release "
        f"PR with the appropriate suffix for the `{to_branch}` branch."
    )

    try:
        gitops.create_pr(
            title=pr_title,
            body=pr_body,
            source=from_branch,
            target=to_branch,
            github_token=github_token,
            labels=["manual-promotion", "semver"],
        )

        logger.info(f"✅ Promotion PR created successfully: {from_branch} → {to_branch}")
        logger.info(f"This will promote version {version} to {to_branch}")

    except Exception as e:
        raise ValueError(f"Failed to create promotion PR: {e}") from e
