from jinja2 import Template, TemplateSyntaxError
from pydantic import BaseModel, Field, field_validator
from ..semver import Version
from textwrap import dedent
from .constants import DEFAULT_CHANGELOG


class PullRequestConfig(BaseModel):
    labels: list[str] = Field(
        default=["semver-bump"],
        min_length=1,
        description="List of labels to apply to the pull request.",
    )
    title: str = Field(
        default="Release {{version}}",
        description="Title template for the pull request.",
    )
    body: str = Field(
        default="Auto-created PR by auto-semver.",
        description="Body template for the pull request.",
    )

    @field_validator("title", "body")
    @classmethod
    def validate_jinja_template(cls, value: str) -> str:
        try:
            Template(value)  # Check if it compiles
        except TemplateSyntaxError as err:
            raise ValueError(f"Invalid Jinja2 template: {err}")
        return value

    def render_title(self, **kwargs) -> str:
        return Template(self.title).render(**kwargs)

    def render_body(self, **kwargs) -> str:
        return Template(self.body).render(**kwargs)

class ChangelogConfig(BaseModel):
    file: str = Field(
        default=DEFAULT_CHANGELOG,
        description="Path to the changelog file."
    )
    truncate: bool = Field(
        default=False,
        description="If true, overwrite the changelog instead of prepending."
    )
    template: str = Field(
        default=dedent("""
        ## [{{version}}] - {{date}}
        {% for msg in messages -%}
        - {{ msg }}
        {%- endfor %}
        """),
        description="Jinja template for changelog entries."
    )
    header: str | None = Field(default="", description="Optional header text for the changelog.")
    footer: str | None = Field(default="", description="Optional footer text for the changelog.")

class ConfigData(BaseModel):
    start_version: Version =  Field(default="0.1.0", description="Optional start_version.")
    suffixes: dict[str, str] = Field(..., description="Required branch suffix mapping.")
    version_files: list[str] = Field(default="version.txt", description="Optional files that hold version format to update.")
    branch_strategy: str = "single"
    pull_request: PullRequestConfig
    changelog: ChangelogConfig

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator("start_version", mode="before")
    @classmethod
    def parse_start_version(cls, v: str) -> Version:
        return Version.parse(v)