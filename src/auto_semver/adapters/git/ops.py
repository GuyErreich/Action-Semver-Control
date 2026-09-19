# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""GitOps facade composing local, verified, promote, and release-PR parts."""

from __future__ import annotations

from .local import GitLocal
from .promote import GitPromote
from .release_pr import GitReleasePr
from .verified import GitVerifiedCommits


class GitOps(GitLocal, GitVerifiedCommits, GitPromote, GitReleasePr):
    """Unified Git / GitHub operations for auto-semver pipelines."""

    pass
