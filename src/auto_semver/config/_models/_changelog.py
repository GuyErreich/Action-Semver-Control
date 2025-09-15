"""Changelog configuration models."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent

from jinja2 import TemplateSyntaxError
from pydantic import BaseModel, Field, field_serializer, field_validator

from ...templates.engine import get_template_engine
from ...templates.types import FunctionDict, TemplateVariables
from ..constants import DEFAULT_CHANGELOG
from ._commit_group import CommitGroupConfig, CommitGroups


@dataclass
class ChangelogTemplateVars:
    """Template variables for changelog rendering.

    This dataclass defines the exact structure of variables that can be passed
    to changelog templates, providing type safety and clear documentation of available
    template variables.

    Attributes:
        version (str): The semantic version being released (e.g., "1.2.3").
        date (str): Formatted date string for the release date.
        messages (list[str]): List of raw commit messages since last version.
        commit_groups (CommitGroups | None): Pre-processed commit groups (optional).
    """

    version: str
    date: str
    messages: list[str]
    commit_groups: CommitGroups | None = None


class ChangelogConfig(BaseModel):
    def model_post_init(self, __context: dict[str, object] | None) -> None:
        """
        Post-initialization hook to register changelog-specific template functions.

        This ensures that the template functions are available whenever an instance
        of this class is created, without requiring manual registration.
        """
        self._register_changelog_template_functions()

    def _register_changelog_template_functions(self) -> None:
        """
        Register changelog-specific template functions with the global template engine.

        Adds domain-specific functions useful for changelog templates:
        - format_date_changelog: Format date strings for changelog
        - group_commits: Group commit messages for grouped changelogs
        - title_case: Convert text to title case.
        """
        engine = get_template_engine()

        # TODO: try to simplify these functions and remove complex return types
        # as they complicate serialization and validation
        changelog_functions: FunctionDict = {
            "format_date_changelog": lambda date_str, fmt="%d-%m-%Y": (
                datetime.strptime(date_str, "%Y-%m-%d").strftime(fmt)
                if isinstance(date_str, str)
                else date_str
            ),
            "group_commits": lambda messages, commit_groups: (
                CommitGroupConfig.group_messages(messages, commit_groups)
                if messages and commit_groups
                else []
            ),
            "get_group_titles": lambda messages, commit_groups: [
                group.title for group in CommitGroupConfig.group_messages(messages, commit_groups)
            ]
            if messages and commit_groups
            else [],
            "get_commits_by_group": lambda messages, commit_groups, group_title: [
                commit.title
                for group in CommitGroupConfig.group_messages(messages, commit_groups)
                if group.title == group_title
                for commit in group.commits
            ]
            if messages and commit_groups
            else [],
            "title_case": lambda text: text.title() if isinstance(text, str) else text,
        }

        # Register all functions as both global functions and filters
        engine.register_functions(changelog_functions)
        engine.register_filters(changelog_functions)

    """
    Defines how the changelog should be generated and formatted.

    Includes file path, overwrite behavior, and Jinja2 templates for
    formatting the changelog entries. The templates support variables such
    as `version`, `date`, and `messages`.

    Attributes:
        file (Path): The relative path to the changelog file to update.
        truncate (bool): If True, overwrites the changelog file instead of prepending.
        template (str): A Jinja2 template for formatting the changelog entry.
        header (str | None): Optional header text placed above the changelog entry.
        footer (str | None): Optional footer text placed below the changelog entry.

    """

    file: Path = Field(
        default_factory=lambda: Path(DEFAULT_CHANGELOG), description="Path to the changelog file."
    )

    truncate: bool = Field(
        default=False, description="If true, overwrite the changelog instead of prepending."
    )

    template: str = Field(
        default=dedent(
            """
        ## [{{version}}] - {{date}}
        {% for msg in messages -%}
        - {{ msg }}
        {%- endfor %}
        """
        ),
        description="Jinja template for changelog entries.",
    )

    header: str | None = Field(default=None, description="Optional header text for the changelog.")
    footer: str | None = Field(default=None, description="Optional footer text for the changelog.")

    @field_serializer("file")
    def serialize_path(self, value: Path) -> str:
        """Serialize Path objects to strings."""
        return str(value)

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str) -> str:
        """
        Validate that the provided string is a valid Jinja2 template.

        Args:
            value (str): The template string to validate.

        Returns:
            str: The original value if it's a valid Jinja2 template.

        Raises:
            ValueError: If the template contains syntax errors.

        """
        try:
            # Use the template engine for validation to include all registered functions
            engine = get_template_engine()
            engine.validate_template(value)
            return value
        except TemplateSyntaxError as err:
            raise ValueError(f"Invalid Jinja2 template: {err}") from err

    def render_template(self, variables: ChangelogTemplateVars) -> str:
        """
        Render the changelog template with proper typing.

        Args:
            variables: Template variables containing version, date, messages, and optionally commit_groups.

        Returns:
            Rendered template string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            Exception: If rendering fails
        """
        # Convert to TemplateVariables for engine compatibility
        template_vars: TemplateVariables = {
            "version": variables.version,
            "date": variables.date,
            "messages": variables.messages,
        }

        # Add commit_groups if provided by the user
        if variables.commit_groups is not None:
            template_vars["commit_groups"] = variables.commit_groups

        engine = get_template_engine()
        return engine.render_template(self.template, template_vars)
