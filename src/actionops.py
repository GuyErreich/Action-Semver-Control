import json
import logging
import os

logger = logging.getLogger(__name__)


def extract_branch_from_event() -> str:
    logger.debug("Extracting branch name from GitHub event data")

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        logger.error("GITHUB_EVENT_PATH is not set in environment")
        raise RuntimeError("GITHUB_EVENT_PATH is not set in environment")

    logger.debug(f"Reading event data from {event_path}")

    with open(event_path) as f:
        event_data = json.load(f)

    if not event_data.get("pull_request", {}).get("merged", False):
        logger.error("The pull request was not merged.")
        raise RuntimeError("The pull request was closed but not merged.")

    branch_name: str = event_data["pull_request"]["head"]["ref"]
    if not branch_name:
        logger.error("Failed to extract branch name from event data")
        raise RuntimeError("Failed to extract merged branch name.")

    logger.debug(f"Extracted branch name: {branch_name}")

    return branch_name


def extract_commit_from_event() -> str:
    logger.debug("Extracting commit message from GitHub event data")

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        logger.error("GITHUB_EVENT_PATH is not set in environment")
        raise RuntimeError("GITHUB_EVENT_PATH is not set in environment")

    logger.debug(f"Reading event data from {event_path}")

    with open(event_path) as f:
        event_data = json.load(f)

    if not event_data.get("pull_request", {}).get("merged", False):
        logger.error("The pull request was not merged.")
        raise RuntimeError("The pull request was closed but not merged.")

    commit_sha: str = event_data["pull_request"]["head"]["sha"]
    if not commit_sha:
        logger.error("Failed to extract commit sha from event data.")
        raise RuntimeError("Failed to extract merged commit sha.")

    logger.debug(f"Extracted commit: {commit_sha}")

    return commit_sha
