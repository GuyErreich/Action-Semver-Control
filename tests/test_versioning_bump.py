import pytest

from versioning.bump import bump_version, parse_bump


@pytest.mark.parametrize(
    "branch,default,expected",
    [
        ("feature/new-feature", "patch", "minor"),
        ("fix/bug-fix", "minor", "patch"),
        ("breaking/api", "patch", "major"),
        ("docs/readme", "minor", "minor"),
    ],
)
def test_parse_bump(branch, default, expected):
    """Test the `parse_bump` function.

    Ensure it returns the expected result based on the provided branch name
    and default bump value.

    Args:
        branch (str): The name of the branch to parse for bump information.
        default (str): The default bump value to use if no specific bump is found.
        expected (str): The expected result of the `parse_bump` function.

    Raises:
        AssertionError: If the result of `parse_bump` does not match the expected value.

    """

    assert parse_bump(branch, default) == expected


@pytest.mark.parametrize(
    "current,bump_type,suffix,expected",
    [
        ("v1.2.3", "patch", None, "v1.2.4"),
        ("v1.2.3", "minor", None, "v1.3.0"),
        ("v1.2.3", "major", None, "v2.0.0"),
        ("v1.2.3", "patch", "dev", "v1.2.4-dev"),
        ("v1.2.3", "minor", "staging", "v1.3.0-staging"),
    ],
)
def test_bump_version(current, bump_type, suffix, expected):
    """Test that `bump_version` produces the expected version string.

    Args:
        current (str): Current version string (e.g., "1.0.0").
        bump_type (str): Type of version bump ("major", "minor", "patch").
        suffix (str): Optional suffix to append to the version (e.g., "-beta").
        expected (str): Expected version string after the bump.

    Raises:
        AssertionError: If the result of `bump_version` does not match the expected value.

    """

    assert bump_version(current, bump_type, suffix) == expected
