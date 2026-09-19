# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sync language package lockfiles after version bumps."""

from .sync import sync_package_locks

__all__ = ["sync_package_locks"]
