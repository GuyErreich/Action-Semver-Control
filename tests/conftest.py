from collections.abc import Generator
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from tests.helpers.fake_repo_scenerio import FakeGitScenario


@pytest.fixture
def fake_git_environment(
    request: pytest.FixtureRequest,
    fs: FakeFilesystem,
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch
) -> Generator[tuple[FakeFilesystem, FakeGitScenario], None, None]:
    """
    Fixture to create a fake Git repository with a specific structure for testing.
    
    This fixture sets up a mock Git repository with a specific directory structure,
    including version files, a lock file, and a GitHub event JSON file.
    It also mocks the Git repository and its branches and tags for testing purposes.
    The fixture yields the fake filesystem object, which can be used in tests to
    interact with the mock repository.
    """

    scenario: FakeGitScenario = getattr(request, "param", FakeGitScenario({}, {}, {}, {}))

    # Filesystem layout
    # Prepare repo base
    fs.cwd = "/repo"
    fs.makedirs("/repo/.github", exist_ok=True)

    full_path: str = ""

    # Add files
    for path, content in scenario.files.items():
        full_path = str(Path("/repo") / path)
        fs.create_file(full_path, contents=content)

    # Template-rendered files
    for path, content in scenario.render_template_files().items():
        full_path = str(Path("/repo") / path)
        fs.create_file(full_path, contents=content)

    # Patch git.Repo
    mock_repo = mocker.MagicMock()

    # Setup branches
    mock_repo.heads = {
        name: mocker.MagicMock(name=name) for name in scenario.branches
    }

    # Setup tags
    mock_repo.tags = []
    for tag, sha in scenario.tags.items():
        tag_mock = mocker.MagicMock()
        tag_mock.name = tag
        tag_mock.commit.hexsha = sha
        mock_repo.tags.append(tag_mock)

    # Add remotes if needed
    if scenario.remotes:
        mock_remote = mocker.MagicMock()
        mock_remote.refs = []
        for remote_branch, shas in scenario.remotes.get("origin", {}).items():
            ref_mock = mocker.MagicMock()
            ref_mock.name = f"origin/{remote_branch}"
            ref_mock.commit.hexsha = shas[-1] if shas else "deadbeef"
            mock_remote.refs.append(ref_mock)
        mock_repo.remotes = [mock_remote]

    mock_repo.commit.return_value.hexsha = "abc123"

    mocker.patch("auto_semver.git.ops.Repo", return_value=mock_repo)

    mock_gh = mocker.MagicMock()
    mock_repo_api = mocker.MagicMock()
    mock_gh.get_repo.return_value = mock_repo_api

    mocker.patch("auto_semver.git.ops.Github", return_value=mock_gh)
    

    monkeypatch.setenv("GITHUB_EVENT_PATH", "/repo/.github/event.json")

    yield fs, scenario