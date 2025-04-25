import logging

logger = logging.getLogger(__name__)

BRANCH_BUMP_MAP = {"feature": "minor", "fix": "patch", "breaking": "major"}


def parse_bump(branch, default):
    logger.debug(f"Parsing bump from branch: {branch}")
    for prefix, bump in BRANCH_BUMP_MAP.items():
        if branch.startswith(f"{prefix}/"):
            logger.debug(f"Match found: {prefix} -> {bump}")
            return bump
    logger.debug(f"No match found. Using default: {default}")
    return default


def bump_version(version, bump_type, suffix=None):
    logger.debug(f"Bumping version {version} with type {bump_type} and suffix {suffix}")
    version = version.lstrip("v")
    base_version = version.split("-")[0]
    major, minor, patch = map(int, base_version.split("."))
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    new_version = f"v{major}.{minor}.{patch}"
    if suffix and suffix.lower() in ["dev", "staging"]:
        new_version += f"-{suffix.lower()}"
    logger.debug(f"New version: {new_version}")
    return new_version
