"""
Commit message grouping logic.

This module provides the core logic for categorizing commit messages into groups
based on configuration. It is responsible for parsing commits, matching them
against patterns/sections, and organizing them into structure ready for templates.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from ..config._models._commit_group import Commit, CommitGroup
from .parser import CommitParser

if TYPE_CHECKING:
    from ..config._models._commit_group import CommitGroupConfig, CommitGroups

logger = logging.getLogger(__name__)

# Constants
CONVENTIONAL_COMMIT_PARTS = 2


class CommitGrouper:
    """Logic for grouping commit messages based on configuration."""

    @staticmethod
    def group_messages(messages: list[str], commit_groups: list[CommitGroupConfig]) -> CommitGroups:
        """
        Group commit messages by patterns and return data ready for Jinja templates.

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
            commits = [CommitGrouper._parse_commit(msg) for msg in messages]
            default_group = CommitGroup(title="📝 Changes", commits=commits, priority=1)
            return [default_group]

        # Sort groups by priority (lower numbers first)
        sorted_groups = sorted(commit_groups, key=lambda g: g.priority)

        # Parse all messages using the robust parser
        parser = CommitParser()

        # Prepare groups structure
        groups: dict[str, CommitGroup] = {
            g.title: CommitGroup(title=g.title, commits=[], priority=g.priority)
            for g in sorted_groups
        }

        unmatched_commits: list[Commit] = []

        for message in messages:
            CommitGrouper._process_message(
                parser, message, sorted_groups, groups, unmatched_commits
            )

        # Handle unmatched messages
        if unmatched_commits:
            CommitGrouper._handle_unmatched(unmatched_commits, sorted_groups, groups)

        # Return groups with commits, sorted by priority
        result: CommitGroups = []
        for group in groups.values():
            if group.commits:
                result.append(group)

        return sorted(result, key=lambda g: g.priority)

    @staticmethod
    def _resolve_group(
        text: str, section: str | None, groups: list[CommitGroupConfig]
    ) -> CommitGroupConfig | None:
        """Find matching group for text/section."""
        if section:
            for group in groups:
                if section in group.match_groups:
                    return group

        for group in groups:
            if CommitGrouper._message_matches(text, group.patterns):
                return group
        return None

    @staticmethod
    def _process_message(
        parser: CommitParser,
        message: str,
        sorted_groups: list[CommitGroupConfig],
        groups: dict[str, CommitGroup],
        unmatched_commits: list[Commit],
    ) -> None:
        """Process a single commit message and sort into groups."""
        parsed = parser.parse(message)

        # 1. Handle grouped sections (Type 3)
        if parsed.sectioned_changes:
            CommitGrouper._process_sections(
                parsed.sectioned_changes, sorted_groups, groups, unmatched_commits
            )

        # 2. Handle flat bullet points (Type 2)
        if parsed.bullet_points:
            CommitGrouper._process_bullets(
                parsed.bullet_points, sorted_groups, groups, unmatched_commits
            )

        # 3. Handle Header only if NO details found at all (Type 1)
        if not parsed.sectioned_changes and not parsed.bullet_points:
            CommitGrouper._process_header(
                parsed.header, parsed.body, sorted_groups, groups, unmatched_commits
            )

    @staticmethod
    def _process_sections(
        sections: dict[str, list[str]],
        sorted_groups: list[CommitGroupConfig],
        groups: dict[str, CommitGroup],
        unmatched_commits: list[Commit],
    ) -> None:
        """Process Type 3 commits (grouped sections)."""
        for section, items in sections.items():
            # Attempt to find a group that matches this section header
            # We pass empty text because if section matches, we use that group for ALL items.
            group = CommitGrouper._resolve_group("", section, sorted_groups)

            if group:
                # If section matches a group, all items go there
                for item_text in items:
                    groups[group.title].commits.append(Commit(title=item_text))
            else:
                # If section doesn't match a group, try to match items individually
                # or fall back to unmatched
                for item_text in items:
                    item_group = CommitGrouper._resolve_group(item_text, None, sorted_groups)
                    commit = Commit(title=item_text)
                    if item_group:
                        groups[item_group.title].commits.append(commit)
                    else:
                        unmatched_commits.append(commit)

    @staticmethod
    def _process_bullets(
        bullets: list[str],
        sorted_groups: list[CommitGroupConfig],
        groups: dict[str, CommitGroup],
        unmatched_commits: list[Commit],
    ) -> None:
        """Process Type 2 commits (flat bullet points)."""
        for item_text in bullets:
            group = CommitGrouper._resolve_group(item_text, None, sorted_groups)
            commit = Commit(title=item_text)

            if group:
                groups[group.title].commits.append(commit)
            else:
                unmatched_commits.append(commit)

    @staticmethod
    def _process_header(
        header: str,
        body: str | None,
        sorted_groups: list[CommitGroupConfig],
        groups: dict[str, CommitGroup],
        unmatched_commits: list[Commit],
    ) -> None:
        """Process Type 1 commits (header only)."""
        group = CommitGrouper._resolve_group(header, None, sorted_groups)
        title = CommitGrouper._clean_conv_title(header)
        commit = Commit(title=title, body=body)

        if group:
            groups[group.title].commits.append(commit)
        else:
            unmatched_commits.append(commit)

    @staticmethod
    def _clean_conv_title(title: str) -> str:
        """Clean conventional commit title."""
        if ":" in title:
            parts = title.split(":", 1)
            if len(parts) == CONVENTIONAL_COMMIT_PARTS:
                clean_title = parts[1].strip()
                if clean_title:
                    return clean_title
        return title

    @staticmethod
    def _handle_unmatched(
        commits: list[Commit],
        config_groups: list[CommitGroupConfig],
        groups: dict[str, CommitGroup],
    ) -> None:
        """Handle unmatched commits by adding to catch-all or default group."""
        catch_all_config = next((g for g in config_groups if ".*" in g.patterns), None)

        if catch_all_config:
            groups[catch_all_config.title].commits.extend(commits)
        else:
            other_title = "Other Changes"
            if other_title not in groups:
                groups[other_title] = CommitGroup(title=other_title, commits=[], priority=999)
            groups[other_title].commits.extend(commits)

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
