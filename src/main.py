import argparse
import re
from src.utils.git import ensure_git_safe_directory
from src.logger import setup_logger
from src.config import Config
from src.versioning import VersionManager
from src.changelog import update_changelog
from src.gitops import GitOps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch-name', required=True, type=str)
    parser.add_argument('--target-branch', required=True, type=str)
    parser.add_argument('--github-token', required=True, type=str)
    parser.add_argument('--repo-full-name', required=True, type=str)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    ensure_git_safe_directory("/github/workspace")

    logger = setup_logger(args.debug)
    config = Config()
    gitops = GitOps()

    try:
        with open('version.txt', 'r') as f:
            current_version: str = f.read().strip()
    except FileNotFoundError:
        current_version = config.get_start_version()

    logger.info(f"Current version: {current_version}")

    bump_type: str = VersionManager.detect_bump_type(args.branch_name)
    suffix: str = config.get_suffix(args.target_branch)
    vm = VersionManager(current_version)
    new_version: str = vm.bump(bump_type, suffix)

    logger.info(f"New version: {new_version}")

    for file_path in config.get_files_to_update():
        try:
            with open(file_path, 'r+') as f:
                content = f.read()
                content = re.sub(r"version:\s*.*", f"version: {new_version}", content)
                f.seek(0)
                f.write(content)
                f.truncate()
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")

    branch_strategy: str = config.get_branch_strategy()
    branch_name: str = f"release/{new_version}"

    if branch_strategy == "single":
        logger.info("Closing old release PRs (branch_strategy=single)...")
        gitops.close_old_release_prs(args.github_token, args.repo_full_name)

    gitops.create_branch(branch_name, overwrite=(branch_strategy == "single"))
    gitops.push_branch(branch_name)

    # Get commits for changelog
    commit_messages = gitops.get_recent_commits(args.target_branch)
    update_changelog(new_version, commit_messages)

    gitops.create_pr(args.github_token, args.repo_full_name, f"Release {new_version}", branch_name, args.target_branch)

if __name__ == "__main__":
    main()
