# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Shared attribute declarations for GitOps mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git import Repo
    from github import Github


class GitOpsMixinBase:
    """Attribute surface every GitOps mixin may read/write on ``self``."""

    repo: Repo
    github_token: str | None
    signed_commits: bool
    _repo_full_name: str
    _github_clients: dict[str, Github]
