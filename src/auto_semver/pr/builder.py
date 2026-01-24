"""
Abstract PRBuilder for provider-agnostic pull request content generation.

Defines the interface for building PR title, body, and labels from templates and data.
Provider-specific builders should inherit from this class and implement the build methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from auto_semver.config._models._commit_group import CommitGroup, CommitGroups
from auto_semver.templates.engine import get_template_engine
from auto_semver.templates.types import TemplateFunction
from auto_semver.templates.utils import (
    capitalize_first_letter,
    extract_prefix_before_delimiter,
    format_date_iso_to_custom,
    truncate_text,
)


# Base template variables for PR builders
@dataclass
class BasePRTemplateVariables:
    """Base template variables for PR builders."""

    version: str
    previous_version: str
    commit_groups: CommitGroups
    breaking_changes: list[str]
    author: str
    repository: str
    date: str
    branch: str
    base_branch: str
    labels: list[str] | None = None


class PRBuilder[T: BasePRTemplateVariables](ABC):
    """Abstract base class for building pull request content (title, body, labels) from templates and data.

    Instantiate with data, and title, body, labels properties are automatically rendered and ready to use.
    """

    def __init__(self, data: T) -> None:
        """Initialize the PR builder with data and auto-render all content.

        Args:
            data: Template variables data for rendering PR content
        """
        self._engine = get_template_engine()
        self._data = data

        # Setup: register functions and variables
        self._register_shared_functions()
        self._register_template_variables()

        # Auto-render and store as properties
        self.title: str = self._build_title()
        self.body: str = self._build_body()
        self.labels: list[str] = self._build_labels()

    def _register_shared_functions(self) -> None:
        """
        Register shared template functions for all builders.

        Built-in functions (see engine docs) are already available and should not be re-registered.
        """
        shared_functions: dict[str, TemplateFunction] = {
            "truncate_commit": self.truncate_commit,
            "format_date_custom": self.format_date_custom,
            "conventional_type": self.conventional_type,
            "capitalize_first": self.capitalize_first,
            "count_commits": self.count_commits,
            "has_breaking": self.has_breaking,
            "count_groups": self.count_groups,
        }

        # Only register functions that are not already present in the engine
        for name, func in shared_functions.items():
            if name not in self._engine.env.globals:
                self._engine.register_function(name, func)

    # Shared utility methods available to all builders
    def truncate_commit(self, msg: str, length: int = 72) -> str:
        """Truncate commit message to specified length."""
        return truncate_text(msg, length)

    def format_date_custom(self, date_str: str, fmt: str = "%Y-%m-%d") -> str:
        """Format date string with custom format."""
        return format_date_iso_to_custom(date_str, fmt)

    def conventional_type(self, msg: str) -> str:
        """Extract conventional commit type from message."""
        return extract_prefix_before_delimiter(msg, ":")

    def capitalize_first(self, text: str) -> str:
        """Capitalize first letter of text."""
        return capitalize_first_letter(text)

    def count_commits(self, groups: list[CommitGroup] | None) -> int:
        """Count total commits across groups."""
        if not groups:
            return 0
        return sum(len(group.commits) for group in groups)

    def has_breaking(self, groups: list[CommitGroup] | None) -> bool:
        """Check if there are breaking changes."""
        if not groups:
            return False
        return any("breaking" in group.title.lower() or "🔥" in group.title for group in groups)

    def count_groups(self, groups: list[CommitGroup] | None) -> int:
        """Count number of commit groups."""
        return len(groups) if groups else 0

    @abstractmethod
    def _register_template_variables(self) -> None:
        """Register template variables specific to this PR builder type.

        Should be called once during __init__ to register variables with the template engine.
        """
        pass

    @abstractmethod
    def _build_title(self) -> str:
        """Build the PR title from template and self._data."""
        pass

    @abstractmethod
    def _build_body(self) -> str:
        """Build the PR body from template and self._data."""
        pass

    @abstractmethod
    def _build_labels(self) -> list[str]:
        """Build the PR labels from template and self._data."""
        pass
