"""
CHANGELOG management module.

This module provides a class for appending or truncating changelog entries
based on a semantic versioning context. It is typically used during CI/CD release
automation in GitHub Actions workflows.

Typical usage::

    manager = ChangelogManager()
    manager.write("1.0.1", ["Fix bug", "Improve logging"])
"""

import datetime
import logging
from pathlib import Path
from string import Template

from src.config import Config

logger = logging.getLogger(__name__)


_DEFAULT_COMMIT_PLACEHOLDER: str = "Miscellaneous changes"

class ChangelogManager:

    """
    Manage the changelog file, allowing updates and truncation.
    
    This class supports rendering a changelog entry using a customizable template,
    with options to append to or truncate the changelog content.
    It also supports loading configuration from a `Config` instance.
    """

    def __init__(
        self,
        *,
        path: str,
        truncate: bool,
        template: str,
        header: str,
        footer: str,
    ) -> None:
        """
        Initialize the changelog manager with user-provided parameters.

        Args:
            path (str): Path to the changelog file.
            truncate (bool): Whether to overwrite existing changelog content.
            template (str): The Jinja-style template for the changelog entry.
            header (str): Header content of the changelog file.
            footer (str): Footer content of the changelog file.

        """
        self.path = Path(path)
        self.truncate = truncate
        self.template = template
        self.header = header
        self.footer = footer

    @classmethod
    def from_config(cls, config: Config) -> 'ChangelogManager':
        """
        Instantiate the manager using values from a Config instance.

        Args:
            config: The Config instance to extract changelog parameters from.

        Returns:
            ChangelogManager instance initialized from the config.

        """
        return cls(
            path=config.get_changelog_file(),
            truncate=config.should_truncate_changelog(),
            template=config.get_changelog_template(),
            header=config.get_changelog_header(),
            footer=config.get_changelog_footer(),
        )


    def update(self, *, version: str, messages: list[str]) -> None:
        """
        Update the changelog file with the provided version and commit messages.

        Args:
            version: The version string to record (e.g., 1.2.3).
            messages: A list of commit messages to include under the version.

        Raises:
            IOError: If writing to the changelog file fails.

        """
        if not messages:
            logger.warning("No commit messages provided. Adding default message.")
            messages = [_DEFAULT_COMMIT_PLACEHOLDER]

        formatted_message: str = "\n".join(f"- {msg}" for msg in messages)
        rendered: str = Template(self.template).substitute(
            version=version,
            date=datetime.date.today().isoformat(),
            message=formatted_message,
        )

        logger.info("Updating changelog file.")
        if not self.path.exists():
            logger.warning("Changelog file not found. Creating a new file.")
            content = self._compose_new_changelog(rendered)
        else:
            with open(self.path, encoding="utf-8") as f:
                existing = f.read().strip()
            content = self._compose_updated_changelog(existing=existing, rendered=rendered)

        with open(self.path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Changelog update complete.")

    def _compose_new_changelog(self, rendered: str) -> str:
        """
        Compose the initial changelog content.

        Args:
            rendered: The newly rendered changelog entry.

        Returns:
            Combined changelog string.

        """
        parts = [self.header.strip(), rendered.strip(), self.footer.strip()]
        return "\n\n".join(part for part in parts if part)

    def _compose_updated_changelog(self, *, existing: str, rendered: str) -> str:
        """
        Compose the updated changelog content, either truncating or prepending.

        Args:
            existing: The existing changelog content.
            rendered: The newly rendered changelog entry.

        Returns:
            Updated changelog content as a string.

        """
        if self.truncate:
            return self._compose_new_changelog(rendered)

        parts = [self.header.strip(), rendered.strip(), existing.strip(), self.footer.strip()]
        return "\n\n".join(part for part in parts if part)
