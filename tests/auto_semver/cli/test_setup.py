"""Tests for setup CLI dispatch."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from auto_semver.cli.main import main


@pytest.mark.unit
def test_main_setup_dispatches_before_config(mocker: MockerFixture) -> None:
    """Setup subcommand runs without loading Config or GitOps."""
    mock_setup = mocker.patch("auto_semver.cli.main.setup.run")
    mocker.patch(
        "sys.argv",
        [
            "auto-semver",
            "setup",
            "--dry-run",
            "--skip-secrets",
            "--skip-scaffold",
            "--owner",
            "acme",
            "--repo",
            "demo",
        ],
    )
    mock_config = mocker.patch("auto_semver.cli.main.Config")
    mock_gitops = mocker.patch("auto_semver.cli.main.GitOps")

    main()

    mock_setup.assert_called_once()
    mock_config.assert_not_called()
    mock_gitops.assert_not_called()


@pytest.mark.unit
def test_setup_parser_accepts_private_key_path(mocker: MockerFixture) -> None:
    """Setup forwards --private-key to setup.run."""
    mock_setup = mocker.patch("auto_semver.cli.main.setup.run")
    key_path = Path("/tmp/test.pem")
    mocker.patch(
        "sys.argv",
        [
            "auto-semver",
            "setup",
            "--dry-run",
            "--skip-secrets",
            "--skip-scaffold",
            "--private-key",
            str(key_path),
        ],
    )

    main()

    call_kwargs = mock_setup.call_args.kwargs
    assert call_kwargs["private_key_path"] == key_path
