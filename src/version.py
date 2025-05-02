import logging
import re

logger = logging.getLogger(__name__)


class Version:

    """
    Version Class.

    The `Version` class provides a structured representation of semantic versioning
    and includes methods for parsing, formatting, and manipulating version strings.
    It supports semantic versioning components (major, minor, patch) and additional
    attributes such as title, prefix, suffix, and quote.

    Attributes:
        version_pattern (re.Pattern): A compiled regular expression pattern for
            parsing version strings.

    Methods:
        __init__(self, major, minor, patch, title, prefix, suffix, quote):
            Initialize a `Version` object with version components and optional
            attributes.

        parse(cls, version_line):
            Parse a version string into a `Version` object.

        __str__(self):
            Return a string representation of the `Version` object.

        format_full_line(self):
            Format and return the full version line as a string.

        merge_from(self, other):
            Merge version components (major, minor, patch, suffix) from another
            `Version` instance.

        detect_bump_type(self, branch_name):

        bump(self, branch_name):
            Determine the type of version bump based on the branch name and apply
            the appropriate bump.

        bump_major(self):

        bump_minor(self):
            Increment the minor version number by 1 and reset the patch version to 0.

        bump_patch(self):
            Increment the patch version number by 1.

        set_suffix(self, suffix):

        remove_suffix(self):

    """

    version_pattern = re.compile(
        r"^(?P<title>[\w\-]+:\s*)?"
        r'(?P<quote>["\'])?'  # Optional opening quote
        r"(?P<prefix>v)?"
        r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        r"(?P<suffix>-[\w\d]+)?"
        r"(?P=quote)?$",
        re.MULTILINE,
    )

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        title: str = "version:",
        prefix: str | None = None,
        suffix: str | None = None,
        quote: str | None = None,
    ) -> None:
        """
        Initialize a version object.

        This method sets the major, minor, and patch version numbers,
        along with optional attributes such as title, prefix, suffix,
        and quote.

        Note:
            - The title is included only if it is not None.
            - The prefix is included only if it is not None.
            - The version number is always included.
            - The suffix is included only if it is not None.
            - The quote is included only if it is not None.

        Args:
            major (int): The major version number.
            minor (int): The minor version number.
            patch (int): The patch version number.
            title (str, optional): A title or label for the version. Defaults to "version:".
            prefix (str | None, optional): A prefix to prepend to the version string. Defaults to None.
            suffix (str | None, optional): A suffix to append to the version string. Defaults to None.
            quote (str | None, optional): A quote style to wrap the version string. Defaults to None.

        """

        self.major = major
        self.minor = minor
        self.patch = patch
        self.title = title
        self.prefix = prefix
        self.suffix = suffix
        self.quote = quote

    @classmethod
    def parse(cls, version_line: str) -> "Version":
        """
        Parse a version string into a Version object.

        Args:
            version_line (str): A string representing the version line,
            e.g., 'version: v1.2.3-dev'.

        Returns:
            Version: An instance of the Version class with parsed components.

        Raises:
            ValueError: If the version string does not match the expected format.

        """

        logger.debug(f"Parsing version line: {version_line}")

        match = cls.version_pattern.match(version_line.strip())
        if not match:
            raise ValueError("Invalid version format")

        groups = match.groupdict()
        major = int(groups["major"])
        minor = int(groups["minor"])
        patch = int(groups["patch"])
        title = groups.get("title", "")
        prefix = groups.get("prefix", "")
        suffix = groups.get("suffix", "")
        qoute = groups.get("quote", "")

        logger.debug(
            f"Parsed version components - "
            f"Title: {title}, Prefix: {prefix}, Major: {major}, "
            f"Minor: {minor}, Patch: {patch}, Suffix: {suffix}, Quote: {qoute}"
        )

        return cls(major, minor, patch, title, prefix, suffix, qoute)

    def __str__(self) -> str:
        """
        Return a string representation of the Version object.

        This method formats the version number as a string in the format:
        'major.minor.patch[-suffix]', where:
        - major: The major version number.
        - minor: The minor version number.
        - patch: The patch version number.
        - suffix: An optional suffix that can be appended to the version number.

        Note:
            - The suffix is included only if it is not None.
            - The version number is always included.

        Example:
            version = Version(1, 2, 3, suffix="-dev")
            print(str(version))
            # Output: '1.2.3-dev'

        Returns:
            str: The formatted version string.

        """

        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.suffix:
            version += self.suffix

        return f"{version}"

    def format_full_line(self) -> str:
        """
        Format and returns the full version line as a string.

        This method constructs a formatted version string based on the
        attributes of the Version object. It includes the title, prefix,
        version number, and optional quote. The format is as follows:
        '[title] [prefix][version][quote]', where each component is
        included only if it is not None.

        This method is useful for generating a complete version string
        that can be used in various contexts, such as displaying the
        version in a user interface or logging it for tracking purposes.

        Note:
            - The title is included only if it is not None.
            - The prefix is included only if it is not None.
            - The version number is always included.
            - The quote is included only if it is not None.

        Example:
            version = Version(1, 2, 3, title="version:", prefix="v", quote='"')
            print(version.format_full_line())  # Output: 'version: v1.2.3"'


        Returns:
            str: A formatted version string in the format:
                 '[title] [prefix][version][quote]'

        """

        version = str(self)  # Just 1.2.3[-suffix]

        if self.prefix:
            version = f"{self.prefix}{version}"

        if self.quote:
            version = f"{self.quote}{version}{self.quote}"

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

        Returns:
            None

        """

        self.major = other.major
        self.minor = other.minor
        self.patch = other.patch
        self.suffix = other.suffix

    def detect_bump_type(self, branch_name: str) -> str:
        """
        Detect the semantic version bump type based on the branch name.

        This method analyzes the branch name to determine the type of version bump
        that should be applied. It categorizes the branch names into three types:
        - Major: For branches starting with 'breaking/' or 'major/'.
        - Minor: For branches starting with 'feature/'.
        - Patch: For branches starting with 'fix/', 'bug/', 'hotfix/', 'chore/',
          or 'devops/'.
        If the branch name does not match any of these patterns, it defaults to 'patch'.
        The detected bump type is logged for tracking purposes.

        Args:
            branch_name (str): The name of the branch to analyze.

        Returns:
            str: The detected bump type, which can be one of the following:
                - 'major': For branches starting with 'breaking/' or 'major/'.
                - 'minor': For branches starting with 'feature/'.
                - 'patch': For branches starting with 'fix/', 'bug/', 'hotfix/',
                  'chore/', or 'devops/'. Defaults to 'patch' if no match is found.
        Logs:
            Logs the branch name being analyzed and the detected bump type.

        """

        bump_type: str = "patch"  # Default bump type

        logger.debug(f"Detecting bump type for branch: {branch_name}")

        if branch_name.startswith(("breaking/", "major/")):
            bump_type = "major"
        elif branch_name.startswith(("feature/",)):
            bump_type = "minor"
        elif branch_name.startswith(("fix/", "bug/", "hotfix/", "chore/", "devops/")):
            bump_type = "patch"

        logger.debug(f"Bump type detected: {bump_type}")

        return bump_type

    def bump(self, branch_name: str) -> None:
        """
        Determine the type of version bump based on the branch name and applies the appropriate bump.

        This method uses the branch name to detect the type of version bump (major, minor, or patch)
        and applies the corresponding bump by calling the appropriate method (`bump_major`, `bump_minor`,
        or `bump_patch`).

        Args:
            branch_name (str): The name of the branch used to determine the type of version bump.

        Example:
            If the branch name is 'feature/new-feature', the method will apply a minor version bump.

        Returns:
            None

        """

        bump_type: str = self.detect_bump_type(branch_name)

        if bump_type == "major":
            self.bump_major()
        elif bump_type == "minor":
            self.bump_minor()
        else:
            self.bump_patch()

    def bump_major(self) -> None:
        """
        Increment the major version number by 1.

        This method increases the major version by 1 while resetting the minor
        and patch version numbers to 0. It also logs the version change for
        tracking purposes.

        Example:
            If the current version is 2.3.4, calling this method will update
            the version to 3.0.0.

        Returns:
            None

        """

        logger.info(f"Bumping major version: {self.major} -> {self.major + 1}")
        self.major += 1
        self.minor = 0
        self.patch = 0

    def bump_minor(self) -> None:
        """
        Increment the minor version by 1 and reset the patch version to 0.

        This method updates the `minor` attribute by incrementing its value by 1.
        Additionally, it resets the `patch` attribute to 0 to reflect the start
        of a new minor version series.

        Returns:
            None

        """

        logger.info(f"Bumping minor version: {self.minor} -> {self.minor + 1}")
        self.minor += 1
        self.patch = 0

    def bump_patch(self) -> None:
        """
        Increment the patch version by 1.

        This method updates the `patch` attribute of the version object.

        Example:
            If the current patch version is 2, calling this method will
            update it to 3.

        Returns:
            None

        """

        logger.info(f"Bumping patch version: {self.patch} -> {self.patch + 1}")
        self.patch += 1

    def set_suffix(self, suffix: str | None) -> None:
        """
        Set the suffix for the version.

        This method updates the `suffix` attribute of the version object.

        Args:
            suffix (str | None): The new suffix to set.

        Returns:
            None

        """

        logger.info(f"Setting suffix: {self.suffix} -> {suffix}")
        self.suffix = suffix

    def remove_suffix(self) -> None:
        """
        Remove the suffix from the version object.

        This method sets the `suffix` attribute of the version object to `None`.

        Returns:
            None

        """

        logger.info(f"Removing suffix: {self.suffix}")
        self.suffix = None
