# Changelog
All notable changes to this project will be documented in this file.

## [1.3.10-dev] - 10-02-2026

### ✨ Features & Enhancements
- Added a safe fallback to "Release " prefix if the configuration fails
- Enhanced `get_static_prefix` in `src/auto_semver/templates/engine.py`
- Implement `CommitParser` to support varied commit message styles
- Add `match_groups` support for explicit section matching
- Add examples for header-only, bullet-point, and sectioned styles
- Add comprehensive tests for `CommitParser` and `CommitGrouper`
### 🔧 Infrastructure & Tooling
- Updated `_filter_release_commits` logic in
- Update existing tests to align with new architecture
### ⚡ Performance
- Optimize imports and type hints across git operations
### 📝 Other Changes
- Remove redundant checkout step from GH Release action
- Create new publish-production.yml workflow for production releases
- Create new publish-staging.yml workflow for staging releases
- Delete outdated publish-release.yml workflow
- Streamlines release process by consolidating workflows
- Improves clarity and maintainability of release configurations
- Changed log levels from DEBUG to WARNING for cases where configuration
- [x] Unit tests added:
- [x] Existing tests updated:
- [x] Validated that mocks correctly simulate `GitOps` remote URL
- Related to: Changelog noise reduction
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [x] Documentation updated (code comments)
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch
- Extract commit grouping logic into dedicated `CommitGrouper` class
- Decouple parsing logic from configuration models
- Expand default regex patterns for better categorization
- Document supported commit parsing strategies in README

## License
This project is licensed under the MIT License.