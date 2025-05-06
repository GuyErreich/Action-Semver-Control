"""
Semantic versioning utilities for Auto-Semver pipelines.

This module provides a `Version` class for managing semantic versioning, including
parsing, bumping (major, minor, patch), setting suffixes, and converting to strings.

Typical usage example::

    version = Version.parse("1.2.3")
    version.bump_patch()
    version.set_suffix("-dev")
    print(str(version))  # "1.2.4-dev"
"""

import logging
import re

logger = logging.getLogger(__name__)

_VERSION_PATTERN = re.compile(
    r"^(?P<title>[\w\-]+:\s*)?"
    r"(?P<quote>[\"'])?"  # Optional opening quote
    r"(?P<prefix>v)?"
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?P<suffix>-[\w\d]+)?"
    r"(?P=quote)?$",
    re.MULTILINE,
)

_MAJOR_PREFIXES = ("breaking/", "major/")
_MINOR_PREFIXES = ("feature/",)
_PATCH_PREFIXES = ("fix/", "bug/", "hotfix/", "chore/", "devops/")


class Version:

    """
    Represents a semantic version, optionally with prefix, suffix, or title.

    Attributes:
        title (str | None): Optional title or label before version string.
        prefix (str | None): Optional 'v' prefix.
        major (int): Major version component.
        minor (int): Minor version component.
        patch (int): Patch version component.
        suffix (str | None): Optional suffix like '-dev' or '-rc.1'.
        quote (str | None): Optional surrounding quote (" or ').

    """

    def __init__(
        self,
        *,
        major: int,
        minor: int,
        patch: int,
        title: str | None = None,
        prefix: str | None = None,
        suffix: str | None = None,
        quote: str | None = None,
    ) -> None:
        """
        Initialize a Version object.

        Args:
            major (int): Major version number.
            minor (int): Minor version number.
            patch (int): Patch version number.
            title (str | None): Optional title or label before version string.
            prefix (str | None): Optional 'v' prefix.
            suffix (str | None): Optional suffix like '-dev' or '-rc.1'.
            quote (str | None): Optional surrounding quote (" or ').

        """

        self.major = major
        self.minor = minor
        self.patch = patch
        self.title = title
        self.prefix = prefix
        self.suffix = suffix
        self.quote = quote

    @staticmethod
    def parse(version_line: str) -> "Version":
        """
        Parse a version line and returns a Version object.

        Args:
            version_line: The raw version string to parse.

        Returns:
            A Version instance.

        Raises:
            ValueError: If the version format is invalid.

        """

        logger.debug(f"Parsing version line: {version_line}")

        match = _VERSION_PATTERN.match(version_line.strip())
        if not match:
            raise ValueError("Invalid version format")

        groups = match.groupdict()
        version = Version(
            title=groups.get("title", ""),
            prefix=groups.get("prefix", ""),
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            suffix=groups.get("suffix", ""),
            quote=groups.get("quote", ""),
        )

        logger.debug(
            f"Parsed version components - "
            f"Title: {version.title}, Prefix: {version.prefix}, Major: {version.major}, "
            f"Minor: {version.minor}, Patch: {version.patch}, Suffix: {version.suffix}, Quote: {version.quote}"
        )

        return version

    @staticmethod
    def detect_bump_type(branch_name: str) -> str:
        """
        Determine bump type based on Git branch naming conventions.

        This method analyzes the branch name to determine the type of version bump
        that should be applied. It categorizes the branch names into three types:
        - Major: For branches starting with 'breaking/' or 'major/'.
        - Minor: For branches starting with 'feature/'.
        - Patch: For branches starting with 'fix/', 'bug/', 'hotfix/', 'chore/',
          or 'devops/'.

        Note:
            If the branch name does not match any of these patterns, it defaults to 'patch'.

        Args:
            branch_name (str): The name of the branch to analyze.

        Returns:
            One of 'major', 'minor', or 'patch'.

        """

        bump_type: str = "patch"  # Default bump type

        logger.debug(f"Detecting bump type for branch: {branch_name}")

        if branch_name.startswith(_MAJOR_PREFIXES):
            bump_type = "major"
        elif branch_name.startswith(_MINOR_PREFIXES):
            bump_type = "minor"
        elif branch_name.startswith(_PATCH_PREFIXES):
            bump_type = "patch"

        logger.debug(f"Bump type detected: {bump_type}")

        return bump_type

    def bump_major(self) -> None:
        """Increments the major version and resets minor and patch to 0."""

        logger.info(f"Bumping major version: {self.major} -> {self.major + 1}")

        self.major += 1
        self.minor = 0
        self.patch = 0

    def bump_minor(self) -> None:
        """Increments the minor version and resets patch to 0."""

        logger.info(f"Bumping minor version: {self.minor} -> {self.minor + 1}")

        self.minor += 1
        self.patch = 0

    def bump_patch(self) -> None:
        """Increments the patch version."""

        logger.info(f"Bumping patch version: {self.patch} -> {self.patch + 1}")

        self.patch += 1

    def bump(self, *, branch_name: str) -> None:
        """
        Bumps the version based on the branch name.

        This method determines the type of version bump (major, minor, or patch)
        based on the branch name and applies the appropriate bump method.

        The branch name is analyzed to detect the type of change:
        - Major: For branches starting with 'breaking/' or 'major/'.
        - Minor: For branches starting with 'feature/'.
        - Patch: For branches starting with 'fix/', 'bug/', 'hotfix/', 'chore/',
          or 'devops/'.

        Note:
            If the branch name does not match any of these patterns, it defaults to 'patch'.

        Args:
            branch_name (str): The name of the branch to analyze.

        """

        bump_type: str = self.detect_bump_type(branch_name)

        match bump_type:
            case "major":
                self.bump_major()
            case "minor":
                self.bump_minor()
            case _:
                self.bump_patch()

    def set_suffix(self, *, suffix: str | None) -> None:
        """
        Set a new suffix (e.g. -dev, -rc.1) on the version.

        Args:
            suffix: Suffix string to apply or None to clear it.

        """

        logger.info(f"Setting suffix: {self.suffix} -> {suffix}")

        self.suffix = suffix

    def remove_suffix(self) -> None:
        """Remove the suffix from the version object."""

        logger.info(f"Removing suffix: {self.suffix}")

        self.suffix = None

    def __str__(self) -> str:
        """Return the version string in the format 'major.minor.patch' or 'major.minor.patch-suffix'."""

        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.suffix:
            version += self.suffix

        return f"{version}"

    def format_full_line(self) -> str:
        """Return the full version string, including title, prefix, and quotes if present."""

        version = f"{self.prefix or ''}{self}"
        version = f"{self.quote or ''}{version}{self.quote or ''}"

        if self.title is None:
            return version

        return f"{self.title} {version}"

    def merge_from(self, other: "Version") -> None:
        """
        Merge version components (major, minor, patch, suffix) from another Version instance.

        This method copies the version components from the provided Version instance
        to the current instance. It does not modify the title or prefix of the current instance.
        This is useful for updating the version components based on another Version instance.

        Note:
            This method does not return a new Version instance; it modifies the current instance in place.

        Example:
            version1 = Version(1, 2, 3)
            version2 = Version(4, 5, 6)
            version1.merge_from(version2)
            # version1 is now 4.5.6

        Args:
            other (Version): The Version instance from which to copy the version components.

        """

        self.major = other.major
        self.minor = other.minor
        self.patch = other.patch
        self.suffix = other.suffix
