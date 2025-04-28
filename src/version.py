import re
import logging

logger = logging.getLogger(__name__)

class Version:
    version_pattern = re.compile(
        r'^(?P<title>[\w\-]+:)?\s*(?P<prefix>v)?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?P<suffix>-[\w\d]+)?$',
        re.MULTILINE
    )

    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        title: str = "version:",
        prefix: str | None = None,
        suffix: str | None = None
    ) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch
        self.title = title
        self.prefix = prefix
        self.suffix = suffix

    @classmethod
    def parse(cls, version_line: str) -> 'Version':
        """
        Parse a full version line like 'version: v1.2.3-dev' into a Version object.
        """
        logger.debug(f"Parsing version line: {version_line}")
        match = cls.version_pattern.match(version_line.strip())
        if not match:
            logger.error(f"Invalid version format: {version_line}")
            raise ValueError(f"Invalid version format: {version_line}")

        groups = match.groupdict()
        major = int(groups['major'])
        minor = int(groups['minor'])
        patch = int(groups['patch'])
        title = groups['title']
        prefix = groups.get('prefix')
        suffix = groups.get('suffix')

        logger.debug(f"Parsed version components - Title: {title}, Prefix: {prefix}, Major: {major}, Minor: {minor}, Patch: {patch}, Suffix: {suffix}")
        return cls(major, minor, patch, title, prefix, suffix)

    def __str__(self) -> str:
        """
        Format the Version object back into a full version line string.
        """
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.suffix:
            version += self.suffix
        if self.prefix:
            version = f"{self.prefix}{version}"
        return f"{self.title} {version}"

    def bump_major(self) -> None:
        logger.info(f"Bumping major version: {self.major} -> {self.major + 1}")
        self.major += 1
        self.minor = 0
        self.patch = 0

    def bump_minor(self) -> None:
        logger.info(f"Bumping minor version: {self.minor} -> {self.minor + 1}")
        self.minor += 1
        self.patch = 0

    def bump_patch(self) -> None:
        logger.info(f"Bumping patch version: {self.patch} -> {self.patch + 1}")
        self.patch += 1

    def set_suffix(self, suffix: str | None) -> None:
        logger.info(f"Setting suffix: {self.suffix} -> {suffix}")
        self.suffix = suffix

    def remove_suffix(self) -> None:
        logger.info(f"Removing suffix: {self.suffix}")
        self.suffix = None