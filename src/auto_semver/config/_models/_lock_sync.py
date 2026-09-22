# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Package-manager lockfile sync configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Register built-ins before validation reads the registry.
import auto_semver.lock_sync.strategies as _lock_sync_strategies  # noqa: F401
from auto_semver.lock_sync.registry import default_registry

OnMissingPolicy = Literal["skip", "fail"]


class LockSyncConfig(BaseModel):
    """Controls post-bump sync of language package lockfiles."""

    enabled: bool = Field(
        default=True,
        description="When true, sync known lockfiles after version-file rewrites",
    )
    on_missing: OnMissingPolicy = Field(
        default="skip",
        description="skip: warn and continue when the lock CLI is missing; fail: abort the bump",
    )
    ecosystems: list[str] | None = Field(
        default=None,
        description=(
            "Allow-list of ecosystems to sync (registered strategy names). "
            "Omit to auto-detect every known lockfile present at the repo root."
        ),
    )

    @field_validator("ecosystems", mode="before")
    @classmethod
    def validate_ecosystems(cls, value: object) -> object:
        """Reject unknown ecosystem names early with a clear message."""
        if value is None:
            return value
        if not isinstance(value, list):
            raise ValueError("ecosystems must be a list of ecosystem names")
        known = default_registry.names()
        unknown = [item for item in value if item not in known]
        if unknown:
            raise ValueError(f"Unknown lock_sync ecosystems: {unknown}. Supported: {sorted(known)}")
        return value
