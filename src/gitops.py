import logging
import time

import requests
from git import Commit, Head, Remote, Repo

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

    def create_pr(
        self, github_token: str, repo_full_name: str, title: str, head: str, base: str
    ) -> None:
        url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        headers = {"Authorization": f"token {github_token}"}
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": "Auto-created PR by auto-semver.",
        }

        logger.debug("Creating PR with the following parameters:")
        logger.debug(f"  Repo: {repo_full_name}")
        logger.debug(f"  Title: {title}")
        logger.debug(f"  Head (source): {head}")
        logger.debug(f"  Base (target): {base}")

        # Small wait to ensure GitHub sees the pushed branch
        for attempt in range(10):
            logger.debug(f"Attempt {attempt + 1}")
            response = requests.post(url, headers=headers, json=data)
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code == 201:
                pr_number = response.json()["number"]
                logger.info(f"PR created successfully with number: {pr_number}")
                self.add_label_to_pr(github_token, repo_full_name, pr_number, "semver-bump")
            elif response.status_code == 422:
                logger.warning("PR creation failed with status 422. Retrying after 2 seconds...")
                try:
                    logger.warning(f"GitHub 422 response: {response.json()}")
                except Exception:
                    logger.warning("Could not decode 422 response body.")
            else:
                logger.error(
                    f"PR creation failed with status {response.status_code}. Response: {response.text}"
                )
                response.raise_for_status()

            time.sleep(2)  # Wait 2 seconds and retry

        logger.error("Failed to create PR after multiple attempts.")
        response.raise_for_status()

    def add_label_to_pr(
        self, github_token: str, repo_full_name: str, pr_number: int, label: str
    ) -> None:
        """
        Add a label to a pull request.

        This method adds a specified label to a pull request in a GitHub repository.
        It uses the GitHub API to perform the operation.
        The method constructs the API URL for adding a label to the pull request,
        sets the authorization header with the provided GitHub token, and sends a POST request
        with the label data in JSON format.

        Note:
            - The label must already exist in the repository.
            - The method raises an HTTPError if the request fails.

        Args:
            github_token (str): The personal access token for authenticating with the GitHub API.
            repo_full_name (str): The full name of the repository in the format "owner/repo".
            pr_number (int): The pull request number to which the label will be added.
            label (str): The label to add to the pull request.

        Raises:
            requests.exceptions.HTTPError: If the GitHub API request fails.
        Logs:
            - Logs an info message indicating the label being added.
            - Logs a debug message with the response status code.
            - Logs an error message if adding the label fails.

        """
        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/labels"
        headers = {"Authorization": f"token {github_token}"}
        data = {"labels": [label]}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    def close_old_release_prs(self, github_token: str, repo_full_name: str) -> None:
        """
        Close all open release pull requests.

        Close all open pull requests in a GitHub repository that have a head branch
        starting with "release/".

        Args:
            github_token (str): The personal access token for authenticating with the GitHub API.
            repo_full_name (str): The full name of the repository in the format "owner/repo".

        Raises:
            requests.exceptions.HTTPError: If the GitHub API request fails.

        Logs:
            - Logs an info message indicating the start of the operation.
            - Logs a debug message with the number of PRs found.
            - Logs an info message for each PR being closed.
            - Logs an error message if closing a PR fails.

        """
        logger.info("Starting to close old release pull requests.")
        
        url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=open&head={repo_full_name.split('/')[0]}:release/"
        headers = {"Authorization": f"token {github_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            prs = response.json()
            logger.debug(f"Found {len(prs)} open release pull requests.")
        except Exception as e:
            logger.error(f"Failed to fetch open release pull requests: {e}")
            raise

        for pr in prs:
            pr_number = pr["number"]
            close_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
            try:
                logger.info(f"Closing pull request #{pr_number}.")
                close_response = requests.patch(close_url, headers=headers, json={"state": "closed"})
                close_response.raise_for_status()
                logger.info(f"Successfully closed pull request #{pr_number}.")
            except Exception as e:
                logger.error(f"Failed to close pull request #{pr_number}: {e}")
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
