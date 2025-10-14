"""
Shared template utility functions for consistent date formatting and text processing.

This module provides common template functions that can be reused across different
managers and builders to ensure consistency and reduce code duplication.
"""

from datetime import datetime
from typing import Any


def format_date_iso_to_custom(date_str: str, fmt: str = "%Y-%m-%d") -> str:
    """Format date string from ISO format (YYYY-MM-DD) to custom format.

    Args:
        date_str: Date string in YYYY-MM-DD format.
        fmt: Target format string (default: "%Y-%m-%d").

    Returns:
        Formatted date string, or original string if parsing fails.

    Examples:
        >>> format_date_iso_to_custom("2024-12-25", "%B %d, %Y")
        'December 25, 2024'
        >>> format_date_iso_to_custom("2024-12-25", "%d-%m-%Y")
        '25-12-2024'
        >>> format_date_iso_to_custom("invalid-date")
        'invalid-date'
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime(fmt)
    except (ValueError, TypeError):
        return str(date_str)  # Return as string if parsing fails


def truncate_text(text: str, length: int = 72, suffix: str = "...") -> str:
    """Truncate text to specified length with optional suffix.

    Args:
        text: Text to truncate.
        length: Maximum length including suffix (default: 72).
        suffix: Suffix to append when truncating (default: "...").

    Returns:
        Truncated text with suffix if longer than length, otherwise original text.

    Examples:
        >>> truncate_text("This is a very long message", 20)
        'This is a very lo...'
        >>> truncate_text("Short", 20)
        'Short'
        >>> truncate_text("Custom truncate", 10, ">>")
        'Custom tr>>'
    """
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix


def capitalize_first_letter(text: str) -> str:
    """Capitalize first letter of text while preserving the rest.

    Args:
        text: Text to capitalize.

    Returns:
        Text with first letter capitalized, empty string unchanged.

    Examples:
        >>> capitalize_first_letter("hello world")
        'Hello world'
        >>> capitalize_first_letter("HTML parser")
        'HTML parser'
        >>> capitalize_first_letter("")
        ''
    """
    return text[0].upper() + text[1:] if text else text


def extract_prefix_before_delimiter(text: str, delimiter: str = ":") -> str:
    """Extract text before first occurrence of delimiter.

    Args:
        text: Text to extract from.
        delimiter: Delimiter to split on (default: ":").

    Returns:
        Text before delimiter, or "other" if delimiter not found.

    Examples:
        >>> extract_prefix_before_delimiter("feat: add feature")
        'feat'
        >>> extract_prefix_before_delimiter("fix(api): resolve bug")
        'fix(api)'
        >>> extract_prefix_before_delimiter("no delimiter here")
        'other'
    """
    return text.split(delimiter)[0].strip() if delimiter in text else "other"


def count_items_in_groups(groups: list[dict[str, Any]] | None, items_key: str = "commits") -> int:
    """Count total items across all groups.

    Args:
        groups: List of groups, each containing an items_key.
        items_key: Key name for items list in each group (default: "commits").

    Returns:
        Total number of items across all groups.

    Examples:
        >>> groups = [{"commits": ["a", "b"]}, {"commits": ["c"]}]
        >>> count_items_in_groups(groups)
        3
        >>> count_items_in_groups(None)
        0
    """
    if not groups:
        return 0

    total = 0
    for group in groups:
        items = group.get(items_key, [])
        if isinstance(items, list):
            total += len(items)
    return total


def has_keyword_in_group_titles(
    groups: list[dict[str, Any]] | None, keywords: list[str], title_key: str = "title"
) -> bool:
    """Check if any group title contains specified keywords.

    Args:
        groups: List of groups to check.
        keywords: List of keywords to search for (case-insensitive).
        title_key: Key name for title in each group (default: "title").

    Returns:
        True if any group title contains any of the keywords.

    Examples:
        >>> groups = [{"title": "Breaking Changes"}, {"title": "Features"}]
        >>> has_keyword_in_group_titles(groups, ["breaking", "🔥"])
        True
        >>> has_keyword_in_group_titles(groups, ["docs"])
        False
    """
    if not groups:
        return False

    keywords_lower = [keyword.lower() for keyword in keywords]
    return any(
        any(keyword in str(group.get(title_key, "")).lower() for keyword in keywords_lower)
        for group in groups
    )
