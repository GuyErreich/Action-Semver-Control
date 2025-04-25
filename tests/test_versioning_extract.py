import pytest

from versioning.extract import SemverGroups, version


@pytest.fixture
def mock_semver_regex(mocker):
    """Mock the SEMVER_REGEX constant in the versioning.extract module.

    This function is a generator that uses the `patch` function from the `unittest.mock`
    module to temporarily replace the `SEMVER_REGEX` constant with a mock object.
    It is intended to be used in tests to control or inspect the behavior of code
    that relies on `SEMVER_REGEX`.

    Args:
        mocker: The pytest-mock fixture used to apply the patch.

    Yields:
        Mock object for the `SEMVER_REGEX` constant.

    """

    return mocker.patch("versioning.extract.SEMVER_REGEX")


@pytest.mark.parametrize(
    "file_content, mock_group_side_effect, expected_result",
    [
        # Full match case with version key
        (
            'version: "v1.0.0-beta"',
            ["version: ", '"', "v", "1.0.0", "-beta", '"'],
            {
                SemverGroups.TITLE: "version: ",
                SemverGroups.STARTING_QUOTE: '"',
                SemverGroups.PREFIX: "v",
                SemverGroups.VERSION: "1.0.0",
                SemverGroups.SUFFIX: "-beta",
                SemverGroups.ENDING_QUOTE: '"',
            },
        ),
        (
            "version: 'v2.3.4'",
            ["version: ", "'", "v", "2.3.4", None, "'"],
            {
                SemverGroups.TITLE: "version: ",
                SemverGroups.STARTING_QUOTE: "'",
                SemverGroups.PREFIX: "v",
                SemverGroups.VERSION: "2.3.4",
                SemverGroups.SUFFIX: None,
                SemverGroups.ENDING_QUOTE: "'",
            },
        ),
        (
            "version: '2.3.4'",
            ["version: ", "'", None, "2.3.4", None, "'"],
            {
                SemverGroups.TITLE: "version: ",
                SemverGroups.STARTING_QUOTE: "'",
                SemverGroups.PREFIX: None,
                SemverGroups.VERSION: "2.3.4",
                SemverGroups.SUFFIX: None,
                SemverGroups.ENDING_QUOTE: "'",
            },
        ),
        (
            "version: v2.3.4",
            ["version: ", None, "v", "2.3.4", None, None],
            {
                SemverGroups.TITLE: "version: ",
                SemverGroups.STARTING_QUOTE: None,
                SemverGroups.PREFIX: "v",
                SemverGroups.VERSION: "2.3.4",
                SemverGroups.SUFFIX: None,
                SemverGroups.ENDING_QUOTE: None,
            },
        ),
        # Case with additional options
        (
            'name: example\nversion: "v2.3.4"\ndescription: test',
            ["version: ", '"', "v", "2.3.4", None, '"'],
            {
                SemverGroups.TITLE: "version: ",
                SemverGroups.STARTING_QUOTE: '"',
                SemverGroups.PREFIX: "v",
                SemverGroups.VERSION: "2.3.4",
                SemverGroups.SUFFIX: None,
                SemverGroups.ENDING_QUOTE: '"',
            },
        ),
        # No version key case
        (
            "name: example\ndescription: test",
            [None] * 6,
            {
                SemverGroups.TITLE: None,
                SemverGroups.STARTING_QUOTE: None,
                SemverGroups.PREFIX: None,
                SemverGroups.VERSION: None,
                SemverGroups.SUFFIX: None,
                SemverGroups.ENDING_QUOTE: None,
            },
        ),
        # Empty content case
        ("", None, None),
    ],
)
def test_version(mock_semver_regex, file_content, mock_group_side_effect, expected_result):
    """Test the version extraction function with various file content and expected results.

    Args:
        mock_semver_regex: Mocked SEMVER_REGEX object.
        file_content: The content of the file to be tested.
        mock_group_side_effect: Side effects for the mock match group.
        expected_result: The expected result of the version extraction.

    """

    if mock_group_side_effect is not None:
        mock_match = mock_semver_regex.search.return_value
        mock_match.group.side_effect = mock_group_side_effect
    else:
        mock_semver_regex.search.return_value = None

    assert version(file_content) == expected_result
