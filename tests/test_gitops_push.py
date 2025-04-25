import pytest
from git import GitCommandError

from gitops.push import push_with_retry


@pytest.mark.parametrize(
    "side_effect, expected_call_count, should_raise",
    [
        (None, 1, False),  # Simulate successful push
        ([GitCommandError("push", "error")] * 3, 3, True),  # Simulate push failure
        (
            [GitCommandError("push", "error"), GitCommandError("push", "error"), None],
            3,
            False,
        ),  # Partial failure
    ],
)
def test_push_with_retry(mocker, side_effect, expected_call_count, should_raise):
    mocker.patch("gitops.push.time.sleep", return_value=None)
    remote = mocker.MagicMock()
    remote.push.side_effect = side_effect
    branch = "main"

    if should_raise:
        with pytest.raises(SystemExit) as excinfo:
            push_with_retry(remote, branch, retries=3, delay=1)
        assert excinfo.value.code == 1
    else:
        push_with_retry(remote, branch, retries=3, delay=1)

    assert remote.push.call_count == expected_call_count
