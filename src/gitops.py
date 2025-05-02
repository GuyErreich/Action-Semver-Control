import logging
import time

import requests
from git import Commit, Head, Remote, Repo
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.GithubException import GithubException

logger = logging.getLogger(__name__)


class GitOps:
    def __init__(self, repo_path: str = ".") -> None:
        self.repo = Repo(repo_path)
        self.__ensure_git_safe_directory()

    def create_branch(self, branch_name: str, overwrite: bool = False) -> None:
        if branch_name in self.repo.heads:
            if not overwrite:
                logger.info(f"Branch '{branch_name}' already exists and overwrite is False.")
                return
        
            logger.info(f"Deleting existing branch '{branch_name}'")
            existing_branch: Head = self.repo.heads[branch_name]
            existing_branch.delete(self.repo, force=True)

        logger.info(f"Creating new branch '{branch_name}'")
        new_branch: Head = self.repo.create_head(branch_name)
        new_branch.checkout()

    def push(self, branch_name: str, remote_name: str = "origin", overwrite: bool = False) -> None:
        """
        Push the specified branch to the remote repository.

        Args:
            branch_name (str): The name of the branch to push.
            remote_name (str): The name of the remote repository. Defaults to "origin".
            overwrite (bool): Whether to force push with lease. Defaults to False.

        Raises:
            Exception: If the push operation fails, the exception is logged and re-raised.

        Logs:
            - Logs an info message indicating the branch being pushed and the remote.
            - Logs a debug message if the push is successful.
            - Logs an error message if the push fails.

        """
        try:
            logger.info(f"Pushing branch '{branch_name}' to remote '{remote_name}' with overwrite={overwrite}.")
            remote: Remote = self.repo.remote(remote_name)
            push_info = remote.push(branch_name, force=overwrite)
            logger.debug(f"Push result: {push_info}")
        except Exception as e:
            logger.error(f"Failed to push branch '{branch_name}' to remote '{remote_name}': {e}")
            raise

    def create_pr(self, repo_full_name: str, title: str, head: str, base: str, github_token: str, label: str | None = None) -> int:
        logger.debug("Creating PR with the following parameters:")
        logger.debug(f"  Repo: {repo_full_name}")
        logger.debug(f"  Title: {title}")
        logger.debug(f"  Head (source): {head}")
        logger.debug(f"  Base (target): {base}")

        gh = Github(github_token)
        try:
            repo: Repository = gh.get_repo(repo_full_name)

            # Check for existing PRs
            for pr in repo.get_pulls(state="open"):
                if pr.head.ref == head and pr.base.ref == base:
                    logger.warning(f"PR already exists for branch '{head}' → '{base}', skipping creation.")
                    return pr.number

            new_pr: PullRequest = repo.create_pull(title=title, body="Auto-created PR by auto-semver.", head=head, base=base)
            if label:
                try:
                    new_pr.add_to_labels(label)
                    logger.info(f"Label '{label}' added to PR #{new_pr.number}.")
                except GithubException as e:
                    logger.error(f"Failed to add label '{label}' to PR #{new_pr.number}: {e}")
                    raise
            logger.info(f"PR created successfully: #{new_pr.number}")
            return new_pr.number

        except GithubException as e:
            logger.error(f"GitHub API error during PR creation: {e}")
            raise

    def close_existing_prs_for_branch(self, repo_full_name: str, branch_name: str ,github_token: str) -> None:
        logger.info(f"Checking for existing PRs for head branch: {branch_name}")
        gh = Github(github_token)
        try:
            repo: Repository = gh.get_repo(repo_full_name)
            open_prs = repo.get_pulls(state="open")

            for pr in open_prs:
                if pr.head.ref == branch_name:
                    logger.info(f"Closing PR #{pr.number} from branch '{branch_name}'")
                    pr.edit(state="closed")
        except GithubException as e:
            logger.error(f"GitHub API error while closing PRs: {e}")
            raise

    def get_recent_commits(self, base_branch: str) -> list[str]:
        """Get commit messages between base_branch and HEAD."""
        
        commits: list[Commit] = []
        message: str = ""
        commit_messages: list[str] = []
        
        logger.info(f"Fetching recent commits between {base_branch} and HEAD.")

        try:
            commits = list(self.repo.iter_commits(f"{base_branch}..HEAD"))

            for commit in reversed(commits):
                message = str(commit.message.strip())
                commit_messages.append(message)
                logger.debug(f"Commit message: {message}")
                
            logger.debug(f"Found {len(commit_messages)} commits.")

            return commit_messages
        except Exception as e:
            logger.error(f"Failed to fetch recent commits: {e}")
            raise

    def __ensure_git_safe_directory(self) -> None:
        path = self.repo.working_tree_dir
        git_config = self.repo.config_writer(config_level="global")

        try:
            safe_dirs = [str(git_config.get_value("safe", "directory"))]
        except Exception:
            safe_dirs = []

        if path not in safe_dirs:
            git_config.set_value("safe", "directory", path)
            git_config.release()

    def add(self, files: list[str]) -> None:
        """
        Add the specified files to the git index (staging area).

        Args:
            files (list[str]): A list of file paths to be added to the git index.

        Raises:
            Exception: If adding a file to the git index fails, an exception is raised with the error details.

        Logs:
            - Logs an info message listing the files to be added.
            - Logs a warning if the repository is not dirty (no changes staged or committed).
            - Logs a debug message if the repository has staged or committed changes.
            - Logs a debug message for each file successfully added to the git index.
            - Logs an error message if adding a file to the git index fails.

        """
        logger.info(f"Adding files: {files}")

        if not self.repo.is_dirty(untracked_files=True):
            logger.warning("Repo is not dirty — no changes staged or committed.")
        else:
            logger.debug("Repo has staged/committed changes.")

        for file_path in files:
            try:
                self.repo.index.add([file_path])
                logger.debug(f"Added {file_path} to git.")
            except Exception as e:
                logger.error(f"Failed to add {file_path} to git: {e}")
                raise

    # TODO: make it support description
    def commit(self, message: str = "") -> None:
        """
        Commit the current changes in the repository with the provided commit message.

        Args:
            message (str): The commit message to use. Defaults to an empty string.

        Raises:
            Exception: If the commit operation fails, the exception is logged and re-raised.

        Logs:
            Logs a success message if the commit is successful.
            Logs an error message if the commit fails.

        """
        try:
            self.repo.index.commit(message)
            logger.info("Committed changes.")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            raise
