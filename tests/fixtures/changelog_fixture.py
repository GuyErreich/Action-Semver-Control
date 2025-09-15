"""
Changelog fixtures for testing.

This module provides a fixture class for creating changelog files for tests
backed by a fake filesystem.
"""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem


class ChangelogFixture:
    """
    A fixture class that creates and manages a changelog file in a fake FS.

    Provides helpers to quickly create common changelog layouts for tests
    without touching the real filesystem.
    """

    def __init__(self, tmp_path: Path, fs: FakeFilesystem) -> None:
        """Initialize the fixture with a temporary directory and fake FS.

        Args:
            tmp_path: Temporary directory path provided by pytest
            fs: pyfakefs FakeFilesystem instance
        """
        self.tmp_path = tmp_path
        self.fs = fs

        # Ensure tmp_path exists in the fake filesystem
        if not self.fs.exists(self.tmp_path):
            self.fs.create_dir(self.tmp_path)

    @property
    def path(self) -> Path:
        """Return the path to the changelog file in the temp directory."""
        return self.tmp_path / "CHANGELOG.md"

    def write(self, content: str) -> Path:
        """Write arbitrary content to the changelog file in the fake FS."""
        if self.fs.exists(self.path):
            # Remove if exists to avoid appending
            self.fs.remove_object(str(self.path))
        self.fs.create_file(self.path, contents=content)
        return self.path

    def create(self) -> Path:
        """Create an empty changelog file in the fake filesystem."""
        return self.write("")
