import re
from enum import Enum


class SemverGroups(Enum):
    TITLE = "title"
    STARTING_QUOTE = "starting_quote"
    PREFIX = "prefix"
    VERSION = "version"
    SUFFIX = "suffix"
    ENDING_QUOTE = "ending_quote"


SEMVER_REGEX = re.compile(
    rf"(?P<{SemverGroups.TITLE.value}>version:\s*)"
    rf'(?P<{SemverGroups.STARTING_QUOTE.value}>["\']?)'  # opening quote
    rf"(?P<{SemverGroups.PREFIX.value}>v?)"  # optional prefix v
    rf"(?P<{SemverGroups.VERSION.value}>\d+\.\d+\.\d+)"  # main version
    rf"(?P<{SemverGroups.SUFFIX.value}>-[\w]+)?"  # optional suffix like -dev
    rf'(?P<{SemverGroups.ENDING_QUOTE.value}>["\']?)'  # optional closing quote
)
