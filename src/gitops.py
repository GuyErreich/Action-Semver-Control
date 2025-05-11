"""
GitOps utilities for Git and GitHub operations in Auto-Semver pipelines.

This module provides functionality to manage Git branches, stage and commit files,
push branches, retrieve commit history, and handle GitHub pull requests — all through
Python APIs provided by `GitPython` and `PyGithub`.

Typical usage example::

    gitops = GitOps()
    gitops.create_branch(branch_name="release/v1.0.0", overwrite=True)
    gitops.add(files=["version.txt"])
    gitops.commit(message="Bump version")
    gitops.push(branch_name="release/v1.0.0")
    gitops.create_pr(
        github_token="...",
        repo_full_name="owner/repo",
        title="Release v1.0.0",
        head="release/v1.0.0",
        base="main"
    )
"""

import logging

from git import Commit, GitCommandError, Head, Repo
from git.remote import Remote
from github import Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
import yaml

from semver_lock import SemverLock
from src.version import Version

logger = logging.getLogger(__name__)


class GitOps:

    """
    Encapsulates Git and GitHub operations such as branch handling, commits, pushing, and pull requests.

    Attributes:
        repo (Repo): The Git repository object from GitPython.
    """

    def __init__(self, *, repo_path: str = ".", ensure_safe: bool = False) -> None:
        """
        Initialize GitOps for the given repository path.

        Args:
            repo_path (str): Path to the local Git repository (default: current directory).
            ensure_safe (bool): If True, ensures the repository is marked as a safe directory in Git config.

        """

        self.repo = Repo(path=repo_path)
        if ensure_safe:
            self.__ensure_git_safe_directory()

    def __ensure_git_safe_directory(self) -> None:
        """
        Ensure the repository path is listed as a safe Git directory in the global config.

        This is important for CI environments that may require explicitly trusting the repo.
        """

        logger.info("Ensuring the repository is marked as a safe directory.")

        safe_key: str = "safe"
        directory_key: str = "directory"

        path: str = str(self.repo.working_tree_dir)

        logger.debug(f"Working tree directory: {path}")

        git_config = self.repo.config_writer(config_level="global")

        logger.debug(f"Checking if {path} is in safe directories.")

        raw_values = git_config.get_values(section=safe_key, option=directory_key, default="")
        safe_dirs: list[str] = [v for v in raw_values if isinstance(v, str)]

        if path not in safe_dirs:
            logger.debug(f"{path} is not in safe directories.")
            logger.info(f"Adding {path} to safe directories.")

            git_config.set_value(section=safe_key, option=directory_key, value=path)

            git_config.release()

    def _get_github_repo(self, *, github_token: str, repo_full_name: str) -> Repository:
        return Github(github_token).get_repo(repo_full_name)

    def create_branch(self, *, branch_name: str, force: bool = False) -> None:
        """
        Create a new Git branch or overwrites an existing one if specified.

        Args:
            branch_name (str): The name of the branch to create.
            force (bool): If True, overwrites the existing branch with the same name.
                Defaults to False, which prevents overwriting.

        """

        if branch_name in self.repo.heads:
            if not force:
                logger.info(f"Branch '{branch_name}' already exists and force is False.")
                return

            logger.info(f"Deleting existing branch '{branch_name}'")

            existing_branch: Head = self.repo.heads[branch_name]
            existing_branch.delete(repo=self.repo, force=True)

        logger.info(f"Creating new branch '{branch_name}'")

        new_branch: Head = self.repo.create_head(path=branch_name)
        new_branch.checkout()

    def add(self, files: list[str]) -> None:
        """
        Stage the specified files for commit.

        Args:
            files (list[str]): List of file paths to add to the Git index.

        """

        logger.info(f"Adding files: {files}")

        if not self.repo.is_dirty(untracked_files=True):
            logger.warning("Repo is not dirty — no changes staged or committed.")
        else:
            logger.debug("Repo has staged/committed changes.")

        for file_path in files:
            try:
                self.repo.index.add(items=[file_path])

                logger.debug(f"Added {file_path} to git.")

            except GitCommandError as err:
                logger.error(f"Failed to add {file_path} to git: {err}")
                raise

    def commit(self, message: str) -> None:
        """
        Commit staged changes with the provided message.

        Args:
            message (str): Commit message.

        """

        logger.info(f"Committing changes with message: {message}")
        logger.debug(f"Staged changes: {self.repo.index.diff('HEAD')}")

        try:
            self.repo.index.commit(message=message)

            logger.info("Committed changes.")

        except GitCommandError as err:
            logger.error(f"Failed to commit changes: {err}")
            raise

    def push(self, *, branch_name: str, remote_name: str = "origin", force: bool = False) -> None:
        """
        Push the specified branch to the remote repository, optionally forcing the push.

        Args:
            branch_name (str): The branch to push.
            remote_name (str): Name of the Git remote (default: 'origin').
            force (bool): If True, force push the branch.

        """

        logger.info(f"Pushing branch '{branch_name}' to remote '{remote_name}' with force={force}.")

        try:
            remote: Remote = self.repo.remote(name=remote_name)
            push_info = remote.push(refspec=branch_name, force=force)

            logger.debug(f"Push result: {push_info}")

        except GitCommandError as err:
            logger.error(f"Failed to push branch '{branch_name}' to remote '{remote_name}': {err}")
            raise

    def close_old_release_prs(
        self,
        *,
        github_token: str,
        repo_full_name: str,
        target_branch: str,
        labels: list[str] | None = None,
    ) -> None:
        """
        Close open PRs.

        This method checks for open pull requests in the specified GitHub repository 
        that are targeting the specified branch. It closes any open pull requests
        that match the specified labels and are based on branches starting with "release/".
        This is useful for cleaning up old pull requests before creating a new one.

        Args:
            github_token: GitHub access token.
            repo_full_name: The repository name (e.g., "owner/repo").
            target_branch: The target branch (e.g., 'dev' or 'main').
            labels: Optional list of label names to match.

    
        Raises:
            GithubException: If there is an error with the GitHub API.

        """

        logger.info(f"Checking for existing PRs for target branch: {target_branch}")

        gh = Github(login_or_token=github_token)

        try:
            repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)
            open_prs = repo.get_pulls(state="open")

            for pr in open_prs:
                head_ref: str = pr.head.ref
                base_ref: str = pr.base.ref
                pr_labels: list[str] = [label.name for label in pr.labels]
            
                if (
                    head_ref.startswith("release/")
                    and base_ref == target_branch
                    and (not labels or any(label in pr_labels for label in labels))
                ):
                    logger.info(f"Closing old PR #{pr.number}: {head_ref} → {base_ref}")
                    pr.edit(state="closed")

        except GithubException as err:
            logger.error(f"GitHub API error while closing PRs: {err}")
            raise

    def create_pr(
        self,
        *,
        github_token: str,
        repo_full_name: str,
        title: str,
        source: str,
        target: str,
        label: str | None = None,
    ) -> int:
        """
        Create a pull request from the source branch to the target branch.

        Args:
            github_token (str): GitHub API token.
            repo_full_name (str): Repository name in "owner/repo" format.
            title (str): Title for the PR.
            source (str): Source branch.
            target (str): Target branch.
            label (str | None): Optional label to add to the PR.
                If None, no label is added.

        Returns:
            The PR number.

        """

        logger.debug("Creating PR with the following parameters:")
        logger.debug(f"  Repo: {repo_full_name}")
        logger.debug(f"  Title: {title}")
        logger.debug(f"  Source (source): {source}")
        logger.debug(f"  Target (target): {target}")

        gh = Github(login_or_token=github_token)

        try:
            repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)

            for pr in repo.get_pulls(state="open"):
                if pr.head.ref == source and pr.base.ref == target:
                    logger.warning(
                        f"PR already exists for branch '{source}' → '{target}', skipping creation."
                    )

                    return pr.number

            new_pr: PullRequest = repo.create_pull(
                title=title, body="Auto-created PR by auto-semver.", head=source, base=target
            )

            if label:
                try:
                    new_pr.add_to_labels(label)

                    logger.info(f"Label '{label}' added to PR #{new_pr.number}.")

                except GithubException as err:
                    logger.error(f"Failed to add label '{label}' to PR #{new_pr.number}: {err}")

                    raise

            logger.info(f"PR created successfully: #{new_pr.number}")

            return new_pr.number

        except GithubException as err:
            logger.error(f"GitHub API error during PR creation: {err}")

            raise

    def get_recent_commits(self, commit_sha: str) -> list[str]:
        """
        Get commit messages between the specified between a given commit SHA and HEAD.

        This method attempts to fetch the commit SHA from the remote if it doesn't exist locally.

        Args:
            commit_sha (str): The base commit SHA to compare against HEAD.

        Returns:
            list[str]: A list of commit messages.

        Raises:
            RuntimeError: If the git command fails.

        """

        logger.info(f"Fetching recent commits between {commit_sha} and HEAD.")

        try:
            # Check if SHA exists locally
            self.repo.git.rev_parse(commit_sha)
        except GitCommandError:
            logger.warning(f"SHA {commit_sha} not found locally. Attempting to fetch...")
            try:
                self.repo.git.fetch("origin", commit_sha, "--depth=1")
            except GitCommandError as fetch_err:
                logger.error(f"Failed to fetch missing SHA '{commit_sha}': {fetch_err}")
                raise RuntimeError(f"Failed to fetch SHA {commit_sha}: {fetch_err}") from fetch_err

        try:
            commits: list[Commit] = list(self.repo.iter_commits(f"{commit_sha}..HEAD"))
            messages: list[str] = [str(commit.message).strip() for commit in reversed(commits)]

            for message in messages:
                logger.debug(f"Commit message: {message}")

            logger.debug(f"Found {len(messages)} commits.")

            return messages

        except GitCommandError as err:
            logger.error(f"Failed to fetch recent commits: {err}")

            raise RuntimeError(f"Failed to fetch recent commits: {err}") from err

    def get_highest_release_lock_version_for_target(self, target_branch: str | None = None) -> Version | None:
        """
        Scans all release/* branches, loads .semver.lock from each,
        and returns the highest declared version.

        Args:
            target_branch (str): The target branch to check against.

        Returns:
            The highest Version object found, or None if none found.
        """
        highest: Version | None = None
        origin = self.repo.remotes.origin

        try:
            logger.info("Fetching all remote branches...")
            origin.fetch(prune=True)

            for ref in origin.refs:
                if not ref.name.startswith("origin/release/") or ref.name != f"origin/{target_branch}":
                    logger.debug(f"Skipping branch {ref.name}.")
                    continue

                branch_name = ref.name.removeprefix("origin/")
                logger.debug(f"Checking branch for lockfile: {branch_name}")

                try:
                    blob = self.repo.git.show(f"{branch_name}:{SemverLock.FILE_NAME}")
                    lock = SemverLock.from_dict(yaml.safe_load(blob))

                    if target_branch and lock.target_branch != target_branch:
                        logger.debug(f"Skipping lockfile on {branch_name} for target branch {target_branch}.")
                        continue

                    logger.debug(f"Found lock version {lock.version} on {branch_name}")

                    if highest is None:
                        highest = lock.version
                        logger.debug(f"First lockfile found: {highest}")
                    else:
                        highest = max(highest, lock.version)
                        logger.debug(f"New highest version: {highest}")
                except Exception as err:
                    logger.warning(f"No lockfile in {branch_name}: {err}")

            return highest

        except Exception as err:
            logger.error(f"Failed to scan remote release branches: {err}")
            return None
