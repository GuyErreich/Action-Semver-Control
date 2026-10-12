# Changelog
All notable changes to this project will be documented in this file.

## [1.8.13-dev] - 12-10-2026

### ⚠️ Deprecations
- `grouped_messages` in changelog and pull request templates; use `commit_groups`. Removed in 2.0 (#233)
- `commit_groups` as a YAML list; use a mapping with `groups`. Removed in 2.0 (#233)
- setup `--app-id`; use `--client-id`. Removed in 2.0 (#233)

### ♻️ Refactoring & Code Quality
- extract runview reporting package (#318)

### 🔧 Infrastructure & Tooling
- annotate when Python CI runs or skips (#356)

## License
This project is licensed under the GPL-3.0-or-later License.