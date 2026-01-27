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
