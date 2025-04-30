import argparse
import re

from src.logger import setup_logger
from src.config import Config
from src.versioning import VersionManager
from src.changelog import update_changelog
from src.gitops import GitOps
from src.actionops import extract_branch_from_event
from src.version import Version
from src.version_updater import update_version_in_file



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch-name', required=True, type=str)
    parser.add_argument('--target-branch', required=True, type=str)
    parser.add_argument('--github-token', required=True, type=str)
    parser.add_argument('--repo-full-name', required=True, type=str)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    logger = setup_logger(args.debug)
    config = Config()
    gitops = GitOps()

    # Extract branch name if not passed
    branch_name = args.branch_name
    if not branch_name:
        logger.info("Branch name not provided. Extracting from GITHUB_EVENT_PATH...")
        branch_name = extract_branch_from_event()

    logger.info(f"Branch name: {branch_name}")

    try:
        with open('version.txt', 'r') as f:
            current_version_line = f.read().strip()
    except FileNotFoundError:
        current_version_line = config.get_start_version()

    logger.info(f"Current version: {current_version_line}")

    version_obj: Version = Version.parse(current_version_line)
    version_obj.bump(branch_name)
    suffix: str = config.get_suffix(args.target_branch)
    version_obj.set_suffix(suffix)
    new_version: str = str(version_obj)

    logger.info(f"New version: {new_version}")

    for file_path in config.get_files_to_update():
        update_version_in_file(file_path, version_obj)

    branch_strategy: str = config.get_branch_strategy()
    branch_name: str = f"release/{new_version}"

    if branch_strategy == "single":
        logger.info("Closing old release PRs (branch_strategy=single)...")
        gitops.close_old_release_prs(args.github_token, args.repo_full_name)

    gitops.create_branch(branch_name, overwrite=(branch_strategy == "single"))
    gitops.add(config.get_files_to_update())
    
    commit_messages = gitops.get_recent_commits(branch_name)
    update_changelog(new_version, commit_messages)
    gitops.add('CHANGELOG.md') #TODO: make sure the changelog is a class and hold this param

    gitops.commit(f"Release {new_version}")
    gitops.push(branch_name)

    # Get commits for changelog

    gitops.create_pr(args.github_token, args.repo_full_name, f"Release {new_version}", branch_name, args.target_branch)

if __name__ == "__main__":
    main()
