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
        title="Release v1.0.0",
        source="release/v1.0.0",
        target="main",
    )
"""

import logging
import re
from pathlib import Path

import yaml
from git import Commit, GitCommandError, Head, Repo
from git.remote import Remote
from github import Github
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository

from auto_semver.config import Config
from auto_semver.semver import SemverLock, Version

logger = logging.getLogger(__package__)


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
        self._repo_full_name: str = self._parse_repository_name()  # Cache repository name on init
        if ensure_safe:
            self.__ensure_git_safe_directory()
        self.__ensure_git_identity()

    def __ensure_git_safe_directory(self) -> None:
        """
        Ensure the repository path is listed as a safe Git directory in the repository config.

        This is important for CI environments that may require explicitly trusting the repo.
        Uses repository-level config which doesn't require elevated privileges and is scoped to this repo.
        """

        logger.info("Ensuring the repository is marked as a safe directory.")

        safe_key: str = "safe"
        directory_key: str = "directory"

        path: str = str(self.repo.working_tree_dir)

        logger.debug(f"Working tree directory: {path}")

        try:
            git_config = self.repo.config_writer(config_level="global")

            logger.debug(f"Checking if {path} is in safe directories.")

            raw_values = git_config.get_values(section=safe_key, option=directory_key, default="")
            safe_dirs: list[str] = [v for v in raw_values if isinstance(v, str)]

            if path not in safe_dirs:
                logger.debug(f"{path} is not in safe directories.")
                logger.info(f"Adding {path} to safe directories.")

                git_config.set_value(section=safe_key, option=directory_key, value=path)

            git_config.release()

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to configure git safe directory due to permission error: {e}")
            logger.error(
                "Git safe directory configuration is required for proper operation in CI environments."
            )
            raise RuntimeError(f"Unable to configure git safe directory: {e}") from e

    def _get_github_repo(self, *, github_token: str, repo_full_name: str) -> Repository:
        return Github(github_token).get_repo(repo_full_name)

    def _parse_repository_name(self, *, remote_name: str = "origin") -> str:
        """
        Extract the repository name from the Git remote URL.

        Args:
            remote_name (str): Name of the Git remote (default: 'origin').

        Returns:
            str: Repository name in "owner/repo" format.

        Raises:
            ValueError: If remote URL cannot be parsed or is not a GitHub URL.
        """
        try:
            remote: Remote = self.repo.remote(name=remote_name)
            remote_url = remote.url

            # Handle both SSH and HTTPS GitHub URLs
            # SSH: git@github.com:owner/repo.git
            # HTTPS: https://github.com/owner/repo.git

            patterns = [
                r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$",  # SSH format
                r"https://github\.com/([^/]+)/(.+?)(?:\.git)?$",  # HTTPS format
            ]

            for pattern in patterns:
                match = re.match(pattern, remote_url)
                if match:
                    owner, repo = match.groups()
                    return f"{owner}/{repo}"

            raise ValueError(f"Unable to parse GitHub repository from remote URL: {remote_url}")

        except Exception as e:
            raise ValueError(
                f"Failed to get repository name from remote '{remote_name}': {e}"
            ) from e

    def get_repository_name(self) -> str:
        """
        Get the cached repository name.

        Returns:
            str: Repository name in "owner/repo" format.
        """
        return self._repo_full_name

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

    def add(self, files: list[str] | list[Path] | list[str | Path]) -> None:
        """
        Stage the specified files for commit.

        Args:
            files (list[str]): List of file paths to add to the Git index.

        """
        files = [str(f) for f in files]

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

    def tag(self, *, tag: str, branch: str) -> str:
        """
        Create a new tag on the given branch.

        Args:
            tag (str): Tag name.
            branch (str): Branch name.

        """
        return self.repo.create_tag(path=tag, ref=branch, message="").name

    def fetch(self, *, remote_name: str = "origin") -> None:
        """
        Fetch all refs from the remote repository.

        Args:
            remote_name (str): Name of the Git remote (default: 'origin').

        Raises:
            GitCommandError: If fetch operation fails.
        """
        logger.info(f"Fetching from remote '{remote_name}'")

        try:
            remote: Remote = self.repo.remote(name=remote_name)
            remote.fetch()
            logger.debug(f"Fetch from '{remote_name}' completed")
        except GitCommandError as err:
            logger.error(f"Failed to fetch from remote '{remote_name}': {err}")
            raise

    def checkout(self, *, branch_name: str, create_from: str | None = None) -> None:
        """
        Checkout an existing branch or create and checkout a new branch.

        Args:
            branch_name (str): Name of the branch to checkout.
            create_from (str | None): If provided, create the branch from this ref before checkout.

        Raises:
            GitCommandError: If checkout operation fails.
        """
        try:
            if create_from:
                logger.info(
                    f"Creating and checking out branch '{branch_name}' from '{create_from}'"
                )
                new_branch = self.repo.create_head(branch_name, create_from)
                new_branch.checkout()
            else:
                logger.info(f"Checking out branch '{branch_name}'")
                self.repo.heads[branch_name].checkout()

            logger.debug(f"Checked out branch '{branch_name}'")
        except (GitCommandError, IndexError) as err:
            logger.error(f"Failed to checkout branch '{branch_name}': {err}")
            raise GitCommandError(f"Checkout failed for branch '{branch_name}'") from err

    def __ensure_git_identity(
        self, *, email: str = "auto-semver@github.action", name: str = "Auto-Semver Bot"
    ) -> None:
        """
        Ensure Git user identity is configured for commits.

        This is required for merge operations that create commits.
        If not already set, configures user.email and user.name locally.

        Args:
            email (str): Git user email (default: 'auto-semver@github.action').
            name (str): Git user name (default: 'Auto-Semver Bot').
        """
        try:
            # Check if identity is already configured
            with self.repo.config_reader() as config:
                try:
                    existing_email = config.get_value("user", "email")
                    existing_name = config.get_value("user", "name")
                    logger.debug(
                        f"Git identity already configured: {existing_name} <{existing_email}>"
                    )
                    return
                except Exception:
                    # Not configured, will set below
                    pass

            # Configure identity locally
            logger.info(f"Configuring Git identity: {name} <{email}>")
            with self.repo.config_writer() as config:
                config.set_value("user", "email", email)
                config.set_value("user", "name", name)

            logger.debug("Git identity configured successfully")
        except Exception as err:
            logger.warning(f"Failed to configure Git identity: {err}")
            # Don't raise - let the merge fail with clearer error if needed

    def pull(self, *, branch_name: str, remote_name: str = "origin") -> None:
        """
        Pull the latest changes for the current branch from remote.

        Args:
            branch_name (str): Name of the branch to pull.
            remote_name (str): Name of the Git remote (default: 'origin').

        Raises:
            GitCommandError: If pull operation fails.
        """
        logger.info(f"Pulling latest changes for '{branch_name}' from '{remote_name}'")

        try:
            remote: Remote = self.repo.remote(name=remote_name)
            remote.pull(branch_name)
            logger.debug(f"Pull for '{branch_name}' completed")
        except GitCommandError as err:
            logger.error(f"Failed to pull '{branch_name}' from '{remote_name}': {err}")
            raise

    def merge(
        self, *, source_ref: str, message: str, no_ff: bool = True, remote_name: str = "origin"
    ) -> None:
        """
        Merge a source ref into the current branch.

        Args:
            source_ref (str): Source reference to merge (branch name, will use remote/branch).
            message (str): Merge commit message.
            no_ff (bool): If True, create a merge commit even if fast-forward is possible.
            remote_name (str): Remote name to prefix to source_ref (default: 'origin').

        Raises:
            RuntimeError: If merge fails due to conflicts or other errors.
        """
        full_source_ref = f"{remote_name}/{source_ref}"
        logger.info(f"Merging '{full_source_ref}' into current branch (no-ff={no_ff})")

        try:
            self.repo.git.merge(full_source_ref, no_ff=no_ff, m=message)
            logger.info(f"Merge successful: {full_source_ref} → HEAD")
        except GitCommandError as merge_err:
            stderr = str(merge_err)
            if "CONFLICT" in stderr or "conflict" in stderr.lower():
                logger.error(f"Merge conflict detected: {merge_err}")
                # Attempt to abort the merge to keep repo clean
                try:
                    self.repo.git.merge("--abort")
                    logger.debug("Aborted merge after conflict")
                except Exception:
                    logger.warning("Failed to abort merge after conflict")

                raise RuntimeError(
                    f"Merge conflict detected when merging '{full_source_ref}'. "
                    "Please resolve conflicts manually."
                ) from merge_err

            logger.error(f"Merge failed: {merge_err}")
            raise RuntimeError(f"Merge failed: {merge_err}") from merge_err

    def auto_promote(
        self,
        *,
        source_branch: str,
        target_branch: str,
        version: str,
        source_version: str | None = None,
        remote_name: str = "origin",
    ) -> str:
        """
        Automatically promote changes from source branch to target branch.

        This performs a local merge operation (SCM-agnostic) that:
        1. Fetches latest changes from remote
        2. Checks out/creates the target branch
        3. Pulls latest changes on target
        4. Merges source branch into target
        5. Creates a tag on target
        6. Pushes target branch and tags to remote

        Args:
            source_branch (str): Source branch name (e.g., 'dev').
            target_branch (str): Target branch name (e.g., 'staging').
            version (str): Version tag to create on the target branch.
            source_version (str | None): Original version tag from source branch.
            remote_name (str): Remote name (default: 'origin').

        Returns:
            str: The version tag that was created.

        Raises:
            RuntimeError: If any operation fails (fetch, merge, push, etc.).
        """
        logger.info(f"Starting auto-promotion: {source_branch} → {target_branch}")

        try:
            # 1. Fetch latest changes
            self.fetch(remote_name=remote_name)

            # 2. Checkout or create target branch
            if target_branch in self.repo.heads:
                self.checkout(branch_name=target_branch)
            else:
                self.checkout(
                    branch_name=target_branch, create_from=f"{remote_name}/{target_branch}"
                )

            # 3. Pull latest changes on target
            self.pull(branch_name=target_branch, remote_name=remote_name)

            # 4. Merge source into target
            if source_version:
                merge_message = f"chore: auto-promote {source_version} from {source_branch} to {target_branch} as {version}"
            else:
                merge_message = f"chore: auto-promote from {source_branch} to {target_branch} as {version}"

            self.merge(source_ref=source_branch, message=merge_message, remote_name=remote_name)

            # 5. Create tag on target branch
            logger.info(f"Creating tag '{version}' on '{target_branch}'")
            tag_ref = self.repo.create_tag(version, message=f"Auto-promotion: {version}")

            # 6. Push target branch
            self.push(branch_name=target_branch, remote_name=remote_name)

            # 7. Push tags
            logger.info("Pushing tags to remote")
            remote: Remote = self.repo.remote(name=remote_name)
            remote.push(tags=True)

            logger.info(
                f"✅ Auto-promotion complete: {source_branch} → {target_branch} (tagged: {version})"
            )

            return str(tag_ref)

        except (GitCommandError, RuntimeError) as err:
            logger.error(f"Auto-promotion failed: {err}")
            raise RuntimeError(f"Auto-promotion failed: {err}") from err
        except Exception as err:
            logger.error(f"Unexpected error during auto-promotion: {err}")
            raise RuntimeError(f"Auto-promotion failed unexpectedly: {err}") from err

    def close_old_release_prs(
        self,
        *,
        github_token: str,
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
            target_branch: The target branch (e.g., 'dev' or 'main').
            labels: Optional list of label names to match.


        Raises:
            GithubException: If there is an error with the GitHub API.

        """

        # Get the repository name (uses cached value)
        repo_full_name = self._repo_full_name

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
        title: str,
        body: str,
        source: str,
        target: str,
        labels: list[str] | None = None,
    ) -> int:
        """
        Create a pull request from the source branch to the target branch.

        Args:
            github_token (str): GitHub API token.
            title (str): Title for the PR.
            body (str): Body for the PR content.
            source (str): Source branch.
            target (str): Target branch.
            labels (str | None): Optional label to add to the PR.
                If None, no label is added.

        Returns:
            The PR number.

        """

        # Get the repository name (uses cached value)
        repo_full_name = self._repo_full_name

        logger.debug("Creating PR with the following parameters:")
        logger.debug(f"  Repo: {repo_full_name}")
        logger.debug(f"  Title: {title}")
        logger.debug(f"  Body: {body}")
        logger.debug(f"  Source: {source}")
        logger.debug(f"  Target: {target}")
        logger.debug(f"  Labels: {labels}")

        gh = Github(login_or_token=github_token)

        try:
            repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)

            for pr in repo.get_pulls(state="open"):
                if pr.head.ref == source and pr.base.ref == target:
                    logger.warning(
                        f"PR already exists for branch '{source}' → '{target}', skipping creation."
                    )

                    return pr.number

            new_pr: PullRequest = repo.create_pull(title=title, body=body, head=source, base=target)

            if labels:
                try:
                    new_pr.add_to_labels(*labels)

                    label_str = ", ".join(f"'{label}'" for label in labels)
                    logger.info(f"Labels [{label_str}] added to PR #{new_pr.number}.")

                except GithubException as err:
                    logger.error(f"Failed to add labels '{labels}' to PR #{new_pr.number}: {err}")

                    raise

            logger.info(f"PR created successfully: #{new_pr.number}")

            return new_pr.number

        except GithubException as err:
            logger.error(f"GitHub API error during PR creation: {err}")

            raise

    def get_recent_commits(
        self,
        commit_sha: str,
        *,
        filter_release_commits: bool = True,
        config: Config | None = None,
    ) -> list[str]:
        """
        Get commit messages between the specified commit SHA and HEAD.

        This method attempts to fetch the commit SHA from the remote if it doesn't exist locally.

        Args:
            commit_sha (str): The base commit SHA to compare against HEAD.
            filter_release_commits (bool): If True, filters out release-related commits.
            config (Config): Configuration object to determine release commit patterns.

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

            if filter_release_commits and config:
                original_count = len(messages)
                messages = self._filter_release_commits(messages, config)
                filtered_count = original_count - len(messages)

                if filtered_count > 0:
                    logger.debug(f"Filtered out {filtered_count} release-related commits")
                else:
                    logger.debug("No release-related commits found to filter out.")
            else:
                if not filter_release_commits:
                    logger.debug("Filtering of release commits is disabled.")
                if not config:
                    logger.debug("No config provided, skipping release commit filtering.")

            for message in messages:
                logger.debug(f"Commit message: {message}")

            logger.debug(f"Found {len(messages)} commits.")

            return messages

        except GitCommandError as err:
            logger.error(f"Failed to fetch recent commits: {err}")

            raise RuntimeError(f"Failed to fetch recent commits: {err}") from err

    def get_lock_version_from_branch(
        self,
        branch_name: str,
        remote_name: str = "origin",
    ) -> Version | None:
        """
        Get the version from the lockfile on a specific branch.

        Args:
            branch_name (str): The branch to check.
            remote_name (str): The name of the remote to check.

        Returns:
            The Version object found, or None if none found.

        """
        try:
            logger.info(f"Fetching branch '{branch_name}' from remote '{remote_name}'...")
            self.repo.git.fetch(remote_name, branch_name)

            full_branch_ref = f"{remote_name}/{branch_name}"
            logger.debug(f"Checking branch for lockfile: {full_branch_ref}")

            try:
                blob = self.repo.git.show(f"{full_branch_ref}:{SemverLock.path}")
                lock = SemverLock.from_dict(yaml.safe_load(blob))
                logger.debug(f"Loaded lockfile from {branch_name}: {lock}")
                return lock.version
            except Exception as err:
                logger.warning(f"No lockfile in {branch_name}: {err}")
                return None

        except Exception as err:
            logger.error(f"Failed to get lock version from branch {branch_name}: {err}")
            return None

    def get_lock_version_from_tag(self, tag_name: str) -> Version | None:
        """
        Get the version from the lockfile at a specific tag.

        Args:
            tag_name (str): The tag to check.

        Returns:
            The Version object found, or None if none found.
        """
        try:
            logger.debug(f"Checking tag for lockfile: {tag_name}")
            blob = self.repo.git.show(f"{tag_name}:{SemverLock.path}")
            lock = SemverLock.from_dict(yaml.safe_load(blob))
            logger.debug(f"Loaded lockfile from {tag_name}: {lock}")
            return lock.version
        except Exception as err:
            logger.warning(f"No lockfile in tag {tag_name}: {err}")
            return None

    def _filter_release_commits(self, messages: list[str], config: Config) -> list[str]:
        """
        Filter out release-related commit messages.

        Args:
            messages (list[str]): List of commit messages to filter.
            config (Config): Configuration object to get release title template.

        Returns:
            list[str]: Filtered list of commit messages with release commits removed.

        """

        # Get the release commit prefix from config
        release_prefix = config.data.pull_request.get_release_commit_prefix()
        if not release_prefix:
            logger.debug("No release prefix found in config title template")
            return messages

        logger.debug(f"Using config-based release prefix: '{release_prefix}'")

        filtered_messages = []

        for message in messages:
            if message.startswith(release_prefix):
                logger.debug(f"Filtering out release commit: {message}")
            else:
                filtered_messages.append(message)

        return filtered_messages
