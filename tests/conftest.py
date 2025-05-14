import pytest


@pytest.fixture
def fake_args():
    return [
        "--branch-name", "bufix/test",
        "--target-branch", "dev",
        "--github-token", "ghp_mocktoken",
        "--repo-full-name", "example/repo",
        "--debug",
    ]