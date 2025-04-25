import logging

from versioning import SemverGroups
from versioning.extract import version

logger = logging.getLogger(__name__)


def update_version_file(path, new_version, suffix=None):
    logger.debug(f"Updating version in {path}")

    if not new_version:
        raise ValueError("New version cannot be empty")

    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        groups = version(line)
        if not groups:
            continue

        logger.debug(f"Matched line: {line.strip()}")
        logger.debug(f"Preserved groups: {groups}")

        # Reconstruct version string from parts
        title = groups.get(SemverGroups.TITLE, "version: ")
        start_quote = groups.get(SemverGroups.STARTING_QUOTE) or ""
        prefix = groups.get(SemverGroups.PREFIX) or ""
        suffix = groups.get(SemverGroups.SUFFIX) or ""
        end_quote = groups.get(SemverGroups.ENDING_QUOTE) or ""

        full_version = f"{prefix}{new_version}{suffix}"
        new_line = f"{title}{start_quote}{full_version}{end_quote}\n"

        lines[i] = new_line
        break
    else:
        raise ValueError("No version pattern found")

    with open(path, "w") as f:
        f.writelines(lines)

    logger.debug(f"Version line updated to {new_line} in {path}")
