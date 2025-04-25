import logging

from . import SEMVER_REGEX, SemverGroups

logger = logging.getLogger(__name__)


def version(file_content):
    logging.debug("Extracting version from file content.")

    match = SEMVER_REGEX.search(file_content)

    if not match:
        return None

    return {
        SemverGroups.TITLE: match.group(SemverGroups.TITLE.value),
        SemverGroups.STARTING_QUOTE: match.group(SemverGroups.STARTING_QUOTE.value),
        SemverGroups.PREFIX: match.group(SemverGroups.PREFIX.value),
        SemverGroups.VERSION: match.group(SemverGroups.VERSION.value),
        SemverGroups.SUFFIX: match.group(SemverGroups.SUFFIX.value),
        SemverGroups.ENDING_QUOTE: match.group(SemverGroups.ENDING_QUOTE.value),
    }
