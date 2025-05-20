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

    version = gitops.get_highest_release_lock_version_for_target(target_branch)

    if not version:
        try:
            with open("version.txt") as f:
                current_version_line = f.read().strip()
                version = Version.parse(current_version_line)
        except FileNotFoundError:
            version = config.data.start_version

    logger.info(f"Current version: {version}")

    version.bump(branch_name=current_branch)
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
            version=version,
            source_branch=current_branch,
            target_branch=target_branch
        )

    #TODO: maybe find away to catch correct base sha of the PR rather then using current one
    latest_commit_sha = lockfile.target_base_sha or event.get_merged_commit_sha()

    commit_messages = gitops.get_recent_commits(latest_commit_sha)
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
        messages=commit_messages
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