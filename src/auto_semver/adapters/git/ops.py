# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""GitOps facade composing local, verified, promote, and release-PR mixins."""

from __future__ import annotations

from .local import GitLocalMixin
from .promote import GitPromoteMixin
from .release_pr import GitReleasePrMixin
from .verified import GitVerifiedCommitMixin


class GitOps(GitLocalMixin, GitVerifiedCommitMixin, GitPromoteMixin, GitReleasePrMixin):
    """Unified Git / GitHub operations for auto-semver pipelines."""

    pass
