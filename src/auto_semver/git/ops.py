# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
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

from __future__ import annotations

import base64
import logging
import re
from collections.abc import Callable, Collection
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from git import Actor, Commit, GitCommandError, Head, Repo
from git.remote import PushInfo, Remote
from github import Github
from github.GithubException import GithubException

from auto_semver.config.constants import PR_HIDDEN_MARKER
from auto_semver.semver import SemverLock, Version

if TYPE_CHECKING:
    from pathlib import Path

    from github.PullRequest import PullRequest
    from github.Repository import Repository
    from github.Requester import Requester

    from auto_semver.config import Config

logger = logging.getLogger(__package__)

LEGACY_RELEASE_PREFIX = "release/"
DEFAULT_RELEASE_PREFIX = "auto-semver/release/"

# GraphQL mutation that GitHub auto-signs (verified). Git Database REST create_git_commit
# does NOT produce verified signatures.
_CREATE_COMMIT_ON_BRANCH_MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) {
    commit {
      oid
    }
  }
}
"""


class GitOps:
    """
    Encapsulates Git and GitHub operations such as branch handling, commits, pushing, and pull requests.

    Attributes:
        repo (Repo): The Git repository object from GitPython.

    """

    def __init__(
        self,
        *,
        repo_path: str = ".",
        ensure_safe: bool = False,
        signed_commits: bool = False,
        github_token: str | None = None,
    ) -> None:
        """
        Initialize GitOps for the given repository path.

        Args:
            repo_path (str): Path to the local Git repository (default: current directory).
            ensure_safe (bool): If True, ensures the repository is marked as a safe directory in Git config.
            signed_commits (bool): When True, create commits/merges/tags via the GitHub API so
                GitHub signs them as verified (requires ``github_token``).
            github_token (str | None): Token for API-backed commits (App installation token).

        """

        self.repo = Repo(path=repo_path)
        self._repo_full_name: str = self._parse_repository_name()  # Cache repository name on init
        self.signed_commits = signed_commits
        self.github_token = github_token
        if signed_commits and not github_token:
            raise ValueError("github_token is required when signed_commits=True")
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

    def _github_client(self) -> Github:
        if not self.github_token:
            raise ValueError("github_token is required for API git operations")
        return Github(self.github_token)

    def _gh_repo(self) -> Repository:
        if not self.github_token:
            raise ValueError("github_token is required for API git operations")
        return self._get_github_repo(
            github_token=self.github_token,
            repo_full_name=self._repo_full_name,
        )

    def _github_requester(self) -> Requester:
        return self._github_client().requester

    def _collect_staged_paths(self) -> list[str]:
        """Return repository-relative paths staged for the next commit (all change types)."""
        additions, deletions = self._collect_staged_file_changes()
        return additions + deletions

    def _collect_staged_file_changes(self) -> tuple[list[str], list[str]]:
        """
        Return staged paths split into additions/modifications and deletions.

        Uses ``git diff --cached --diff-filter`` so GraphQL ``createCommitOnBranch``
        receives correct ``fileChanges.additions`` and ``fileChanges.deletions``.
        """
        added = self.repo.git.diff("--cached", "--name-only", "--diff-filter=ACMR")
        deleted = self.repo.git.diff("--cached", "--name-only", "--diff-filter=D")
        additions = [line.strip() for line in added.splitlines() if line.strip()]
        deletions = [line.strip() for line in deleted.splitlines() if line.strip()]
        return additions, deletions

    def _collect_dirty_tracked_paths(self) -> list[str]:
        """Return tracked paths with unstaged modifications."""
        output = self.repo.git.diff("--name-only")
        return [line.strip() for line in output.splitlines() if line.strip()]

    @staticmethod
    def _normalize_repo_rel_path(rel_path: str) -> str:
        return rel_path.replace("\\", "/")

    @staticmethod
    def _split_commit_message(message: str) -> tuple[str, str | None]:
        """Split a commit message into GraphQL headline and optional body."""
        headline, sep, body = message.partition("\n")
        headline = headline.strip() or message.strip()
        body_text = body.strip() if sep and body.strip() else None
        return headline, body_text

    def _reject_unsupported_file_modes(self, *, file_paths: list[str], repo_root: Path) -> None:
        """
        Raise if any path is a symlink or executable.

        ``createCommitOnBranch`` only supports regular non-executable files.
        """
        for rel_path in file_paths:
            full_path = repo_root / rel_path
            if not full_path.exists():
                continue
            if full_path.is_symlink():
                raise ValueError(
                    f"Signed commits cannot include symlinks via createCommitOnBranch: {rel_path}"
                )
            if full_path.is_file() and full_path.stat().st_mode & 0o111:
                raise ValueError(
                    f"Signed commits cannot include executable files via createCommitOnBranch: "
                    f"{rel_path}"
                )

    def _ensure_remote_branch(self, *, branch_name: str) -> str:
        """
        Ensure ``branch_name`` exists on the remote; return its tip OID.

        When the branch is missing, create it at the local HEAD commit.
        """
        gh_repo = self._gh_repo()
        ref_name = f"heads/{branch_name}"
        try:
            ref = gh_repo.get_git_ref(ref_name)
            return str(ref.object.sha)
        except GithubException:
            parent_sha = self.repo.head.commit.hexsha
            gh_repo.create_git_ref(f"refs/{ref_name}", parent_sha)
            logger.info("Created remote branch %s at %s", branch_name, parent_sha)
            return parent_sha

    def _build_file_additions(
        self, *, file_paths: list[str], repo_root: Path
    ) -> list[dict[str, str]]:
        """Build GraphQL ``FileAddition`` payloads (base64 contents)."""
        self._reject_unsupported_file_modes(file_paths=file_paths, repo_root=repo_root)
        additions: list[dict[str, str]] = []
        for rel_path in file_paths:
            full_path = repo_root / rel_path
            content = full_path.read_bytes()
            additions.append(
                {
                    "path": self._normalize_repo_rel_path(rel_path),
                    "contents": base64.b64encode(content).decode("ascii"),
                }
            )
        return additions

    def _graphql_create_commit_on_branch(
        self,
        *,
        branch_name: str,
        message: str,
        expected_head_oid: str,
        additions: list[dict[str, str]],
        deletions: list[dict[str, str]],
    ) -> str:
        """Run ``createCommitOnBranch`` and return the new commit OID."""
        headline, body = self._split_commit_message(message)
        message_input: dict[str, str] = {"headline": headline}
        if body is not None:
            message_input["body"] = body

        variables = {
            "input": {
                "branch": {
                    "repositoryNameWithOwner": self._repo_full_name,
                    "branchName": branch_name,
                },
                "message": message_input,
                "expectedHeadOid": expected_head_oid,
                "fileChanges": {
                    "additions": additions,
                    "deletions": deletions,
                },
            }
        }

        _, data = self._github_requester().graphql_query(
            _CREATE_COMMIT_ON_BRANCH_MUTATION,
            variables,
        )
        try:
            oid = data["data"]["createCommitOnBranch"]["commit"]["oid"]
        except (KeyError, TypeError) as err:
            raise RuntimeError(f"createCommitOnBranch returned unexpected payload: {data}") from err
        return str(oid)

    @staticmethod
    def _is_expected_head_mismatch(exc: BaseException) -> bool:
        text = str(exc).lower()
        return "expectedheadoid" in text or "expected the head" in text

    def _api_commit_files_on_branch(
        self,
        *,
        branch_name: str,
        message: str,
        file_paths: list[str] | None = None,
        deletions: list[str] | None = None,
        force: bool = False,
    ) -> str:
        """
        Create a verified commit on a branch via GraphQL ``createCommitOnBranch``.

        GitHub auto-signs commits from this mutation. The Git Database REST
        ``create_git_commit`` API does not.

        Args:
            branch_name: Target branch (created on the remote if missing).
            message: Commit message (first line = headline, rest = body).
            file_paths: Paths to add or update (read from the local worktree).
            deletions: Paths to delete in the commit.
            force: Kept for call-site compatibility; GraphQL commits always
                require a matching ``expectedHeadOid`` (no force-push). Author
                and committer are the token owner and cannot be overridden.
        """
        del force  # GraphQL path cannot force-update divergent refs.
        addition_paths = list(file_paths or [])
        deletion_paths = list(deletions or [])
        if not addition_paths and not deletion_paths:
            raise ValueError("file_paths/deletions must not be empty for API commit")

        repo_root = Path(self.repo.working_tree_dir or ".")
        additions = self._build_file_additions(file_paths=addition_paths, repo_root=repo_root)
        deletion_inputs = [{"path": self._normalize_repo_rel_path(path)} for path in deletion_paths]

        expected_head = self._ensure_remote_branch(branch_name=branch_name)
        try:
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=branch_name,
                message=message,
                expected_head_oid=expected_head,
                additions=additions,
                deletions=deletion_inputs,
            )
        except GithubException as err:
            if not self._is_expected_head_mismatch(err):
                raise
            logger.warning(
                "expectedHeadOid mismatch on %s; fetching and retrying once: %s",
                branch_name,
                err,
            )
            self.fetch()
            expected_head = self._ensure_remote_branch(branch_name=branch_name)
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=branch_name,
                message=message,
                expected_head_oid=expected_head,
                additions=additions,
                deletions=deletion_inputs,
            )

        self.fetch()
        logger.info("Verified API commit %s on %s", commit_sha, branch_name)
        return commit_sha

    def _api_merge(self, *, base: str, head: str, message: str) -> str:
        """
        Merge ``head`` into ``base`` via the GitHub REST merges API.

        Kept on REST (not GraphQL) because ``POST /repos/{owner}/{repo}/merges``
        already produces a GitHub-signed, verified merge commit. There is no
        GraphQL equivalent that preserves merge semantics.
        """
        gh_repo = self._gh_repo()
        result = gh_repo.merge(base=base, head=head, commit_message=message)
        if result is None or not getattr(result, "sha", None):
            raise RuntimeError(f"Merge API returned no commit for {head} -> {base}")
        logger.info("Verified API merge %s into %s (%s)", head, base, result.sha)
        return str(result.sha)

    def _api_create_lightweight_tag(self, *, tag: str, sha: str) -> str:
        """Create a lightweight tag ref via the GitHub API."""
        gh_repo = self._gh_repo()
        ref_name = f"tags/{tag}"
        try:
            ref = gh_repo.get_git_ref(ref_name)
            ref.edit(sha=sha, force=True)
        except GithubException:
            gh_repo.create_git_ref(f"refs/{ref_name}", sha)
        logger.info("Verified API tag %s -> %s", tag, sha)
        return tag

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
                r"https://(?:.*?@)?github\.com/([^/]+)/(.+?)(?:\.git)?$",  # HTTPS format (supports auth)
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

    def commit(self, message: str, *, force: bool = False) -> None:
        """
        Commit staged changes with the provided message.

        Args:
            message (str): Commit message.
            force (bool): Kept for compatibility with signed commits. GraphQL
                ``createCommitOnBranch`` cannot force-update divergent refs;
                concurrent updates retry once on ``expectedHeadOid`` mismatch.
        """

        logger.info(f"Committing changes with message: {message}")
        logger.debug(f"Staged changes: {self.repo.index.diff('HEAD')}")

        if self.signed_commits:
            branch_name = self.repo.active_branch.name
            additions, deletions = self._collect_staged_file_changes()
            if not additions and not deletions:
                logger.warning("No staged files for signed commit")
                return
            commit_sha = self._api_commit_files_on_branch(
                branch_name=branch_name,
                message=message,
                file_paths=additions,
                deletions=deletions,
                force=force,
            )
            # GraphQL commits update the remote only; sync the runner worktree so
            # later checkouts (e.g. auto-promote to staging) are not blocked by
            # leftover dirty files such as .semver.lock.
            self.repo.git.reset("--hard", commit_sha)
            logger.info("Synced local worktree to signed commit %s", commit_sha)
            return

        try:
            # Explicitly set author and committer to ensure consistency (e.g., prevent "GitHub" as committer)
            reader = self.repo.config_reader()
            author = Actor(
                name=str(reader.get_value("user", "name")),
                email=str(reader.get_value("user", "email")),
            )
            reader.release()

            self.repo.index.commit(message=message, author=author, committer=author)

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

        if self.signed_commits:
            logger.info(
                "Signed commit path: branch/tag refs updated via GitHub API; syncing local clone"
            )
            self.fetch(remote_name=remote_name)
            return

        try:
            remote: Remote = self.repo.remote(name=remote_name)
            push_infos = remote.push(refspec=branch_name, force=force)

            for info in push_infos:
                if info.flags & (
                    PushInfo.ERROR
                    | PushInfo.REJECTED
                    | PushInfo.REMOTE_REJECTED
                    | PushInfo.REMOTE_FAILURE
                ):
                    error_msg = f"Push failed for {branch_name}: {info.summary}"
                    if info.flags & PushInfo.REJECTED:
                        error_msg += ". Check if remote has diverged or if 'force' is required."

                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            logger.debug(f"Push result: {push_infos}")

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
        if self.signed_commits:
            gh_repo = self._gh_repo()
            branch_ref = gh_repo.get_git_ref(f"heads/{branch}")
            return self._api_create_lightweight_tag(tag=tag, sha=branch_ref.object.sha)

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
        self,
        *,
        email: str = "256984269+auto-semver-bot[bot]@users.noreply.github.com",
        name: str = "auto-semver-bot[bot]",
    ) -> None:
        """
        Ensure Git user identity is configured for commits.

        This is required for merge operations that create commits.
        If not already set, configures user.email and user.name locally.

        Prefer setting identity from the GitHub App token outputs in CI
        (`user-name` / `user-email`). The defaults match this repo's App bot
        noreply address so fallback commits attribute correctly on GitHub.

        Args:
            email (str): Git user email (default: App bot users.noreply address).
            name (str): Git user name (default: auto-semver-bot[bot]).
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
        self,
        *,
        source_ref: str,
        message: str,
        no_ff: bool = True,
        remote_name: str = "origin",
        is_tag: bool = False,
        prefer_source_paths: Collection[str] | None = None,
    ) -> None:
        """
        Merge a source ref into the current branch.

        Args:
            source_ref (str): Source reference to merge (branch name, will use remote/branch).
            message (str): Merge commit message.
            no_ff (bool): If True, create a merge commit even if fast-forward is possible.
            remote_name (str): Remote name to prefix to source_ref (default: 'origin').
            is_tag (bool): If True, treat source_ref as a tag (do not prepend remote).
            prefer_source_paths: Relative paths where conflicts may be auto-resolved by
                taking the source (theirs) side. Used during promotion for version
                metadata files that diverge by design between branches.

        Raises:
            RuntimeError: If merge fails due to conflicts or other errors.
        """
        if is_tag:
            full_source_ref = source_ref
        else:
            full_source_ref = f"{remote_name}/{source_ref}"

        logger.info(f"Merging '{full_source_ref}' into current branch (no-ff={no_ff})")

        try:
            self.repo.git.merge(full_source_ref, no_ff=no_ff, m=message)
            logger.info(f"Merge successful: {full_source_ref} → HEAD")
        except GitCommandError as merge_err:
            stderr = str(merge_err)
            if "CONFLICT" in stderr or "conflict" in stderr.lower():
                if prefer_source_paths and self._resolve_promotion_conflicts(
                    prefer_source_paths=prefer_source_paths,
                    merge_message=message,
                ):
                    logger.info(
                        "Resolved promotion-file conflicts preferring source; merge completed"
                    )
                    return

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

    def _unmerged_paths(self) -> list[str]:
        """Return paths with unresolved merge conflicts."""
        raw = self.repo.git.diff(name_only=True, diff_filter="U")
        if not raw:
            return []
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def _resolve_promotion_conflicts(
        self,
        *,
        prefer_source_paths: Collection[str],
        merge_message: str,
    ) -> bool:
        """
        Resolve conflicts by taking the source (theirs) side for allowlisted paths.

        Returns True when every conflicted path was allowlisted and the merge was
        completed; False when unresolved or non-allowlisted conflicts remain.
        """
        allowed = {str(Path(p)).replace("\\", "/") for p in prefer_source_paths}
        conflicted = self._unmerged_paths()
        if not conflicted:
            return False

        normalized = [str(Path(p)).replace("\\", "/") for p in conflicted]
        disallowed = [p for p in normalized if p not in allowed]
        if disallowed:
            logger.error(
                "Cannot auto-resolve merge conflicts outside promotion files: %s",
                ", ".join(disallowed),
            )
            return False

        for path in conflicted:
            logger.info("Preferring source version for conflicted file: %s", path)
            self.repo.git.checkout("--theirs", "--", path)
            self.repo.git.add("--", path)

        remaining = self._unmerged_paths()
        if remaining:
            logger.error("Unresolved conflicts remain after prefer-source: %s", remaining)
            return False

        # Complete the in-progress merge without re-invoking git merge.
        self.repo.git.commit(m=merge_message, no_edit=False)
        logger.info("Completed merge after resolving promotion-file conflicts")
        return True

    def _resolve_ref_sha(self, ref: str) -> str:
        """Resolve a branch or tag name to a commit SHA."""
        try:
            return str(self.repo.commit(ref).hexsha)
        except GitCommandError as err:
            raise RuntimeError(f"Could not resolve ref '{ref}': {err}") from err

    def _squash_commit_from_ref(self, *, ref: str, message: str) -> str:
        """
        Create a single promotion commit whose tree matches ``ref``.

        Uses the current branch tip as the sole parent so protected branches that
        reject merge commits still receive a linear promote commit.
        """
        source_commit = self.repo.commit(ref)
        parent = self.repo.head.commit
        new_sha = str(
            self.repo.git.commit_tree(
                source_commit.tree.hexsha,
                "-p",
                parent.hexsha,
                "-m",
                message,
            )
        )
        self.repo.head.set_commit(self.repo.commit(new_sha))
        # HEAD moved but index/worktree still reflect pre-promotion target; sync before hooks.
        self.repo.git.reset("--hard", new_sha)
        logger.info("Created squash promotion commit %s from %s", new_sha[:8], ref)
        return new_sha

    def _integrate_source_for_promotion(
        self,
        *,
        source_ref: str,
        message: str,
        remote_name: str,
        is_tag: bool,
        prefer_source_paths: Collection[str] | None,
    ) -> None:
        """
        Integrate a promotion source into the current branch.

        Tag sources try fast-forward first, then fall back to a single squash commit
        (no merge commit). Branch sources merge with ff when possible and auto-resolve
        metadata conflicts by preferring the source side.
        """
        full_ref = source_ref if is_tag else f"{remote_name}/{source_ref}"

        if is_tag:
            try:
                self.repo.git.merge(full_ref, ff_only=True)
                logger.info("Fast-forward promotion merge successful: %s", full_ref)
                return
            except GitCommandError as err:
                stderr = str(err)
                if "CONFLICT" in stderr or "conflict" in stderr.lower():
                    raise RuntimeError(
                        f"Fast-forward promotion conflict for '{full_ref}'. "
                        "Resolve manually before promoting."
                    ) from err
                logger.info(
                    "Fast-forward not possible for %s; creating squash promotion commit",
                    full_ref,
                )
                self._squash_commit_from_ref(ref=full_ref, message=message)
                return

        self.merge(
            source_ref=source_ref,
            message=message,
            remote_name=remote_name,
            is_tag=False,
            prefer_source_paths=prefer_source_paths,
            no_ff=False,
        )

    def _api_squash_promote(self, *, base: str, head: str, message: str) -> str:
        """
        Create a single verified commit on ``base`` whose tree matches ``head``.

        Uses GraphQL ``createCommitOnBranch`` with the file diff from
        ``base...head`` so the resulting commit is GitHub-signed.
        """
        gh_repo = self._gh_repo()
        base_ref = gh_repo.get_git_ref(f"heads/{base}")
        base_sha = str(base_ref.object.sha)
        head_sha = self._resolve_ref_sha(head)

        comparison = gh_repo.compare(base_sha, head_sha)
        additions: list[dict[str, str]] = []
        deletions: list[dict[str, str]] = []

        for file in comparison.files or []:
            path = self._normalize_repo_rel_path(file.filename)
            status = (file.status or "").lower()
            if status == "removed":
                deletions.append({"path": path})
                continue
            if status == "renamed" and file.previous_filename:
                deletions.append({"path": self._normalize_repo_rel_path(file.previous_filename)})
            content_file = gh_repo.get_contents(path, ref=head_sha)
            if isinstance(content_file, list):
                raise RuntimeError(f"Expected a file at {path}@{head_sha}, got a directory listing")
            raw = bytes(content_file.decoded_content)
            additions.append(
                {
                    "path": path,
                    "contents": base64.b64encode(raw).decode("ascii"),
                }
            )

        if not additions and not deletions:
            logger.info(
                "Squash promote %s -> %s has no file diff; leaving %s at %s",
                head,
                base,
                base,
                base_sha,
            )
            return base_sha

        try:
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=base,
                message=message,
                expected_head_oid=base_sha,
                additions=additions,
                deletions=deletions,
            )
        except GithubException as err:
            if not self._is_expected_head_mismatch(err):
                raise
            logger.warning(
                "expectedHeadOid mismatch on squash promote to %s; retrying once: %s",
                base,
                err,
            )
            self.fetch()
            base_ref = gh_repo.get_git_ref(f"heads/{base}")
            base_sha = str(base_ref.object.sha)
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=base,
                message=message,
                expected_head_oid=base_sha,
                additions=additions,
                deletions=deletions,
            )

        logger.info("Verified squash promotion commit on %s (%s)", base, commit_sha)
        return commit_sha

    def _integrate_source_for_promotion_api(
        self,
        *,
        target_branch: str,
        source_ref: str,
        message: str,
        is_source_tag: bool,
    ) -> str:
        """Integrate promotion source via GitHub API (ff merge or squash commit)."""
        try:
            return self._api_merge(base=target_branch, head=source_ref, message=message)
        except (GithubException, RuntimeError) as err:
            if not is_source_tag:
                raise
            logger.info(
                "API merge failed for tag promotion (%s); using squash commit: %s",
                source_ref,
                err,
            )
            return self._api_squash_promote(base=target_branch, head=source_ref, message=message)

    def auto_promote(
        self,
        *,
        source_branch: str,
        target_branch: str,
        version: str,
        source_version: str | None = None,
        remote_name: str = "origin",
        is_source_tag: bool = False,
        post_merge_hook: Callable[[str, str], None] | None = None,
        prefer_source_paths: Collection[str] | None = None,
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
            source_branch (str): Source branch name (e.g., 'dev') or tag name.
            target_branch (str): Target branch name (e.g., 'staging').
            version (str): Version tag to create on the target branch.
            source_version (str | None): Original version tag from source branch.
            remote_name (str): Remote name (default: 'origin').
            is_source_tag (bool): If True, treat source_branch as a tag.
            post_merge_hook (Callable[[str, str], None] | None): Optional hook function to execute after merge
            but before commit/tag.
            Receives (source_version_str, target_version_str).
            prefer_source_paths: Paths to auto-resolve favoring the source branch on
                conflict (changelog, lockfile, version files).

        Returns:
            str: The version tag that was created.

        Raises:
            RuntimeError: If any operation fails (fetch, merge, push, etc.).
        """
        logger.info(f"Starting auto-promotion: {source_branch} → {target_branch}")

        if source_version:
            merge_message = (
                f"chore: auto-promote {source_version} from {source_branch} "
                f"to {target_branch} as {version}"
            )
        else:
            merge_message = (
                f"chore: auto-promote from {source_branch} to {target_branch} as {version}"
            )

        if self.signed_commits:
            return self._auto_promote_api(
                source_branch=source_branch,
                target_branch=target_branch,
                version=version,
                source_version=source_version,
                merge_message=merge_message,
                is_source_tag=is_source_tag,
                post_merge_hook=post_merge_hook,
                prefer_source_paths=prefer_source_paths,
                remote_name=remote_name,
            )

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

            # 4. Integrate source into target (ff, squash, or merge + metadata wins)
            self._integrate_source_for_promotion(
                source_ref=source_branch,
                message=merge_message,
                remote_name=remote_name,
                is_tag=is_source_tag,
                prefer_source_paths=prefer_source_paths,
            )

            # Executing post-merge hook if provided
            if post_merge_hook:
                logger.info("Executing post-merge hook")
                # Fallback to source_branch if version not explicit
                src_v = source_version if source_version else source_branch

                try:
                    post_merge_hook(src_v, version)

                    dirty_paths = self._collect_dirty_tracked_paths()
                    if dirty_paths:
                        logger.info(
                            "Changes detected after post-merge hook; committing metadata: %s",
                            ", ".join(dirty_paths),
                        )
                        for path in dirty_paths:
                            self.repo.git.add("--", path)
                        self.repo.index.commit(f"chore: update version metadata for {version}")
                except Exception as e:
                    logger.error(f"Post-merge hook failed: {e}")
                    raise RuntimeError(f"Post-merge hook failed: {e}") from e

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

    def _diff_paths_between(
        self, *, base_sha: str, head_ref: str = "HEAD"
    ) -> tuple[list[str], list[str]]:
        """Return (additions/modifications, deletions) between two commits."""
        added = self.repo.git.diff(base_sha, head_ref, "--name-only", "--diff-filter=ACMR")
        deleted = self.repo.git.diff(base_sha, head_ref, "--name-only", "--diff-filter=D")
        additions = [line.strip() for line in added.splitlines() if line.strip()]
        deletions = [line.strip() for line in deleted.splitlines() if line.strip()]
        return additions, deletions

    def _remote_has_commit(self, sha: str) -> bool:
        """Return True when ``sha`` is already present on the GitHub remote."""
        try:
            self._gh_repo().get_git_commit(sha)
        except GithubException:
            return False
        return True

    def _publish_local_tip_once(
        self,
        *,
        branch_name: str,
        base_sha: str,
        message: str,
    ) -> str:
        """
        Move ``branch_name`` to the local tip with a single remote ref update.

        Fast-forwards the branch when HEAD already exists on the remote and
        matches ``base_sha``'s descendant with no unpublished local-only history
        that needs signing. Otherwise publishes the final worktree as one
        verified ``createCommitOnBranch`` commit so promote + metadata never
        produce two push events on the integration branch.
        """
        local_tip = self.repo.head.commit.hexsha
        if local_tip == base_sha:
            logger.info("No promotion changes on %s; leaving branch at %s", branch_name, base_sha)
            return base_sha

        additions, deletions = self._diff_paths_between(base_sha=base_sha, head_ref=local_tip)
        if not additions and not deletions:
            if self._remote_has_commit(local_tip):
                ref = self._gh_repo().get_git_ref(f"heads/{branch_name}")
                ref.edit(sha=local_tip)
                self.fetch()
                logger.info(
                    "Fast-forwarded %s to existing commit %s (single ref update)",
                    branch_name,
                    local_tip,
                )
                return local_tip
            logger.info(
                "Empty tree diff for %s but tip %s is local-only; leaving at %s",
                branch_name,
                local_tip,
                base_sha,
            )
            return base_sha

        # Prefer a true fast-forward when the tip is already on the remote and
        # there are no local-only commits beyond that tip (e.g. tag promote ff).
        if self._remote_has_commit(local_tip):
            try:
                self.repo.git.merge_base("--is-ancestor", base_sha, local_tip)
                ref = self._gh_repo().get_git_ref(f"heads/{branch_name}")
                ref.edit(sha=local_tip)
                self.fetch()
                logger.info(
                    "Fast-forwarded %s to %s (single ref update)",
                    branch_name,
                    local_tip,
                )
                return local_tip
            except GitCommandError:
                pass

        try:
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=branch_name,
                message=message,
                expected_head_oid=base_sha,
                additions=self._build_file_additions(
                    file_paths=additions,
                    repo_root=Path(self.repo.working_tree_dir or "."),
                ),
                deletions=[{"path": self._normalize_repo_rel_path(path)} for path in deletions],
            )
        except GithubException as err:
            if not self._is_expected_head_mismatch(err):
                raise
            logger.warning(
                "expectedHeadOid mismatch publishing tip on %s; retrying once: %s",
                branch_name,
                err,
            )
            self.fetch()
            expected_head = self._ensure_remote_branch(branch_name=branch_name)
            commit_sha = self._graphql_create_commit_on_branch(
                branch_name=branch_name,
                message=message,
                expected_head_oid=expected_head,
                additions=self._build_file_additions(
                    file_paths=additions,
                    repo_root=Path(self.repo.working_tree_dir or "."),
                ),
                deletions=[{"path": self._normalize_repo_rel_path(path)} for path in deletions],
            )
        self.fetch()
        logger.info(
            "Published verified promotion tip %s on %s (single ref update)",
            commit_sha,
            branch_name,
        )
        return commit_sha

    def _auto_promote_api(
        self,
        *,
        source_branch: str,
        target_branch: str,
        version: str,
        source_version: str | None,
        merge_message: str,
        is_source_tag: bool,
        post_merge_hook: Callable[[str, str], None] | None,
        prefer_source_paths: Collection[str] | None = None,
        remote_name: str = "origin",
    ) -> str:
        """
        Promote via local integrate + one verified remote tip update.

        Builds promote (and optional metadata) commits locally, then moves the
        target branch once so concurrent workflows (e.g. Secret Scan) are not
        canceled by a second push from the same job.
        """
        self.fetch(remote_name=remote_name)
        # Signed finalize may leave the worktree dirty if a prior sync was
        # skipped; discard local dirt so checkout of the promote target works.
        if self.repo.is_dirty(index=True, working_tree=True, untracked_files=False):
            logger.warning(
                "Dirty worktree before promote checkout; resetting to HEAD "
                "(remote already has signed changes)"
            )
            self.repo.git.reset("--hard", "HEAD")
        if target_branch in self.repo.heads:
            self.checkout(branch_name=target_branch)
        else:
            self.checkout(
                branch_name=target_branch,
                create_from=f"{remote_name}/{target_branch}",
            )
        self.pull(branch_name=target_branch, remote_name=remote_name)
        base_sha = self.repo.head.commit.hexsha

        self._integrate_source_for_promotion(
            source_ref=source_branch,
            message=merge_message,
            remote_name=remote_name,
            is_tag=is_source_tag,
            prefer_source_paths=prefer_source_paths,
        )

        if post_merge_hook:
            logger.info("Executing post-merge hook")
            src_v = source_version if source_version else source_branch
            try:
                post_merge_hook(src_v, version)
                dirty_paths = self._collect_dirty_tracked_paths()
                if dirty_paths:
                    logger.info(
                        "Changes detected after post-merge hook; committing metadata locally: %s",
                        ", ".join(dirty_paths),
                    )
                    for path in dirty_paths:
                        self.repo.git.add("--", path)
                    # Local-only; folded into the single verified tip published below.
                    self.repo.index.commit(f"chore: update version metadata for {version}")
            except Exception as exc:
                logger.error(f"Post-merge hook failed: {exc}")
                raise RuntimeError(f"Post-merge hook failed: {exc}") from exc

        tip_sha = self._publish_local_tip_once(
            branch_name=target_branch,
            base_sha=base_sha,
            message=merge_message,
        )
        self._api_create_lightweight_tag(tag=version, sha=tip_sha)
        self.fetch(remote_name=remote_name)
        logger.info(
            "✅ Verified auto-promotion complete: %s → %s (tagged: %s)",
            source_branch,
            target_branch,
            version,
        )
        return version

    def get_lock_at_ref(self, ref: str) -> SemverLock | None:
        """Load `.semver.lock` from a branch or tag ref."""
        try:
            blob = self.repo.git.show(f"{ref}:{SemverLock.path}")
            return SemverLock.from_dict(yaml.safe_load(blob))
        except GitCommandError as err:
            logger.debug("No lockfile at ref %s: %s", ref, err)
            return None

    def delete_branch(self, *, branch_name: str, remote_name: str = "origin") -> None:
        """Delete a remote branch ref."""
        logger.info("Deleting remote branch '%s' on '%s'", branch_name, remote_name)
        if self.signed_commits:
            gh_repo = self._gh_repo()
            ref_name = f"heads/{branch_name}"
            ref = gh_repo.get_git_ref(ref_name)
            ref.delete()
            self.fetch(remote_name=remote_name)
            return

        remote: Remote = self.repo.remote(name=remote_name)
        push_infos = remote.push(refspec=f":{branch_name}")
        for info in push_infos:
            if info.flags & (PushInfo.ERROR | PushInfo.REJECTED | PushInfo.REMOTE_FAILURE):
                raise RuntimeError(f"Failed to delete branch {branch_name}: {info.summary}")

    @staticmethod
    def _normalize_branch_name(ref: str) -> str:
        """Strip remote prefix from a git ref name."""
        for prefix in ("origin/", "refs/heads/"):
            if ref.startswith(prefix):
                return ref.removeprefix(prefix)
        return ref

    @staticmethod
    def _branch_matches_prefix(branch_name: str, branch_prefix: str) -> bool:
        """Return True when branch_name matches `{prefix}{semver}`."""
        prefix = branch_prefix if branch_prefix.endswith("/") else f"{branch_prefix}/"
        pattern = re.compile(re.escape(prefix) + r"\d+\.\d+\.\d+(?:-[\w.]+)?$")
        return bool(pattern.match(branch_name))

    def get_merged_source_branches_since(
        self,
        *,
        base_sha: str,
        target_branch: str,
        github_token: str,
    ) -> list[str]:
        """List merged PR head branch names on target_branch since base_sha."""
        repo_full_name = self._repo_full_name
        gh = Github(login_or_token=github_token)
        repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)
        branches: list[str] = []

        for pr in repo.get_pulls(
            state="closed", base=target_branch, sort="updated", direction="desc"
        ):
            if not pr.merged or not pr.merge_commit_sha:
                continue
            merge_sha = pr.merge_commit_sha
            try:
                self.repo.git.merge_base("--is-ancestor", base_sha, merge_sha)
                self.repo.git.merge_base("--is-ancestor", merge_sha, f"origin/{target_branch}")
            except GitCommandError:
                continue
            branches.append(pr.head.ref)

        return list(reversed(branches))

    def get_open_release_version(
        self,
        *,
        github_token: str,
        target_branch: str,
        branch_prefix: str,
        labels: list[str] | None = None,
    ) -> Version | None:
        """Return the highest version from open owned release PRs targeting target_branch."""
        repo_full_name = self._repo_full_name
        gh = Github(login_or_token=github_token)
        repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)
        highest: Version | None = None

        for pr in repo.get_pulls(state="open"):
            head_ref = pr.head.ref
            if pr.base.ref != target_branch:
                continue
            if not self._is_candidate_release_branch(head_ref, branch_prefix):
                continue
            pr_labels = [label.name for label in pr.labels]
            if labels and not any(label in pr_labels for label in labels):
                continue
            if PR_HIDDEN_MARKER not in (pr.body or ""):
                continue

            lock = self.get_lock_at_ref(f"origin/{head_ref}")
            if lock is None:
                continue

            if highest is None or lock.version > highest:
                highest = lock.version

        return highest

    def _is_candidate_release_branch(self, branch_name: str, branch_prefix: str) -> bool:
        """Return True for configured or legacy release branch names."""
        return self._branch_matches_prefix(branch_name, branch_prefix) or (
            branch_name.startswith(LEGACY_RELEASE_PREFIX)
            and branch_name != LEGACY_RELEASE_PREFIX.rstrip("/")
        )

    def _find_release_pr(
        self,
        *,
        github_token: str,
        branch_name: str,
        target_branch: str | None = None,
    ) -> PullRequest | None:
        repo: Repository = self._get_github_repo(
            github_token=github_token,
            repo_full_name=self._repo_full_name,
        )
        for pr in repo.get_pulls(state="all"):
            if pr.head.ref != branch_name:
                continue
            if target_branch and pr.base.ref != target_branch:
                continue
            return pr
        return None

    def is_auto_semver_release_branch(
        self,
        *,
        branch_name: str,
        github_token: str,
        branch_prefix: str,
        labels: list[str] | None = None,
        require_closed_pr: bool = False,
        skip_pr_check: bool = False,
    ) -> tuple[bool, str]:
        """
        Verify branch ownership for cleanup/delete operations.

        Returns:
            Tuple of (is_owned, skip_reason). skip_reason is empty when owned.
        """
        skip_reason = ""
        if not self._is_candidate_release_branch(branch_name, branch_prefix):
            skip_reason = "branch name does not match release prefix"
        else:
            lock = self.get_lock_at_ref(f"origin/{branch_name}")
            if lock is None:
                skip_reason = "no lockfile at branch tip"
            elif not lock.is_release_branch_lock() and not lock.is_legacy_managed_lock():
                skip_reason = "lock is not auto-semver managed"

        if skip_reason:
            return False, skip_reason

        if skip_pr_check:
            return True, ""

        pr = self._find_release_pr(github_token=github_token, branch_name=branch_name)
        if pr is None:
            return False, "no associated pull request"

        pr_reason = self._release_pr_ownership_reason(
            pr=pr,
            labels=labels,
            require_closed_pr=require_closed_pr,
        )
        if pr_reason:
            return False, pr_reason

        return True, ""

    def _release_pr_ownership_reason(
        self,
        *,
        pr: PullRequest,
        labels: list[str] | None,
        require_closed_pr: bool,
    ) -> str:
        """Return a skip reason when the release PR fails ownership checks."""
        if require_closed_pr and pr.state == "open":
            return "pull request still open"

        pr_labels = [label.name for label in pr.labels]
        if labels and not any(label in pr_labels for label in labels):
            return "pull request missing configured label"

        if PR_HIDDEN_MARKER not in (pr.body or ""):
            return "pull request missing auto-semver marker"

        return ""

    def _is_closeable_release_pr(
        self,
        *,
        branch_name: str,
        github_token: str,
        branch_prefix: str,
        labels: list[str] | None,
    ) -> tuple[bool, str]:
        """
        Decide whether an open release PR can be superseded in single mode.

        Accepts pre-ownership locks (no managed_by metadata) on candidate release
        branches so legacy release/* PRs are closed when a new release opens.
        """
        owned, reason = self.is_auto_semver_release_branch(
            branch_name=branch_name,
            github_token=github_token,
            branch_prefix=branch_prefix,
            labels=labels,
            skip_pr_check=True,
        )
        if owned:
            return True, ""

        lock = self.get_lock_at_ref(f"origin/{branch_name}")
        if lock is None:
            return False, reason or "no lockfile at branch tip"

        if lock.finalized:
            return False, "lock already finalized"

        if lock.is_preownership_release_lock() and self._is_candidate_release_branch(
            branch_name, branch_prefix
        ):
            return True, ""

        return False, reason or "lock is not auto-semver managed"

    def close_old_release_prs(
        self,
        *,
        github_token: str,
        target_branch: str,
        labels: list[str] | None = None,
        branch_prefix: str = DEFAULT_RELEASE_PREFIX,
        exclude_branch: str | None = None,
        delete_branches: bool = False,
    ) -> None:
        """
        Close open owned release PRs targeting the specified branch.

        Args:
            github_token: GitHub access token.
            target_branch: The target branch (e.g., 'dev' or 'main').
            labels: Optional list of label names to match.
            branch_prefix: Configured release branch prefix.
            exclude_branch: Optional branch name to keep open (current release).
            delete_branches: When True, delete each superseded release branch after closing.

        Raises:
            GithubException: If there is an error with the GitHub API.

        """
        repo_full_name = self._repo_full_name

        logger.info(f"Checking for existing PRs for target branch: {target_branch}")

        gh = Github(login_or_token=github_token)

        try:
            repo: Repository = gh.get_repo(full_name_or_id=repo_full_name)
            open_prs = repo.get_pulls(state="open")

            for pr in open_prs:
                head_ref: str = pr.head.ref
                base_ref: str = pr.base.ref

                if head_ref == exclude_branch:
                    continue

                if base_ref != target_branch:
                    continue

                if not self._is_candidate_release_branch(head_ref, branch_prefix):
                    continue

                pr_labels: list[str] = [label.name for label in pr.labels]
                if labels and not any(label in pr_labels for label in labels):
                    continue

                if PR_HIDDEN_MARKER not in (pr.body or ""):
                    continue

                owned, reason = self._is_closeable_release_pr(
                    branch_name=head_ref,
                    github_token=github_token,
                    branch_prefix=branch_prefix,
                    labels=labels,
                )
                if not owned:
                    logger.info("Skipping PR #%s (%s): %s", pr.number, head_ref, reason)
                    continue

                logger.info(f"Closing old PR #{pr.number}: {head_ref} → {base_ref}")
                pr.edit(state="closed")
                if delete_branches:
                    self._delete_superseded_release_branch(branch_name=head_ref)

        except GithubException as err:
            logger.error(f"GitHub API error while closing PRs: {err}")
            raise

    def cleanup_stale_release_branches(
        self,
        *,
        github_token: str,
        target_branch: str,
        labels: list[str] | None = None,
        branch_prefix: str = DEFAULT_RELEASE_PREFIX,
        exclude_branch: str | None = None,
    ) -> None:
        """
        Delete owned release branches that no longer have an open PR (single mode).

        Handles branches left behind when a previous bump closed the PR but did not
        delete the remote ref.
        """
        self.fetch()
        remote: Remote = self.repo.remote()
        candidates: list[str] = []

        for ref in remote.refs:
            branch_name = self._normalize_branch_name(ref.name)
            if branch_name == exclude_branch:
                continue
            if not self._is_candidate_release_branch(branch_name, branch_prefix):
                continue
            candidates.append(branch_name)

        for branch_name in sorted(set(candidates)):
            pr = self._find_release_pr(
                github_token=github_token,
                branch_name=branch_name,
                target_branch=target_branch,
            )
            if pr is not None and pr.state == "open":
                continue
            if pr is not None:
                pr_labels = [label.name for label in pr.labels]
                if labels and not any(label in pr_labels for label in labels):
                    continue
                if PR_HIDDEN_MARKER not in (pr.body or ""):
                    continue

            closeable, reason = self._is_closeable_release_pr(
                branch_name=branch_name,
                github_token=github_token,
                branch_prefix=branch_prefix,
                labels=labels,
            )
            if not closeable:
                logger.info("Skipping stale branch delete for %s: %s", branch_name, reason)
                continue

            self._delete_superseded_release_branch(branch_name=branch_name)

    def _delete_superseded_release_branch(self, *, branch_name: str) -> None:
        """Delete a superseded release branch, logging failures without raising."""
        try:
            self.delete_branch(branch_name=branch_name)
            logger.info("Deleted superseded release branch %s", branch_name)
        except Exception as err:
            logger.warning("Failed to delete superseded release branch %s: %s", branch_name, err)

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
            elif not filter_release_commits:
                logger.debug("Filtering of release commits is disabled.")
            elif not config:
                logger.warning("No config provided, skipping release commit filtering.")

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

    def get_file_content_at_commit(self, commit_sha: str, file_path: str) -> str | None:
        """
        Retrieve file content from a specific commit SHA.

        Args:
            commit_sha (str): The git commit SHA to read from.
            file_path (str): Relative path to the file in the repository.

        Returns:
            str | None: The file content as a string, or None if the file/commit is missing
                        or cannot be read.
        """
        try:
            logger.debug(f"Reading {file_path} at {commit_sha}")
            return str(self.repo.git.show(f"{commit_sha}:{file_path}"))
        except GitCommandError as e:
            logger.warning(f"Failed to read {file_path} at {commit_sha}: {e}")
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

        # Robust fallback: strict "Release " check if config extraction fails
        if not release_prefix:
            logger.warning(
                "No release prefix found in config title template. Falling back to default 'Release '."
            )
            # Default fallback for most common case
            release_prefix = "Release "
        else:
            logger.debug(f"Using config-based release prefix: '{release_prefix}'")

        filtered_messages = []

        for message in messages:
            # Normalize message for checking - only check the first line (title)
            first_line = message.splitlines()[0].strip() if message else ""

            if release_prefix and first_line.startswith(release_prefix):
                logger.debug(f"Filtering out release commit: {first_line}")
            else:
                filtered_messages.append(message)

        return filtered_messages
