"""
Unit tests for config data module in auto_semver.config.data.

This module contains comprehensive tests for all classes and methods in the data module,
including PullRequestConfig, ChangelogConfig, and ConfigData validator functions.
"""

import pytest
from pydantic import ValidationError

from auto_semver.config.data import ChangelogConfig, ConfigData, PromotionRule, PullRequestConfig
from auto_semver.semver import Version


class TestPullRequestConfig:
    """Test cases for PullRequestConfig class."""

    @pytest.mark.unit
    def test_basic_initialization(self) -> None:
        """Test basic initialization with valid data."""
        pr_config = PullRequestConfig(
            title="Release {{version}}",
            body="- Version: {{version}}\n- Date: {{date}}",
            labels=["semver-bump", "automated"],
        )

        assert pr_config.title == "Release {{version}}"
        assert pr_config.body == "- Version: {{version}}\n- Date: {{date}}"
        assert pr_config.labels == ["semver-bump", "automated"]

    @pytest.mark.unit
    def test_render_title(self) -> None:
        """Test rendering the PR title with a version."""
        pr_config = PullRequestConfig(title="Release {{version}}", body="", labels=["test-label"])

        rendered = pr_config.render_title(version="1.2.3")
        assert rendered == "Release 1.2.3"

    @pytest.mark.unit
    def test_render_body(self) -> None:
        """Test rendering the PR body with version, date, and messages."""
        pr_config = PullRequestConfig(
            title="",
            body="- Version: {{version}}\n- Date: {{date}}\n{% for msg in messages %}- {{ msg }}\n{% endfor %}",
            labels=["test-label"],
        )

        rendered = pr_config.render_body(
            version="1.2.3", date="01-01-2025", messages=["Fix bug", "Add feature"]
        )

        # Account for the hidden marker comment added by render_body
        expected = "<!-- auto-semver:pr -->\n- Version: 1.2.3\n- Date: 01-01-2025\n- Fix bug\n- Add feature\n"
        assert rendered == expected

    @pytest.mark.unit
    def test_invalid_template_syntax_in_title(self) -> None:
        """Test validation catches invalid Jinja2 syntax in title."""
        with pytest.raises(ValueError, match="Invalid Jinja2 template"):
            PullRequestConfig(
                title="Release {{ version",  # Missing closing brace
                body="",
                labels=["test-label"],
            )

    @pytest.mark.unit
    def test_invalid_template_syntax_in_body(self) -> None:
        """Test validation catches invalid Jinja2 syntax in body."""
        with pytest.raises(ValueError, match="Invalid Jinja2 template"):
            PullRequestConfig(
                title="",
                body="{% for msg in messages %}- {{ msg }}",  # Missing endfor
                labels=["test-label"],
            )


class TestChangelogConfig:
    """Test cases for ChangelogConfig class."""

    @pytest.mark.unit
    def test_basic_initialization(self) -> None:
        """Test basic initialization with valid data."""
        changelog_config = ChangelogConfig(
            file="CHANGELOG.md",
            truncate=False,
            template="## [{{version}}] - {{date}}\n",
            header="# Changelog",
            footer="## License",
        )

        assert changelog_config.file == "CHANGELOG.md"
        assert changelog_config.truncate is False
        assert changelog_config.template == "## [{{version}}] - {{date}}\n"
        assert changelog_config.header == "# Changelog"
        assert changelog_config.footer == "## License"

    @pytest.mark.unit
    def test_optional_fields(self) -> None:
        """Test initialization with default values for optional fields."""
        changelog_config = ChangelogConfig(
            file="CHANGELOG.md",
            truncate=True,
            template="## [{{version}}] - {{date}}\n",
            header=None,
            footer=None,
        )

        assert changelog_config.header is None
        assert changelog_config.footer is None

    @pytest.mark.unit
    def test_invalid_template_syntax(self) -> None:
        """Test validation catches invalid Jinja2 syntax in template."""
        with pytest.raises(ValueError, match="Invalid template syntax:"):
            ChangelogConfig(
                file="CHANGELOG.md",
                truncate=False,
                template="## [{{version] - {{date}}\n",  # Missing closing brace
            )


class TestPromotionRule:
    """Test cases for PromotionRule class."""

    @pytest.mark.unit
    def test_basic_initialization(self) -> None:
        """Test basic initialization with valid data."""
        rule = PromotionRule(from_branch="dev", to_branch="main")

        assert rule.from_branch == "dev"
        assert rule.to_branch == "main"


class TestConfigData:
    """Test cases for ConfigData class."""

    @pytest.mark.unit
    def test_basic_initialization(self) -> None:
        """Test basic initialization with valid data."""
        config = ConfigData(
            start_version="0.1.0",  # type: ignore[arg-type]
            suffixes={"dev": "-dev", "staging": "-rc", "main": ""},
            version_files=["version.txt", "pyproject.toml"],
            branch_strategy="single",
            promotions=[
                PromotionRule(from_branch="dev", to_branch="staging"),
                PromotionRule(from_branch="staging", to_branch="main"),
            ],
            pull_request=PullRequestConfig(
                title="Release {{version}}", body="Version: {{version}}", labels=["semver-bump"]
            ),
            changelog=ChangelogConfig(
                file="CHANGELOG.md", truncate=False, template="## [{{version}}] - {{date}}\n"
            ),
        )

        assert config.start_version.major == 0
        assert config.start_version.minor == 1
        assert config.start_version.patch == 0
        assert config.suffixes == {"dev": "-dev", "staging": "-rc", "main": ""}
        assert config.version_files == ["version.txt", "pyproject.toml"]
        assert config.branch_strategy == "single"
        assert isinstance(config.pull_request, PullRequestConfig)
        assert isinstance(config.changelog, ChangelogConfig)

    @pytest.mark.unit
    def test_optional_promotions(self) -> None:
        """Test initialization with promotions."""
        config = ConfigData(
            start_version=str(Version(major=0, minor=1, patch=0)),  # type: ignore[arg-type]
            suffixes={"dev": "-dev", "staging": "-rc", "main": ""},
            version_files=["version.txt"],
            branch_strategy="multi",
            pull_request=PullRequestConfig(title="", body="", labels=["test-label"]),
            changelog=ChangelogConfig(file="CHANGELOG.md", truncate=False, template=""),
            promotions=[
                PromotionRule(from_branch="dev", to_branch="staging"),
                PromotionRule(from_branch="staging", to_branch="main"),
            ],
        )

        assert len(config.promotions) == 2
        assert config.promotions[0].from_branch == "dev"
        assert config.promotions[0].to_branch == "staging"
        assert config.promotions[1].from_branch == "staging"
        assert config.promotions[1].to_branch == "main"

    @pytest.mark.unit
    def test_invalid_branch_strategy(self) -> None:
        """Test validation catches invalid branch strategy."""
        with pytest.raises(ValidationError, match="Input should be 'single' or 'multi'"):
            ConfigData(
                start_version=str(Version(major=0, minor=1, patch=0)),  # type: ignore[arg-type]
                suffixes={"dev": "-dev", "staging": "-rc", "main": ""},
                version_files=["version.txt"],
                # Invalid strategy
                branch_strategy="invalid",  # type: ignore[arg-type]
                promotions=[
                    PromotionRule(from_branch="dev", to_branch="staging"),
                    PromotionRule(from_branch="staging", to_branch="main"),
                ],
                pull_request=PullRequestConfig(title="", body="", labels=["test-label"]),
                changelog=ChangelogConfig(file="CHANGELOG.md", truncate=False, template=""),
            )

    @pytest.mark.unit
    def test_missing_suffix_for_branch(self) -> None:
        """Test validation catches branch without defined suffix."""
        with pytest.raises(ValueError, match="missing suffix definitions"):
            ConfigData(
                start_version=str(Version(major=0, minor=1, patch=0)),  # type: ignore[arg-type]
                suffixes={"dev": "-dev", "staging": "-rc"},  # Missing "main"
                version_files=["version.txt"],
                branch_strategy="multi",
                pull_request=PullRequestConfig(title="", body="", labels=["test-label"]),
                changelog=ChangelogConfig(file="CHANGELOG.md", truncate=False, template=""),
                promotions=[
                    PromotionRule(from_branch="dev", to_branch="staging"),
                    PromotionRule(
                        from_branch="staging", to_branch="main"
                    ),  # "main" not in suffixes
                ],
            )
