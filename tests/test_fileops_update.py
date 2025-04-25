import pytest

from fileops.update import update_version_file


@pytest.mark.parametrize(
    "initial_content, new_version, expected_content, raises_error, error_message",
    [
        ("version: 1.0.0\n", "2.0.0", "version: 2.0.0\n", False, None),
        ("no version here\n", "2.0.0", None, True, "No version pattern found"),
        ("version: '1.0.0'\n", "2.0.0", "version: '2.0.0'\n", False, None),
        ('version: "1.0.0"\n', "2.0.0", 'version: "2.0.0"\n', False, None),
        ("version: 1.0.0-dev\n", "2.0.0", "version: 2.0.0-dev\n", False, None),
        ("version: 1.0.0-staging\n", "2.0.0", "version: 2.0.0-staging\n", False, None),
        ("version: v1.0.0\n", "2.0.0", "version: v2.0.0\n", False, None),
        ("version: 1.0.0\n", "", None, True, "New version cannot be empty"),
        ("", "2.0.0", None, True, "No version pattern found"),
    ],
)
def test_update_version_file(
    tmp_path,
    initial_content,
    new_version,
    expected_content,
    raises_error,
    error_message,
):
    file = tmp_path / "version.txt"
    file.write_text("version: 1.2.3\n")

    update_version_file(file, "2.0.0")
    assert file.read_text() == "version: 2.0.0\n"


@pytest.mark.parametrize(
    "initial_content, new_version, expected_content, raises_error, error_message",
    [
        ("version: 1.0.0\n", "2.0.0", "version: 2.0.0\n", False, None),
        ("no version here\n", "2.0.0", None, True, "No version pattern found"),
        ("version: '1.0.0'\n", "2.0.0", "version: '2.0.0'\n", False, None),
        ('version: "1.0.0"\n', "2.0.0", 'version: "2.0.0"\n', False, None),
        ("version: 1.0.0-dev\n", "2.0.0", "version: 2.0.0-dev\n", False, None),
        ("version: 1.0.0-staging\n", "2.0.0", "version: 2.0.0-staging\n", False, None),
        ("version: v1.0.0\n", "2.0.0", "version: v2.0.0\n", False, None),
        ("version: 1.0.0\n", "", None, True, "New version cannot be empty"),
        ("", "2.0.0", None, True, "No version pattern found"),
    ],
)
def test_update_version_logging(
    tmp_path,
    caplog,
    initial_content,
    new_version,
    expected_content,
    raises_error,
    error_message,
):
    file = tmp_path / "version.txt"
    file.write_text("version: 1.2.3\n")

    with caplog.at_level("DEBUG"):
        update_version_file(file, "2.0.0")

    assert "Updating version in" in caplog.text
    assert "Matched line:" in caplog.text
    assert "Preserved groups:" in caplog.text
    assert "Version line updated to" in caplog.text
