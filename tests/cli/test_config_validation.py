
import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import FixtureRequest, MonkeyPatch
from pytest_mock import MockerFixture

from auto_semver.cli import main
from tests.cli.scenarios import SCENARIOS
from tests.helpers.fake_repo_scenerio import FakeGitScenario


@pytest.mark.parametrize(
    "fake_git_environment",
    [
        pytest.param(SCENARIOS["basic-bump"], id="basic-bump"),
        pytest.param(SCENARIOS["missing-version-file"], id="missing-version-file"),
        pytest.param(SCENARIOS["no-semver-lock"], id="no-semver-lock"),
    ],
    indirect=True
)
def test_main_cli_scenarios(
    fake_git_environment: tuple[FakeFilesystem, FakeGitScenario],
    monkeypatch: MonkeyPatch,
    mocker: MockerFixture,
    request: FixtureRequest
) -> None:
    fs, scenario = fake_git_environment

    monkeypatch.setattr("sys.argv", [
        "auto-semver",
        "--github-token", "dummy",
        "--debug"
    ])

    main()

    for file, expected in scenario.expected.get("files", {}).items():
        assert fs.exists(file), f"{file} should exist"
        content: str = str(fs.get_object("version.txt").contents)
        assert expected in content, f"Expected content not found in {file}"
