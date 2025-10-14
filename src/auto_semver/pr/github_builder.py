"""
GitHub-specific PRBuilder implementation.

Handles GitHub pull request generation with specific templates and configuration.
"""

from dataclasses import dataclass

from auto_semver.config._models._commit_group import CommitGroup

from .builder import BasePRTemplateVariables, PRBuilder


@dataclass
class GitHubPRTemplateVariables(BasePRTemplateVariables):
    """GitHub-specific template variables for PR builder."""

    groups: list[CommitGroup] | None = None


class GitHubPRBuilder(PRBuilder[GitHubPRTemplateVariables]):
    """GitHub-specific implementation of PRBuilder."""

    def __init__(self) -> None:
        """Initialize GitHub PR builder."""
        super().__init__()
        # Default templates
        self.title_template = "Release {{ version }}"
        self.body_template = "Release notes for {{ version }}"
        self.labels_template = ""

    def build_title(self, data: GitHubPRTemplateVariables) -> str:
        """Build the PR title using the title template."""
        self._register_template_variables(data)
        result: str = self._engine.render_template(self.title_template, data.__dict__)
        return result

    def build_body(self, data: GitHubPRTemplateVariables) -> str:
        """Build the PR body using the body template."""
        self._register_template_variables(data)
        result: str = self._engine.render_template(self.body_template, data.__dict__)
        return result

    def build_labels(self, data: GitHubPRTemplateVariables) -> list[str]:
        """Build the PR labels using the labels template."""
        if not self.labels_template:
            return []
        self._register_template_variables(data)
        labels_str: str = self._engine.render_template(self.labels_template, data.__dict__)
        return [label.strip() for label in labels_str.split(",") if label.strip()]

    def render_pr(self, data: GitHubPRTemplateVariables) -> str:
        """Render the full PR as a single string using the engine and a full template."""
        self._register_template_variables(data)
        # You can set self.full_pr_template in __init__ or load from config
        # Example template: title, body, labels all in one string
        template = getattr(self, "full_pr_template", None)
        if not template:
            # Fallback: combine title and body
            template = "{{ title }}\n\n{{ body }}"
            # Register title/body for template rendering
            self._engine.register_variable("title", self.build_title(data))
            self._engine.register_variable("body", self.build_body(data))
        return self._engine.render_template(template, data.__dict__)
