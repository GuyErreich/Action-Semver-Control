"""Commit group configuration models."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Constants
CONVENTIONAL_COMMIT_PARTS = 2

type RegexPattern = str


@dataclass
class Commit:
    r"""
    Parsed commit message data structure for template rendering.

    This dataclass represents a parsed commit message with extracted components
    that can be used in Jinja2 templates for changelog and PR generation.

    Attributes:
        title (str): The cleaned, display-friendly commit title/summary line.
                    For conventional commits, this extracts just the description part.
                    Used for concise commit listings in changelogs and PRs.
                    Example: "add OAuth2 support" (from "feat(auth): add OAuth2 support")

        body (str | None): The extended commit message body, if present.
                          Contains everything after the first line, preserving internal structure.
                          None if the commit only has a title line.
                          Used for detailed commit information in templates.
                          Example: "Implements OAuth2 authentication flow\n\nBREAKING CHANGE: ..."
    """

    title: str
    body: str | None = None


@dataclass
class CommitGroup:
    """
    Runtime data structure representing a single commit group with its commits.

    This dataclass represents a categorized group of commits that have been matched
    against specific patterns. Used as template data for Jinja2 rendering in
    changelogs and pull requests.

    Attributes:
        title (str): The display title for this group of commits.
            This appears as the section header in generated changelogs and PRs.
            Examples: "🚀 Features", "🐛 Bug Fixes", "📝 Documentation"

        commits (list[Commit]): List of parsed commit objects belonging to this group.
            Each commit contains title and optional body text.
            Sorted in the order they were processed from git history.

        priority (int): Numeric priority for sorting groups in output.
            Lower numbers appear first in generated content.
            Used to ensure consistent ordering (e.g., Features before Bug Fixes).

    Note:
        This is typically created by CommitGroupConfig.group_messages() and consumed
        by Jinja2 templates. Templates can iterate over commits and access their
        title/body for formatting.

    Example:
        Template usage:
        ```jinja2
        {% for group in commit_groups %}
        ## {{ group.title }}
        {% for commit in group.commits %}
        - {{ commit.title }}
        {% endfor %}
        {% endfor %}
        ```
    """

    title: str
    commits: list[Commit]
    priority: int


type CommitGroups = list[CommitGroup]
"""
Collection of commit groups for template rendering.

This type alias represents the complete data structure returned by commit grouping
operations and consumed by changelog/PR templates. It contains all categorized
commits organized by their matching patterns.

Note:
    This is the primary data structure passed to Jinja2 templates for rendering
    changelogs and pull request descriptions. Templates iterate over this list
    to generate formatted output with proper grouping and ordering.

Example:
    ```python
    commit_groups = CommitGroupConfig.group_messages(messages, config_groups)
    # Returns:
    [
        {"title": "🚀 Features", "commits": [...], "priority": 1},
        {"title": "🐛 Bug Fixes", "commits": [...], "priority": 2}
    ]
    ```

    Template usage:
    ```jinja2
    {% for group in commit_groups %}
    ## {{ group.title }}
    {% for commit in group.commits %}
    - {{ commit.title }}
    {% endfor %}
    {% endfor %}
    ```

Note:
    Processing details:
    - Groups are sorted by priority (lower numbers first)
    - Empty groups (no matching commits) are filtered out
    - Unmatched commits are placed in a catch-all or "Other Changes" group
    - Each group maintains the original git history order of its commits
"""


class CommitGroupConfig(BaseModel):
    """
    Defines a group for categorizing commit messages by regex patterns.

    Attributes:
        title (str): Display title for this group of commits.
        patterns (list[str]): List of regex patterns to match commit messages.
        priority (int): Sort priority (lower numbers appear first).
    """

    title: str = Field(..., description="Display title for this commit group")
    patterns: list[RegexPattern] = Field(..., description="List of regex patterns to match commits")
    priority: int = Field(..., description="Sort priority (lower numbers first)")

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, patterns: list[RegexPattern]) -> list[RegexPattern]:
        """Validate that all patterns are valid regex."""
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as err:
                raise ValueError(f"Invalid regex pattern '{pattern}': {err}") from err
        return patterns

    @staticmethod
    def group_messages(messages: list[str], commit_groups: list[CommitGroupConfig]) -> CommitGroups:
        """
        Group commit messages by patterns and return data ready for Jinja templates.

        Takes a list of raw commit messages and groups them according to the
        configured patterns, returning structured data for template rendering.
        
        For commits with multi-line bodies containing bullet points, extracts
        each bullet point as a separate commit item to categorize individually.

        Args:
            messages: List of raw commit messages from git.
            commit_groups: List of commit group configurations with patterns.

        Returns:
            CommitGroups containing grouped_messages with parsed commits organized by group.
        """
        if not messages:
            return []

        if not commit_groups:
            # No groups configured - return all messages in one default group
            commits = [CommitGroupConfig._parse_commit(msg) for msg in messages]
            default_group = CommitGroup(title="📝 Changes", commits=commits, priority=1)
            return [default_group]

        # Sort groups by priority (lower numbers first)
        sorted_groups = sorted(commit_groups, key=lambda g: g.priority)

        # Extract individual items from commit messages (including body bullet points)
        individual_items = CommitGroupConfig._extract_individual_items(messages)

        # Group individual items
        groups: dict[str, CommitGroup] = {}
        unmatched: list[str] = []

        for item in individual_items:
            matched = False
            for group in sorted_groups:
                if CommitGroupConfig._message_matches(item, group.patterns):
                    if group.title not in groups:
                        groups[group.title] = CommitGroup(
                            title=group.title,
                            commits=[],
                            priority=group.priority,
                        )
                    groups[group.title].commits.append(CommitGroupConfig._parse_commit(item))
                    matched = True
                    break

            if not matched:
                unmatched.append(item)

        # Handle unmatched messages
        if unmatched:
            CommitGroupConfig._handle_unmatched_messages(unmatched, sorted_groups, groups)

        # Return groups with commits, sorted by priority
        result: CommitGroups = []
        for commit_group in groups.values():
            if commit_group.commits:  # Only include groups that have commits
                result.append(commit_group)

        # Sort by priority (lower numbers first)
        return sorted(result, key=lambda g: g.priority)

    @staticmethod
    def _extract_individual_items(messages: list[str]) -> list[str]:
        """
        Extract individual items from commit messages.
        
        For commits with bullet points in the body, extract each bullet as a separate item.
        Returns a list of individual commit lines/items to be categorized.
        """
        items = []
        for message in messages:
            lines = message.strip().split("\n")
            
            # Check if there are bullet points in the body
            has_bullets = any(line.strip().startswith(("-", "*", "•")) for line in lines[1:])
            
            if has_bullets:
                # Extract each bullet point as a separate item
                for line in lines[1:]:
                    stripped_line = line.strip()
                    if stripped_line.startswith(("-", "*", "•")):
                        # Remove bullet marker and clean up
                        clean_line = stripped_line.lstrip("-*•").strip()
                        if clean_line:
                            items.append(clean_line)
            else:
                # No bullets, use the full commit message
                items.append(message)
        
        return items

    @staticmethod
    def _message_matches(message: str, patterns: list[str]) -> bool:
        """Check if message matches any of the regex patterns (case insensitive)."""
        for pattern in patterns:
            try:
                if re.match(pattern, message, re.IGNORECASE):
                    return True
            except re.error as err:
                logger.warning(f"Invalid regex pattern '{pattern}': {err}")
        return False

    @staticmethod
    def _parse_commit(message: str) -> Commit:
        """
        Parse commit message into title and body.

        For conventional commits like "feat: add thing", extracts "add thing" as title.
        """
        lines = message.strip().split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 and lines[1].strip() else None

        # Clean up conventional commit titles
        if ":" in title:
            parts = title.split(":", 1)
            if len(parts) == CONVENTIONAL_COMMIT_PARTS:
                clean_title = parts[1].strip()
                if clean_title:
                    title = clean_title

        return Commit(title=title, body=body)

    @staticmethod
    def _handle_unmatched_messages(
        unmatched: list[str], sorted_groups: list[CommitGroupConfig], groups: dict[str, CommitGroup]
    ) -> None:
        """Handle messages that didn't match any group patterns."""
        # Check for catch-all group (has ".*" pattern)
        catch_all = next((g for g in sorted_groups if ".*" in g.patterns), None)
        if catch_all:
            if catch_all.title not in groups:
                groups[catch_all.title] = CommitGroup(
                    title=catch_all.title,
                    commits=[],
                    priority=catch_all.priority,
                )
            for msg in unmatched:
                groups[catch_all.title].commits.append(CommitGroupConfig._parse_commit(msg))
        else:
            # Create default "Other Changes" group
            groups["Other Changes"] = CommitGroup(
                title="Other Changes",
                commits=[CommitGroupConfig._parse_commit(msg) for msg in unmatched],
                priority=999,
            )
