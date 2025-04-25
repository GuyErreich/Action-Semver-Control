import pytest

from gitops.pr import create_or_update_pr


@pytest.mark.parametrize(
    "existing_pr, post_called",
    [
        ([{"html_url": "https://github.com/test/repo/pull/1"}], False),  # Existing PR
        ([], True),  # New PR
    ],
)
def test_create_or_update_pr(mocker, existing_pr, post_called):
    mock_get = mocker.patch("gitops.pr.requests.get")
    mock_post = mocker.patch("gitops.pr.requests.post")

    # Mock the GET request
    mock_get.return_value.json.return_value = existing_pr
    mock_get.return_value.ok = True

    # Mock the POST request
    mock_post.return_value.json.return_value = {"html_url": "https://github.com/test/repo/pull/2"}
    mock_post.return_value.ok = True

    # Call the function
    create_or_update_pr(
        token="fake_token",
        repo="test/repo",
        branch="feature-branch",
        base_branch="main",
        title="Test PR",
        body="This is a test PR",
    )

    # Assert GET was called correctly
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/test/repo/pulls?head=test:feature-branch&base=main",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github+json",
        },
    )

    # Assert POST was called or not based on the scenario
    if post_called:
        mock_post.assert_called_once_with(
            "https://api.github.com/repos/test/repo/pulls",
            headers={
                "Authorization": "token fake_token",
                "Accept": "application/vnd.github+json",
            },
            json={
                "title": "Test PR",
                "head": "feature-branch",
                "base": "main",
                "body": "This is a test PR",
            },
        )
    else:
        mock_post.assert_not_called()


def test_create_or_update_pr_failed_creation(mocker):
    mock_get = mocker.patch("gitops.pr.requests.get")
    mock_post = mocker.patch("gitops.pr.requests.post")

    # Mock the GET request to simulate no existing PR
    mock_get.return_value.json.return_value = []
    mock_get.return_value.ok = True

    # Mock the POST request to simulate failed PR creation
    mock_post.return_value.ok = False
    mock_post.return_value.text = "Error creating PR"

    # Call the function
    create_or_update_pr(
        token="fake_token",
        repo="test/repo",
        branch="feature-branch",
        base_branch="main",
        title="Test PR",
        body="This is a test PR",
    )

    # Assert GET was called correctly
    mock_get.assert_called_once_with(
        "https://api.github.com/repos/test/repo/pulls?head=test:feature-branch&base=main",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github+json",
        },
    )

    # Assert POST was called correctly
    mock_post.assert_called_once_with(
        "https://api.github.com/repos/test/repo/pulls",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github+json",
        },
        json={
            "title": "Test PR",
            "head": "feature-branch",
            "base": "main",
            "body": "This is a test PR",
        },
    )
