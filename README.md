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

## Configuration (`auto_semver_config.yml`)

```yaml
start_version: "0.1.0"

suffixes:
  dev: "-dev"
  staging: "-rc"
  main: ""

branch_strategy: "single"  # "single" or "multi"

files_to_update:
  - "version.txt"
  - "README.md"
