import git
import requests
from typing import Any, List

class GitOps:
    def __init__(self, repo_path: str = ".") -> None:
        self.repo = git.Repo(repo_path)

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
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        pr_number = response.json()["number"]

        # Label the PR
        self.add_label_to_pr(github_token, repo_full_name, pr_number, "semver-bump")
        
        return pr_number

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