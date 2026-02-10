# Auto Semver Action

A custom GitHub Action written in Python to automatically bump semantic versioning, update changelogs, and create Pull Requests — fully configurable.

## Features
- Auto bump `major`, `minor`, or `patch` depending on branch type
- Add suffixes (`-dev`, `-rc`) depending on the target branch
- Auto-create release branches
- Auto-close old release PRs (single branch mode)
- Label bump PRs automatically (`semver-bump`)
- 100% typed Python (>=3.12)
- No subprocess — uses GitPython and Requests libraries only
- Fully Dockerized for clean CI/CD usage
- Comprehensive test coverage with pytest and pyfakefs
- Modern Python tooling (ruff, mypy, pre-commit)

## CLI Usage

The action is primarily designed to run in CI/CD, but the CLI can be used for manual operations.

### Manual Promotion
To manually promote a version from one branch to another (e.g., `dev` -> `staging`):

```bash
auto-semver --github-token <TOKEN> promote --from-branch dev --to-branch staging
```

Options:
- `--dry-run`: Validate the promotion without creating a PR.

## Configuration (`auto_semver_config.yml`)

```yaml
start_version: "0.1.0"

suffixes:
  dev: "-dev"
  staging: "-rc"
  main: ""

files_to_update:
  - "version.txt"
  - "README.md"
```

### Commit Parsing & Grouping

The action supports three intelligent parsing strategies to organize your changelogs and release notes effectively. Grouping is configured via the `commit_groups` section in your config file.

#### 1. Sectioned Changes (Type 3 - Highest Priority)
Best for large commits covering multiple areas. Use Markdown headers in your commit body.

**Commit Message:**
```text
feat: major overhaul of auth system

### ✨ Features
- Added OIDC provider support
- Implemented refresh token rotation

### 🐛 Bug Fixes
- Fixed race condition in login flow
- Resolved session timeout issue
```

**Result:**
- The bullet points under `### ✨ Features` will appear in the "Features" group.
- The bullet points under `### 🐛 Bug Fixes` will appear in the "Bug Fixes" group.

#### 2. Bullet Points (Type 2)
Great for listing multiple related changes without specific sections.

**Commit Message:**
```text
fix: update dependency handling

- Upgrade pydantic to v2
- Remove deprecated validation logic
- Fix circular import in config module
```

**Result:**
- Each bullet point is treated as an individual change.
- Each point is matched against your `auto_semver_config.yml` patterns independently.

#### 3. Header Only (Type 1 - Default)
Standard conventional commit format.

**Commit Message:**
```text
fix(api): handle missing auth header gracefully
```

**Result:**
- The entire header is matched against config patterns.
- Grouped based on the prefix (e.g., `fix:` goes to "Bug Fixes").

### Configuration Example

Define how regex patterns map to groups in `auto_semver_config.yml`:

```yaml
commit_groups:
  - title: "✨ Features"
    patterns:
      - "^feat:"
      - "^add:"
    priority: 1

  - title: "🐛 Bug Fixes"
    patterns:
      - "^fix:"
      - "^resolve:"
    priority: 2
```
