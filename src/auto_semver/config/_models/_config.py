"""Main configuration data model."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from ...semver import Version
from ._changelog import ChangelogConfig
from ._commit_group import CommitGroupConfig, CommitGroups
from ._promotion import PromotionRule
from ._pull_request import PullRequestConfig


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
        changelog (_ChangelogConfig): Changelog file behavior and formatting templates.

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
    branch_strategy: Literal["single", "multi"] = Field(
        default="single", description="Strategy for branch management ('single' or 'multi')"
    )
    commit_groups: list[CommitGroupConfig] = Field(
        default_factory=list, description="Optional commit grouping configuration for templates"
    )
    pull_request: PullRequestConfig
    changelog: ChangelogConfig

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("start_version", mode="before")
    @classmethod
    def validate_version(cls, value: str | Version) -> Version:
        """Validate and parse the start_version field."""
        if isinstance(value, Version):
            return value
        try:
            return Version.parse(value)
        except ValueError:
            raise

    @field_serializer("start_version")
    def serialize_version(self, value: Version) -> str:
        """Serialize Version objects to strings."""
        return str(value)

    @model_validator(mode="after")
    def validate_promotions_have_suffixes(self) -> ConfigData:
        """Validate that all branches in promotion rules have suffix definitions."""
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
                    f"Invalid promotion configuration: reverse rule found for "
                    f"'{rule.from_branch} → {rule.to_branch}'"
                )
            seen_pairs.add((rule.from_branch, rule.to_branch))

        return self

    def group_commit_messages(self, messages: list[str]) -> CommitGroups:
        """
        Group commit messages using the configured commit groups.

        Args:
            messages: List of commit messages to group

        Returns:
            CommitGroups: list of CommitGroup dataclasses for template rendering.
        """
        return CommitGroupConfig.group_messages(messages, self.commit_groups)
