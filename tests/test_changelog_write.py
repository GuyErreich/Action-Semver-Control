import logging

import pytest

from src.changelog.write import prepend_changelog


FIXED_DATE = "2023-01-01"


@pytest.fixture
def mock_date_today(mocker):
    mock_date = mocker.patch("src.changelog.write.datetime")
    mock_date.date.today.return_value.isoformat.return_value = FIXED_DATE


@pytest.fixture
def temp_changelog_file(tmp_path):
    return tmp_path / "CHANGELOG.md"


@pytest.mark.parametrize(
    "version, branch, existing_content, expected_content",
    [
        ("1.0.0", "main", "", f"## 1.0.0 - {FIXED_DATE}\n\n- Merged from `main`\n\n"),
        (
            "2.3.4",
            "feature/login",
            "Existing content\n",
            f"## 2.3.4 - {FIXED_DATE}\n\n- Merged from `feature/login`\n\nExisting content\n",
        ),
    ],
)
def test_prepend_changelog(
    mock_date_today,
    temp_changelog_file,
    version,
    branch,
    existing_content,
    expected_content,
):
    changelog_file = temp_changelog_file

    if existing_content:
        changelog_file.write_text(existing_content)

    prepend_changelog(version, branch, changelog_file)

    content = changelog_file.read_text()

    print("Expected:", repr(expected_content))
    print("Actual:  ", repr(changelog_file.read_text()))
    assert content == expected_content


def test_prepend_changelog_logs_debug(mock_date_today, temp_changelog_file, caplog):
    version = "1.0.0"
    branch = "main"

    with caplog.at_level(logging.DEBUG):
        prepend_changelog(version, branch, temp_changelog_file)

    assert "Updating changelog" in caplog.text
    assert "Changelog updated" in caplog.text
