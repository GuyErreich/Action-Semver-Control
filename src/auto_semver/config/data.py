"""
Configuration schema definitions for auto-semver.

This module defines the data structures used to load and validate the
`auto_semver_config.yml` configuration file. It provides Pydantic-based models
for describing the pull request formatting, changelog behavior, and versioning strategy
used throughout the bump and finalize workflows.

Each configuration section (e.g., pull request, changelog) is encapsulated in
its own model with descriptive fields and optional Jinja2 template validation.

Classes:
    PullRequestConfig: Contains labels, title, and body template for generated PRs.
    ChangelogConfig: Controls changelog file generation and formatting.
    ConfigData: Root configuration object holding all top-level config sections.
"""

from textwrap import dedent
from typing import Any

from jinja2 import Template, TemplateSyntaxError
from pydantic import BaseModel, Field, field_validator, model_validator

from ..semver import Version
from .constants import DEFAULT_CHANGELOG


class PullRequestConfig(BaseModel):

    """
    Defines settings for the pull request created during version bumps.

    The configuration includes label names, and Jinja2 templates for the PR title
    and body. Templates are validated at load time to ensure they are syntactically valid.

    Attributes:
        labels (list[str]): A list of GitHub labels to apply to the generated PR.
        title (str): A Jinja2 template string used to generate the PR title.
        body (str): A Jinja2 template string used to generate the PR body content.

    """

    labels: list[str] = Field(
        default=["semver-bump"],
        min_length=1,
        description="List of labels to apply to the pull request.",
    )
    title: str = Field(
        default="Release {{version}}",
        description="Title template for the pull request.",
    )
    body: str = Field(
        default="Auto-created PR by auto-semver.",
        description="Body template for the pull request.",
    )

    @field_validator("title", "body")
    @classmethod
    def validate_jinja_template(cls, value: str) -> str:
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
            Template(value)  # Check if it compiles
        except TemplateSyntaxError as err:
            raise ValueError(f"Invalid Jinja2 template: {err}") from err

        return value

    def render_title(self, **kwargs: Any) -> str:
        """Return the title as a Jinja2 Template."""
        return Template(self.title).render(**kwargs)

    def render_body(self, **kwargs: Any) -> str:
        """Render the body template and silently append a hidden marker comment."""
        rendered = Template(self.body).render(**kwargs)
        return f"<!-- auto-semver:pr -->\n{rendered}"


class ChangelogConfig(BaseModel):

    """
    Defines how the changelog should be generated and formatted.

    Includes file path, overwrite behavior, and Jinja2 templates for
    formatting the changelog entries. The templates support variables such
    as `version`, `date`, and `messages`.

    Attributes:
        file (str): The relative path to the changelog file to update.
        truncate (bool): If True, overwrites the changelog file instead of prepending.
        template (str): A Jinja2 template for formatting the changelog entry.
        header (str | None): Optional header text placed above the changelog entry.
        footer (str | None): Optional footer text placed below the changelog entry.

    """

    file: str = Field(default=DEFAULT_CHANGELOG, description="Path to the changelog file.")
    truncate: bool = Field(
        default=False,
        description="If true, overwrite the changelog instead of prepending."
    )
    template: str = Field(
        default=dedent("""
        ## [{{version}}] - {{date}}
        {% for msg in messages -%}
        - {{ msg }}
        {%- endfor %}
        """),
        description="Jinja template for changelog entries.",
    )
    header: str | None = Field(default="", description="Optional header text for the changelog.")
    footer: str | None = Field(default="", description="Optional footer text for the changelog.")


class PromotionRule(BaseModel):
    from_branch: str
    to_branch: str


class ConfigData(BaseModel):

    """
    Holds all validated configuration values loaded from auto_semver_config.yml.

    This model represents the user-defined configuration for the auto-semver
    process, including versioning behavior, changelog generation, PR metadata, and
    supported branch strategies. It ensures that required fields are present and typed.

    Attributes:
        start_version (Version): The default version to use if no version file is found.
        suffixes (dict[str, str]): Mapping of target branches to version suffixes
            (e.g., {"main": "", "dev": "-dev"}).
        version_files (list[str]): List of files to update with the new version string.
        branch_strategy (str): Strategy for PR generation ("single" or "multi").
        pull_request (PullRequestConfig): Configuration for the pull request title, body, and labels.
        changelog (ChangelogConfig): Changelog file behavior and formatting templates.

    """

    start_version: Version = Field(
        default_factory=lambda: Version.parse("0.1.0"), description="Optional start_version."
    )
    suffixes: dict[str, str] = Field(..., description="Required branch suffix mapping.")
    promotions: list[PromotionRule] = Field(
        ..., description="Allowed branch promotion rules (from → to)."
    )
    version_files: list[str] = Field(
        default=["version.txt"], description="Optional files that hold version format to update."
    )
    branch_strategy: str = "single"
    pull_request: PullRequestConfig
    changelog: ChangelogConfig

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("start_version", mode="before")
    @classmethod
    def validate_version(cls, value: str) -> Version:
        try:
            return Version.parse(value)
        except ValueError:
            raise

    @model_validator(mode="after")
    def validate_promotions_have_suffixes(self) -> "ConfigData":
        # Validate that all promotion targets have suffixes
        missing_suffixes = {
            rule.to_branch for rule in self.promotions if rule.to_branch not in self.suffixes
        }

        if missing_suffixes:
            raise ValueError(
                f"The following promotion targets are missing suffix definitions: {sorted(missing_suffixes)}"
            )

        # Validate no reverse rules exist
        seen_pairs = set()
        for rule in self.promotions:
            reverse = (rule.to_branch, rule.from_branch)
            if reverse in seen_pairs:
                raise ValueError(
                    f"Invalid promotion configuration: reverse rule found for '{rule.from_branch} → {rule.to_branch}'"
                )
            seen_pairs.add((rule.from_branch, rule.to_branch))

        return self
