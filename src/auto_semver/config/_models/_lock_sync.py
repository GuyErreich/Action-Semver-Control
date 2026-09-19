# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: MIT
"""Package-manager lockfile sync configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

KNOWN_ECOSYSTEMS = frozenset({"uv", "npm"})
EcosystemName = Literal["uv", "npm"]
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
    ecosystems: list[EcosystemName] | None = Field(
        default=None,
        description=(
            "Allow-list of ecosystems to sync. "
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
        unknown = [item for item in value if item not in KNOWN_ECOSYSTEMS]
        if unknown:
            raise ValueError(
                f"Unknown lock_sync ecosystems: {unknown}. Supported: {sorted(KNOWN_ECOSYSTEMS)}"
            )
        return value
