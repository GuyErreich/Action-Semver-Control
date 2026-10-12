#!/usr/bin/env python3
# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Match pull request paths against newline-separated glob patterns."""

from __future__ import annotations

import os
import re
import sys


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a glob. ``*`` stays in one path segment. ``**`` crosses directories."""
    parts: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
            continue
        if pattern.startswith("**", index):
            parts.append(".*")
            index += 2
            continue
        char = pattern[index]
        if char == "*":
            parts.append("[^/]*")
        elif char == "?":
            parts.append("[^/]")
        else:
            parts.append(re.escape(char))
        index += 1
    return re.compile("".join(parts) + r"\Z")


def path_matches(path: str, pattern: str) -> bool:
    """Return whether ``path`` matches one glob pattern.

    A pattern with no slash matches the file name in any directory, so ``*.py``
    matches ``src/app.py``. A pattern with a slash matches the full path.
    """
    normalized = path.replace("\\", "/").lstrip("/")
    cleaned = pattern.strip().replace("\\", "/").lstrip("/")
    if not cleaned or cleaned.startswith("#"):
        return False
    regex = _glob_to_regex(cleaned)
    if regex.fullmatch(normalized):
        return True
    if "/" not in cleaned:
        return regex.fullmatch(normalized.rsplit("/", 1)[-1]) is not None
    return False


def any_match(paths: list[str], patterns: str) -> bool:
    """Return whether any path matches any pattern line."""
    pattern_lines = [
        line.strip()
        for line in patterns.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for path in paths:
        cleaned_path = path.strip()
        if not cleaned_path:
            continue
        for pattern in pattern_lines:
            if path_matches(cleaned_path, pattern):
                return True
    return False


def main() -> int:
    """Read paths on stdin and write ``matched`` for ``GITHUB_OUTPUT``."""
    patterns = os.environ.get("PATTERNS", "")
    paths = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    matched = "true" if any_match(paths, patterns) else "false"
    print(f"matched={matched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
