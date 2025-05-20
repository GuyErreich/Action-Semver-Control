"""
Handles the finalization step of the auto-semver workflow.

This script is responsible for verifying that the merged PR is
an auto-generated release PR and, if so, creating and pushing a Git tag.
"""


import logging

from auto_semver.config import Config
from auto_semver.gh import GitHubEvent
from auto_semver.git import GitOps
from auto_semver.semver import SemverLock

logger = logging.getLogger(__package__)

def run(*, gitops: GitOps, event: GitHubEvent, config: Config) -> None:
    """
    Finalize the release process by tagging the merged version.

    Args:
        gitops (GitOps): Git operations handler.
        event (GitHubEvent): GitHub event wrapper for PR metadata.
        config (Config): Loaded configuration object.

    """

    target_branch: str = event.get_target_branch_name()
    version = SemverLock.load_from_file().version
    allowed_targets = list(config.data.suffixes.keys())

    logger.info("Tagging branch")

    if target_branch not in allowed_targets:
        logger.debug(f"Target branch '{target_branch}' not allowed for tagging. Allowed: {allowed_targets}")
        raise ValueError(f"Tagging not allowed on branch '{target_branch}'.")

    tag = gitops.tag(tag=str(version), branch=target_branch)
    gitops.push(tag)