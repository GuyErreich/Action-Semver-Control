"""Tests for semver lock release-branch metadata."""

import pytest

from auto_semver.semver import Version
from auto_semver.semver.lock import SemverLock


@pytest.mark.unit
def test_release_lock_markers() -> None:
    """Release branch locks include branch_role release; baseline strips it."""
    lock = SemverLock(
        version=Version.parse("1.4.0-dev"),
        source_branch="feature/foo",
        target_branch="dev",
    )
    lock.as_release_branch_lock(managed_by_version="1.3.14")

    assert lock.is_release_branch_lock()
    assert lock.branch_role == "release"
    assert lock.managed_by == "auto-semver"

    lock.as_finalized_baseline(merge_sha="abc123")
    assert lock.finalized is True
    assert lock.branch_role is None
    assert lock.target_base_sha == "abc123"
