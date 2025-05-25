import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
env = Environment(loader=FileSystemLoader(ASSETS_DIR))

TEMPLATES = {
    name: env.get_template(name)
    for name in env.list_templates()
}

class FakeGitScenario:

    """
    A class to represent a fake Git scenario for testing purposes.

    Supports static files or template rendering from Jinja2.
    """

    def __init__(
        self,
        expected: dict[str, Any] | None = None,
        files: dict[str, str] | None = None,
        branches: dict[str, list[str]] | None = None,
        tags: dict[str, str] | None = None,
        remotes: dict[str, dict[str, list[str]]] | None = None,
        use_templates: list[str] | None = None,
        template_data: dict[str, Any] | None = None
    ):
        self.files = files or {}
        self.branches = branches or {}
        self.tags = tags or {}
        self.remotes = remotes or {}
        self.use_templates = use_templates or []
        self.template_data = template_data or {}
        self.expected = expected or {}

    def render_template_files(self) -> dict[str, str]:
        rendered = {}
        
        for name in self.use_templates:
            file_name = name.lstrip("/").replace(".github/", "")  # removes .github/ but keeps leading dot
            if not file_name.endswith(".j2"):
                file_name += ".j2"

            if file_name not in TEMPLATES:
                raise ValueError(f"Template '{file_name}' not preloaded")

            template = TEMPLATES[file_name]
            rendered[name] = template.render(self.template_data)
        return rendered