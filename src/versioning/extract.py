"""Extracts semantic versioning components from file content using a regular expression.

It defines the `version` function, which parses the file content and maps the
matched groups to their corresponding semantic versioning components (e.g., major,
minor, patch) as defined in the `SemverGroups` enumeration.
"""

import logging

from . import SEMVER_REGEX, SemverGroups

logger = logging.getLogger(__name__)


def version(file_content: str) -> dict[str, str | None]:
    """Extract semantic versioning components from the given file content.

    This function uses a predefined regular expression (SEMVER_REGEX) to search
    for semantic versioning information in the provided file content. It maps
    the matched groups to their corresponding semantic versioning components
    (e.g., major, minor, patch) as defined in the `SemverGroups` enumeration.

    Args:
    ----
        file_content (str): The content of the file to extract the version from.

    Returns:
    -------
        dict: A dictionary where the keys are the names of the semantic versioning
        components (e.g., 'MAJOR', 'MINOR', 'PATCH'), and the values are the
        corresponding extracted values as strings, or None if not found.

    """
    logging.debug("Extracting version from file content.")

    match = SEMVER_REGEX.search(file_content)

    groups = {}
    for group in SemverGroups:
        name = group.name
        value: str | None  # Ensure value is explicitly typed as Optional[str]

        if match:
            value = match.group(group.name)
            groups[name] = value or None
        else:
            groups[name] = None

    return groups
