"""Tests for onboarding URL builders."""

from urllib.parse import parse_qs, urlparse

import pytest

from auto_semver.setup.links import (
    app_registration_url,
    load_template,
    new_file_pr_url,
    org_app_registration_url,
    workflow_bump_deep_link,
    workflow_promote_deep_link,
)


@pytest.mark.unit
def test_app_registration_url_prefills_permissions() -> None:
    """Registration URL sets contents and pull_requests write."""
    url = app_registration_url(app_name="Test Semver Bot")
    parsed = urlparse(url)
    assert parsed.path == "/settings/apps/new"
    params = parse_qs(parsed.query)
    assert params["name"] == ["Test Semver Bot"]
    assert params["contents"] == ["write"]
    assert params["pull_requests"] == ["write"]
    assert params["webhook_active"] == ["false"]


@pytest.mark.unit
def test_new_file_pr_url_encodes_content() -> None:
    """New file deep link includes filename and value query params."""
    url = new_file_pr_url(
        owner="acme",
        repo="demo",
        branch="master",
        filename=".github/workflows/auto-semver.yml",
        content="name: test\n",
        message="Add workflow",
        pr_branch="add-semver",
    )
    assert "github.com/acme/demo/new/master" in url
    assert "filename=" in url
    assert "value=" in url
    assert "quick_pull=" in url


@pytest.mark.unit
def test_workflow_bump_deep_link_uses_template() -> None:
    """Bump deep link references the reusable workflow template."""
    url = workflow_bump_deep_link(owner="acme", repo="demo", branch="dev")
    assert "semver-bump.reusable.yml" in url
    assert "acme/demo/new/dev" in url


@pytest.mark.unit
def test_load_template_auto_semver_config() -> None:
    """Minimal config template loads from templates/onboarding."""
    content = load_template("auto_semver_config.yml")
    assert "start_version:" in content
    assert "suffixes:" in content


@pytest.mark.unit
def test_org_app_registration_url() -> None:
    """Org registration URL targets the organization settings path."""
    url = org_app_registration_url(org="my-org")
    assert "/organizations/my-org/settings/apps/new" in url
    assert "contents=write" in url


@pytest.mark.unit
def test_workflow_promote_deep_link_uses_template() -> None:
    """Promote deep link references the reusable promote workflow."""
    url = workflow_promote_deep_link(owner="acme", repo="demo", branch="staging")
    assert "semver-promote.reusable.yml" in url
    assert "acme/demo/new/staging" in url
