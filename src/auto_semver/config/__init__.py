# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Public config package entry point.

Import ``Config`` from here. Schema / pydantic model classes live in
``auto_semver.config._models`` and are for typing (and rare runtime construction
when applying config) — not a second public API surface.
"""

from auto_semver.config.config import Config

__all__ = ["Config"]
