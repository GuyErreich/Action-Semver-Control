"""Pull request configuration models."""

from dataclasses import dataclass
from datetime import datetime

from jinja2 import TemplateSyntaxError
from pydantic import BaseModel, Field, field_validator

from ...templates.engine import get_template_engine
from ...templates.types import FunctionDict, TemplateVariables
from ..constants import PR_HIDDEN_MARKER
from ._commit_group import CommitGroups

# Constants
MIN_LABELS_COUNT = 1
DEFAULT_LABELS = ["semver-bump"]
DEFAULT_TITLE_TEMPLATE = "Release {{version}}"
DEFAULT_BODY_TEMPLATE = "Auto-created PR by auto-semver."


# Type aliases for model fields only
type JinjaTemplate = str
type GitHubLabel = str


@dataclass
class PullRequestTemplateVars:
    """Template variables for pull request title and body rendering.

    This dataclass defines the exact structure of variables that can be passed
    to PR templates, providing type safety and clear documentation of available
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


class PullRequestConfig(BaseModel):
    """
    Defines settings for the pull request created during version bumps.

    The configuration includes label names, and Jinja2 templates for the PR title
    and body. Templates are validated at load time to ensure they are syntactically valid.

    Attributes:
        labels (list[str]): A list of GitHub labels to apply to the generated PR.
        title (str): A Jinja2 template string used to generate the PR title.
        body (str): A Jinja2 template string used to generate the PR body content.

    Template Variables:
        The following variables are available in both title and body templates:
        - version (str): The semantic version being released (e.g., "1.2.3")
        - date (str): Formatted date string for the release
        - messages (list[str]): List of raw commit messages since last version
        - commit_groups (CommitGroups): Pre-processed commit groups (optional)

    Template Functions:
        The following functions are available for use in templates:
        - truncate_commit(msg, length=72): Truncate commit messages to specified length
        - format_date_custom(date_str, fmt="%Y-%m-%d"): Format date strings with custom format
        - conventional_type(msg): Extract conventional commit type from message
        - capitalize_first(text): Capitalize first letter of text
        - count_commits(groups): Count total commits across groups
        - has_breaking(groups): Check if there are breaking changes in groups
        - count_groups(groups): Count number of commit groups
    """

    labels: list[GitHubLabel] = Field(
        default=DEFAULT_LABELS,
        min_length=MIN_LABELS_COUNT,
        description="List of labels to apply to the pull request.",
    )
    title: JinjaTemplate = Field(
        default=DEFAULT_TITLE_TEMPLATE,
        description="Title template for the pull request.",
    )
    body: JinjaTemplate = Field(
        default=DEFAULT_BODY_TEMPLATE,
        description="Body template for the pull request.",
    )

    def model_post_init(self, __context: dict[str, object] | None) -> None:
        """
        Post-initialization hook to register PR-specific template functions.

        This ensures that the template functions are available whenever an instance
        of this class is created, without requiring manual registration.
        """
        self._register_pr_template_functions()

    def _register_pr_template_functions(self) -> None:
        """
        Register PR-specific template functions with the global template engine.

        This method adds domain-specific functions that are useful for PR templates:
        - truncate_commit: Truncate commit messages to a specific length
        - format_date: Format date strings with custom formats
        - conventional_type: Extract conventional commit type
        - capitalize_first: Capitalize first letter of text
        - count_commits: Count total commits across groups
        - has_breaking: Check if there are breaking changes
        - count_groups: Count number of commit groups
        """
        engine = get_template_engine()

        # Register PR-specific filters and functions
        pr_functions: FunctionDict = {
            "truncate_commit": lambda msg, length=72: (
                msg[: length - 3] + "..." if len(msg) > length else msg
            ),
            "format_date_custom": lambda date_str, fmt="%Y-%m-%d": (
                datetime.strptime(date_str, "%Y-%m-%d").strftime(fmt)
                if isinstance(date_str, str)
                else date_str
            ),
            "conventional_type": lambda msg: (msg.split(":")[0].strip() if ":" in msg else "other"),
            "capitalize_first": lambda text: (text[0].upper() + text[1:] if text else text),
            "count_commits": lambda groups: (
                sum(len(g["commits"]) for g in groups) if groups else 0
            ),
            "has_breaking": lambda groups: (
                any("breaking" in g["title"].lower() or "🔥" in g["title"] for g in groups)
                if groups
                else False
            ),
            "count_groups": lambda groups: len(groups) if groups else 0,
            # Note: removed get_commit_types and group_commits as they return complex types
            # These can be handled at the application level if needed
        }

        # Register as functions (for explicit function calls like count_commits(groups))
        # Note: Function syntax is more explicit and readable than filter syntax
        engine.register_functions(pr_functions)

        # Also register as filters for use with | syntax
        engine.register_filters(pr_functions)

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
            # Use the template engine for validation to include all registered functions
            engine = get_template_engine()
            engine.validate_template(value)
            return value
        except TemplateSyntaxError as err:
            raise ValueError(f"Invalid Jinja2 template: {err}") from err

    def render_title(
        self,
        variables: PullRequestTemplateVars,
    ) -> str:
        """
        Render the title template using PullRequestTemplateVars only.

        Args:
            variables: PullRequestTemplateVars dataclass containing version, date, and messages.

        Returns:
            str: Rendered title string.
        """
        template_vars: TemplateVariables = {
            "version": variables.version,
            "date": variables.date,
            "messages": variables.messages,
        }
        engine = get_template_engine()
        return engine.render_template(self.title, template_vars)

    def render_body(
        self,
        variables: PullRequestTemplateVars,
    ) -> str:
        """
        Render the body template using PullRequestTemplateVars only and append hidden marker.

        Args:
            variables: PullRequestTemplateVars dataclass containing version,
                date, messages, and optionally commit_groups.

        Returns:
            str: Rendered body with hidden marker appended.
        """
        template_vars: TemplateVariables = {
            "version": variables.version,
            "date": variables.date,
            "messages": variables.messages,
        }
        if variables.commit_groups is not None:
            template_vars["commit_groups"] = variables.commit_groups
        engine = get_template_engine()
        rendered = engine.render_template(self.body, template_vars)
        return f"{PR_HIDDEN_MARKER}\n{rendered}"

    def get_release_commit_prefix(self) -> str | None:
        """
        Extract the prefix from the title template that can be used to identify release commits.

        This method uses the template engine to properly parse the Jinja2 template and find
        static text before template variables, which can be used to filter out release commits
        from commit messages.

        Returns:
            str | None: The prefix string if found, None if the template starts with a variable.

        Examples:
            - "Release {{version}}" -> "Release"
            - "{{version}}" -> None
            - "Bump to {{version}} for {{branch}}" -> "Bump to"
        """
        engine = get_template_engine()

        try:
            # Use the template engine's AST-based static prefix extraction
            return engine.get_static_prefix(self.title)
        except Exception:
            # If template parsing fails, fall back to treating it as plain text
            return self.title.strip() if self.title.strip() else None
