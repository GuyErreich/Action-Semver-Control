"""Version bump CLI operations for auto_semver."""

import datetime
import logging

from auto_semver.changelog.manager import ChangelogManager
from auto_semver.config import Config
from auto_semver.gh import GitHubEvent
from auto_semver.git import GitOps
from auto_semver.semver import Version
from auto_semver.semver.lock import SemverLock
from auto_semver.semver.updater import VersionFileUpdater

logger = logging.getLogger(__package__)


def _detect_tag_source_branch(*, version: Version, config: Config) -> str | None:
    """
    Detect which branch a version tag belongs to based on its suffix.

    This function maps the version's suffix back to the source branch using
    the suffixes configuration.

    Args:
        version: The version object with a suffix
        config: The configuration containing suffix mappings

    Returns:
        The branch name that corresponds to the version's suffix, or None if not found
    """
    # Normalize suffix - treat None as empty string for comparison
    target_suffix = version.suffix or ""

    # Find branch that matches the version's suffix
    for branch, suffix in config.data.suffixes.items():
        if suffix == target_suffix:
            return branch

    return None


def _is_tag_promotion_scenario(*, version: Version, target_branch: str, config: Config) -> bool:
    """
    Check if the current scenario represents a tag promotion.

    A tag promotion scenario occurs when:
    1. We have an existing version with a suffix that maps to a source branch
    2. There's a promotion rule from that source branch to the target branch
    3. This should result in suffix change only, no version bump

    Args:
        version: The current version object
        target_branch: The target branch of the PR
        config: The configuration containing promotion rules and suffixes

    Returns:
        True if this is a tag promotion scenario, False otherwise

    Raises:
        ValueError: If the version has a suffix that doesn't match any configured branch
    """
    # Detect which branch this version tag currently belongs to
    source_branch = _detect_tag_source_branch(version=version, config=config)

    if source_branch is None:
        # If we can't find the source branch, the version's suffix doesn't match
        # any configured branch suffix - this is always a configuration error
        suffix_display = f"'{version.suffix}'" if version.suffix else "None (empty)"
        error_msg = (
            f"Version {version} has suffix {suffix_display} that doesn't match any "
            f"configured branch suffix in: {list(config.data.suffixes.values())}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check if there's a promotion rule from source to target
    for rule in config.data.promotions:
        if rule.from_branch == source_branch and rule.to_branch == target_branch:
            logger.info(f"Tag promotion detected: {version} from {source_branch} → {target_branch}")
            return True

    logger.debug(f"No promotion rule found from {source_branch} → {target_branch}")
    return False


def run(*, gitops: GitOps, event: GitHubEvent, config: Config, github_token: str) -> None:
    """
    Run the bump workflow.

    Args:
        gitops (GitOps): GitOps object.
        event (GitHubEvent): GitHubEvent object.
        config (Config): Config object.
        github_token (str): A token for github to generate a new PR.

    """
    changelog = ChangelogManager.from_config(config)

    # current_branch: str = args.branch_name
    # current_commit_sha: str = ""
    # target_branch: str = args.target_branch

    # Fallback to GitHub event context if no branch is passed
    # if not current_branch:
    # logger.info("Branch name not provided. Extracting from GITHUB_EVENT_PATH...")
    current_branch: str = event.get_source_branch_name()
    # current_commit_sha: str = event.get_source_commit_sha()

    # if not target_branch:
    # logger.info("Target branch not provided. Extracting from GITHUB_EVENT_PATH...")
    target_branch: str = event.get_target_branch_name()
    repo_full_name: str = event.get_repository()

    logger.info(f"Branch name: {current_branch}")

    # Get current version first to check for tag promotion
    version = gitops.get_highest_release_lock_version_for_target(target_branch)

    if not version:
        try:
            with open("version.txt") as f:
                current_version_line = f.read().strip()
                version = Version.parse(current_version_line)
        except FileNotFoundError:
            version = config.data.start_version

    # Check if this is a tag promotion scenario
    is_tag_promotion = _is_tag_promotion_scenario(
        version=version, target_branch=target_branch, config=config
    )

    if is_tag_promotion:
        logger.info(f"Detected tag promotion: {version} → {target_branch}")
    else:
        logger.info(f"Standard bump workflow: {current_branch} → {target_branch}")

    logger.info(f"Current version: {version}")

    # Only bump version if this is NOT a tag promotion
    if not is_tag_promotion:
        version.bump(branch_name=current_branch)
    else:
        logger.info("Skipping version bump for tag promotion - preserving version numbers")

    suffix: str = config.data.suffixes[target_branch]
    version.set_suffix(suffix=suffix)
    new_version: str = str(version)

    logger.info(f"New version: {new_version}")

    files_to_update: list[str] = config.data.version_files

    for path in files_to_update:
        VersionFileUpdater(file_path=path, version=version).update()

    release_branch_name = f"release/{new_version}"
    branch_strategy = config.data.branch_strategy

    # Update the lockfile with the new version
    try:
        lockfile = SemverLock.load_from_file()
        lockfile.version = version
    except FileNotFoundError:
        lockfile = SemverLock(
            version=version, source_branch=current_branch, target_branch=target_branch
        )

    # TODO: maybe find away to catch correct base sha of the PR rather then using current one
    latest_commit_sha = lockfile.target_base_sha or event.get_merged_commit_sha()

    commit_messages = gitops.get_recent_commits(latest_commit_sha, config=config)
    changelog.update(version=new_version, messages=commit_messages)

    lockfile.target_base_sha = event.get_merged_commit_sha()
    lockfile.save_to_file()

    gitops.create_branch(branch_name=release_branch_name, force=(branch_strategy == "single"))
    gitops.add(files_to_update)
    gitops.add([lockfile.path])
    gitops.add([changelog.path])
    gitops.commit(f"Release {new_version}")
    gitops.push(branch_name=release_branch_name, force=(branch_strategy == "single"))

    # Get commits for changelog

    if branch_strategy == "single":
        logger.info("Closing old release PRs (branch_strategy=single)...")
        gitops.close_old_release_prs(
            github_token=github_token,
            repo_full_name=repo_full_name,
            target_branch=target_branch,
            labels=config.data.pull_request.labels,
        )

    pr_body: str = config.data.pull_request.render_body(
        version=new_version,
        date=datetime.date.today().strftime("%d-%m-%Y"),
        messages=commit_messages,
    )

    pr_title: str = config.data.pull_request.render_title(version=new_version)

    gitops.create_pr(
        repo_full_name=repo_full_name,
        title=pr_title,
        body=pr_body,
        source=release_branch_name,
        target=target_branch,
        github_token=github_token,
        labels=config.data.pull_request.labels,
    )
