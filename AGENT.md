# Workspace Agent Notes

This file defines global working rules for the repository.

## Core Rules

- Reuse before creating: check existing modules, helpers, and patterns before adding new ones.
- Prefer absolute imports under `auto_semver.*` (no forced relative imports inside the package).
- Keep domain logic in `domain/`, VCS I/O in `adapters/git/`, and YAML schema in `config/`.

## Config entry point

- **Public entry:** `from auto_semver.config import Config` (load / access configuration).
- **Private schema:** `auto_semver.config._models` holds pydantic / dataclass schema types.
- Outside `config/`, import `_models` **only as types** — put those imports under `TYPE_CHECKING` (with `from __future__ import annotations`) so they enforce variable/parameter annotations without becoming a second runtime API.
- **Allowed runtime exception:** a module that must *construct* schema value objects while applying `Config` (today: `domain/commits/grouper.py`) may import the needed `_models` at runtime. Keep that list tiny; do not grow it casually.
- Do not re-export `_models` symbols from `config/__init__.py`. Tests may import `_models` directly when building fixtures.

## Folder map (src/auto_semver)

- `config/` — `Config` loader + `_models` schema
- `domain/` — commits, semver, changelog, PR content
- `adapters/git/` — git operations (`GitOpsBase` + focused ops modules)
- `cli/` — CLI entrypoints
- `templates/` — Jinja engine + shared template utils
- `setup/` — scaffolds / init helpers
- `log.py` — logging setup

## Validate

- Base branch for branch/PR diffs: `dev`.
- Lint: `task lint` — 0 errors required.
- Type-check: `task type-check` — must succeed.
- Tests: `task test` — must succeed.
- Audit: `task audit` — must succeed when dependencies/lockfile change.

CI and milestone skills read these commands and the base branch from this block.

- Run lint, type-check, and tests at review / commit / PR milestones.
- Record pass/fail from raw shell exit codes.

## Review scope

When reviewing, materialize the full surface: the tier diff (for PR/push prefer `merge-base...HEAD` against `dev`), plus the nearest `AGENT.md` for every changed path (leaf → root), plus the skills routed by the changed file types.
