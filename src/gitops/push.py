import logging
import time

from git import GitCommandError

logger = logging.getLogger(__name__)


def push_with_retry(remote, branch, retries=3, delay=3):
    for attempt in range(retries):
        try:
            remote.push(branch)
            logger.info(f"Pushed branch '{branch}' to remote.")
            return
        except GitCommandError as e:
            logger.warning(f"Push failed (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    logger.error(f"Failed to push branch {branch} after {retries} attempts.")
    raise SystemExit(1)
