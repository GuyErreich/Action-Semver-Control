import logging

import requests

logger = logging.getLogger(__name__)


def create_or_update_pr(token, repo, branch, base_branch, title, body):
    logger.debug(f"Creating or updating PR for branch: {branch}")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/repos/{repo}/pulls"

    existing_prs = requests.get(
        url + f"?head={repo.split('/')[0]}:{branch}&base={base_branch}", headers=headers
    ).json()
    if isinstance(existing_prs, list) and existing_prs:
        pr = existing_prs[0]
        pr_url = pr["html_url"]
        logger.info(f"PR already exists: {pr_url}")
        return

    data = {"title": title, "head": branch, "base": base_branch, "body": body}
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        pr_url = response.json()["html_url"]
        logger.info(f"PR created: {pr_url}")
    else:
        logger.error(f"Failed to create PR: {response.text}")
