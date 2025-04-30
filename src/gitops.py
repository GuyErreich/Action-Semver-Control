import time
import git
import requests
from typing import Any, List
import logging

logger = logging.getLogger(__name__)

class GitOps:
    def __init__(self, repo_path: str = ".") -> None:
        self.repo = git.Repo(repo_path)
        self.ensure_git_safe_directory()

    def create_branch(self, branch_name: str, overwrite: bool) -> None:
        if overwrite and branch_name in self.repo.heads:
            old_branch = self.repo.heads[branch_name]
            self.repo.delete_head(old_branch, force=True)
        self.repo.git.checkout('-b', branch_name)

    def push_branch(self, branch_name: str) -> None:
        self.repo.git.push('--set-upstream', 'origin', branch_name, force=True)

    def create_pr(self, github_token: str, repo_full_name: str, title: str, head: str, base: str) -> int:
        url = f"https://api.github.com/repos/{repo_full_name}/pulls"
        headers = {"Authorization": f"token {github_token}"}
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": "Auto-created PR by auto-semver."
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
                return pr_number
            elif response.status_code == 422:
                logger.warning("PR creation failed with status 422. Retrying after 2 seconds...")
                try:
                    logger.warning(f"GitHub 422 response: {response.json()}")
                except Exception:
                    logger.warning("Could not decode 422 response body.")
            else:
                logger.error(f"PR creation failed with status {response.status_code}. Response: {response.text}")
                response.raise_for_status()
            
            time.sleep(2)  # Wait 2 seconds and retry

        logger.error("Failed to create PR after multiple attempts.")
        response.raise_for_status()

    def add_label_to_pr(self, github_token: str, repo_full_name: str, pr_number: int, label: str) -> None:
        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/labels"
        headers = {"Authorization": f"token {github_token}"}
        data = {"labels": [label]}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

    def close_old_release_prs(self, github_token: str, repo_full_name: str) -> None:
        url = f"https://api.github.com/repos/{repo_full_name}/pulls?state=open&head={repo_full_name.split('/')[0]}:release/"
        headers = {"Authorization": f"token {github_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        prs = response.json()

        for pr in prs:
            pr_number = pr["number"]
            close_url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
            requests.patch(close_url, headers=headers, json={"state": "closed"})

    def get_recent_commits(self, base_branch: str) -> List[str]:
        """
        Get commit messages between base_branch and HEAD.
        """
        commits = list(self.repo.iter_commits(f"{base_branch}..HEAD"))
        return [commit.message.strip() for commit in reversed(commits)]
    
    def ensure_git_safe_directory(self) -> None:
        path = self.repo.working_tree_dir
        git_config = self.repo.config_writer(config_level='global')

        try:
            safe_dirs = git_config.get_value('safe', 'directory')
            if isinstance(safe_dirs, str):
                safe_dirs = [safe_dirs]
        except Exception:
            safe_dirs = []

        if path not in safe_dirs:
            git_config.set_value('safe', 'directory', path)
            git_config.release()

    def commit_version_changes(self, files: list[str], new_version: str) -> None:
        logger.info(f"Staging version bump files: {files}")

        if not self.repo.is_dirty(untracked_files=True):
            logger.warning("Repo is not dirty — no changes staged or committed.")
        else:
            logger.debug("Repo has staged/committed changes.")

        for file_path in files:
            try:
                self.repo.git.add(file_path)
                logger.debug(f"Added {file_path} to git staging.")
            except Exception as e:
                logger.error(f"Failed to add {file_path} to git: {e}")
                raise