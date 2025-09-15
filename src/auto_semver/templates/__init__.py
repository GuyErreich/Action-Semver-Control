"""Templates package public API.

Expose the primary engine class, helper functions, and common type aliases at the
package level so consumers can import from ``auto_semver.templates`` directly.
"""

from .engine import (
    TemplateEngine,
    get_template_engine,
    reset_template_engine,
)
from .types import (
    TemplateFunction,
    TemplateVariables,
)

__all__ = [
    "TemplateEngine",
    "TemplateFunction",
    "TemplateVariables",
    "get_template_engine",
    "reset_template_engine",
]
