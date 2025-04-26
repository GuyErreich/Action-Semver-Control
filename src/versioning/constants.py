"""Defines constants and utilities for semantic versioning.

Classes
-------
SemverGroups : Enum
    Represents components of a semantic version string.

Constants
---------
SEMVER_REGEX : re.Pattern
    Compiled regex for matching and extracting semantic version components.

Notes
-----
`SEMVER_REGEX` uses named capturing groups matching `SemverGroups` to extract parts of a version string.


"""

import re
from enum import Enum, auto, unique


@unique
class SemverGroups(Enum):
    """Represents components of a semantic version string.

    Attributes
    ----------
        TITLE: Title or identifier of the version.
        STARTING_QUOTE: Starting quote in the version string.
        PREFIX: Prefix before the version number (e.g., 'v').
        VERSION: The semantic version number (e.g., '1.0.0').
        SUFFIX: Suffix after the version (e.g., '-alpha').
        ENDING_QUOTE: Ending quote in the version string.

    """

    TITLE = auto()
    STARTING_QUOTE = auto()
    PREFIX = auto()
    VERSION = auto()
    SUFFIX = auto()
    ENDING_QUOTE = auto()


SEMVER_REGEX = re.compile(
    rf"(?P<{SemverGroups.TITLE.name}>version:\s*)"
    rf'(?P<{SemverGroups.STARTING_QUOTE.name}>["\']?)'  # opening quote
    rf"(?P<{SemverGroups.PREFIX.name}>v?)"  # optional prefix v
    rf"(?P<{SemverGroups.VERSION.name}>\d+\.\d+\.\d+)"  # main version
    rf"(?P<{SemverGroups.SUFFIX.name}>-[\w]+)?"  # optional suffix like -dev
    rf'(?P<{SemverGroups.ENDING_QUOTE.name}>["\']?)'  # optional closing quote
)
