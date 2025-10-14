"""Fixture for creating a temporary git repository for tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Generator[tuple[Repo, Path], None, None]:
    """Create a temporary git repository inside tmp_path.
    
    Returns the Repo object and repo path.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    repo = Repo.init(repo_dir)
    yield repo, repo_dir
    # tmp_path is auto-cleaned by pytest
