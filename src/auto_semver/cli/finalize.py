"""
Handles the finalization step of the auto-semver workflow.

This script is responsible for verifying that the merged PR is
an auto-generated release PR and, if so, creating and pushing a Git tag.
After tagging, it checks for auto-promotion rules and creates promotion PRs automatically.
"""

import logging

from auto_semver.config import Config
from auto_semver.gh import GitHubEvent
from auto_semver.git import GitOps
from auto_semver.semver import SemverLock

logger = logging.getLogger(__package__)


def create_and_push_tag(*, gitops: GitOps, event: GitHubEvent, config: Config) -> tuple[str, str]:
    """
    Create and push a Git tag for the finalized version.

    Args:
        gitops (GitOps): Git operations handler.
        event (GitHubEvent): GitHub event wrapper for PR metadata.
        config (Config): Loaded configuration object.

    Returns:
        tuple[str, str]: A tuple of (target_branch, version) that was tagged.

    Raises:
        ValueError: If tagging is not allowed on the target branch.
    """
    target_branch: str = event.get_target_branch_name()
    version = SemverLock.load_from_file().version
    allowed_targets = list(config.data.suffixes.keys())

    logger.info("Tagging branch")

    if target_branch not in allowed_targets:
        logger.debug(
            f"Target branch '{target_branch}' not allowed for tagging. Allowed: {allowed_targets}"
        )
        raise ValueError(f"Tagging not allowed on branch '{target_branch}'.")

    tag = gitops.tag(tag=str(version), branch=target_branch)
    gitops.push(branch_name=tag)

    return target_branch, str(version)


def create_auto_promotion_prs(
    *,
    gitops: GitOps,
    event: GitHubEvent,
    config: Config,
    target_branch: str,
    version: str,
    github_token: str | None = None,
) -> None:
    """
    Create auto-promotion PRs based on configuration rules.

    Args:
        gitops (GitOps): Git operations handler.
        event (GitHubEvent): GitHub event wrapper for PR metadata.
        config (Config): Loaded configuration object.
        target_branch (str): The branch that was just tagged.
        version (str): The version that was just tagged.
        github_token (str, optional): GitHub token for creating promotion PRs.
    """
    logger.info(f"Successfully tagged {target_branch} with {version}")

    # Check for auto-promotion opportunities
    auto_targets = config.data.get_auto_promotion_targets(from_branch=target_branch)

    if not auto_targets:
        logger.info(f"No auto-promotion rules found for branch '{target_branch}'")
        return

    if not github_token:
        logger.warning(
            f"Auto-promotion targets found ({auto_targets}) but no GitHub token provided. "
            "Auto-promotion skipped."
        )
        return

    for to_branch in auto_targets:
        logger.info(f"Creating auto-promotion PR: {target_branch} → {to_branch}")

        try:
            # Create promotion PR using GitOps
            pr_title = f"🚀 Promote {version} from {target_branch} to {to_branch}"
            pr_body = (
                f"This is an automated promotion PR created after tagging "
                f"`{target_branch}` with version `{version}`.\n\n"
                f"**Promotion**: `{target_branch}` → `{to_branch}`\n"
                f"**Version**: `{version}`\n"
                f"**Auto-created**: This PR was automatically created due to "
                f"`auto_promote: true` configuration.\n\n"
                "Merging this PR will trigger the next stage of the release workflow."
            )

            gitops.create_pr(
                title=pr_title,
                body=pr_body,
                source=target_branch,
                target=to_branch,
                github_token=github_token,
                labels=["auto-promotion", "semver"],
            )

            logger.info(f"✅ Auto-promotion PR created: {target_branch} → {to_branch}")

        except Exception as e:
            logger.error(
                f"❌ Failed to create auto-promotion PR {target_branch} → {to_branch}: {e}"
            )
            # Continue with other auto-promotions even if one fails
            continue


def run(
    *, gitops: GitOps, event: GitHubEvent, config: Config, github_token: str | None = None
) -> None:
    """
    Finalize the release process by tagging the merged version.

    After tagging, check for auto-promotion rules and create promotion PRs if configured.

    Args:
        gitops (GitOps): Git operations handler.
        event (GitHubEvent): GitHub event wrapper for PR metadata.
        config (Config): Loaded configuration object.
        github_token (str, optional): GitHub token for creating promotion PRs.

    """
    # Step 1: Create and push the tag
    target_branch, version = create_and_push_tag(gitops=gitops, event=event, config=config)

    # Step 2: Create auto-promotion PRs if configured
    create_auto_promotion_prs(
        gitops=gitops,
        event=event,
        config=config,
        target_branch=target_branch,
        version=version,
        github_token=github_token,
    )
