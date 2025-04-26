"""Provides functionality to update version strings in files.

Functions:
----------
- update_version_file(path, new_version, suffix=None):
    Updates the version string in a file at the specified path. Searches for a
    version pattern, replaces it with the provided new version, and writes the
    updated content back to the file. Raises a ValueError if no version pattern
    is found or if the new version is empty.

Dependencies:
-------------
- logging: Used for logging debug information.
- versioning.SemverGroups: Enum for semantic versioning groups.
- versioning.extract.version: Function to extract version information from a string.

Example Usage:
--------------
"""

import logging

from versioning import SemverGroups
from versioning.extract import version

logger = logging.getLogger(__name__)


def update_version_file(path: str, new_version: str, suffix: str | None = None) -> None:
    """Update the version string in a file at the specified path.

    This function searches for a version pattern in the file, updates it with the
    provided new version, and writes the updated content back to the file. If no
    version pattern is found, a ValueError is raised.

    Args:
    ----
        path (str): The file path where the version string needs to be updated.
        new_version (str): The new version string to replace the existing one.
        suffix (str, optional): An optional suffix to append to the version string.

    Raises:
    ------
        ValueError: If the new_version is empty or if no version pattern is found
                    in the file.

    Example:
    -------
        Given a file with the content:
        ```
        version: "1.0.0"
        ```
        Calling `update_version_file("path/to/file", "2.0.0")` will update the file to:
        ```
        version: "2.0.0"
        ```

    """
    logger.debug(f"Updating version in {path}")

    if not new_version:
        raise ValueError("New version cannot be empty")

    with open(path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        groups = version(line)
        if not groups or not groups.get(SemverGroups.VERSION.name):
            continue

        logger.debug(f"Matched line: {line.strip()}")
        logger.debug(f"Preserved groups: {groups}")

        # Reconstruct version string from parts
        title = groups.get(SemverGroups.TITLE.name, "version: ")
        start_quote = groups.get(SemverGroups.STARTING_QUOTE.name) or ""
        prefix = groups.get(SemverGroups.PREFIX.name) or ""
        suffix = groups.get(SemverGroups.SUFFIX.name) or ""
        end_quote = groups.get(SemverGroups.ENDING_QUOTE.name) or ""

        full_version = f"{prefix}{new_version}{suffix}"
        new_line = f"{title}{start_quote}{full_version}{end_quote}\n"

        lines[i] = new_line
        break
    else:
        raise ValueError("No version pattern found")

    with open(path, "w") as f:
        f.writelines(lines)

    logger.debug(f"Version line updated to {new_line} in {path}")
