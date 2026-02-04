# Changelog
All notable changes to this project will be documented in this file.

## [1.3.10-dev] - 04-02-2026

### ✨ Features & Enhancements
- Improves clarity and maintainability of release configurations
- Enhanced `get_static_prefix` in `src/auto_semver/templates/engine.py`
### 📝 Other Changes
- Remove redundant checkout step from GH Release action
- Create new publish-production.yml workflow for production releases
- Create new publish-staging.yml workflow for staging releases
- Delete outdated publish-release.yml workflow
- Streamlines release process by consolidating workflows
- Describe only the changes that are already committed and
- Updated `_filter_release_commits` logic in
- Added a safe fallback to "Release " prefix if the configuration fails
- Changed log levels from DEBUG to WARNING for cases where configuration
- [x] Unit tests added:
- [x] Existing tests updated:
- [x] Validated that mocks correctly simulate `GitOps` remote URL
- Changelog noise reduction
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [x] Documentation updated (code comments)
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch

## License
This project is licensed under the MIT License.