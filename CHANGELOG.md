# Changelog
All notable changes to this project will be documented in this file.

## [1.3.1-dev] - 24-01-2026

### ✨ Features & Enhancements
- Add `.wtp.yml` configuration file.
- Add `.github/actions/app-authentication` composite action to
- Add proper validation for various URL formats
- Add comprehensive test suite
### ♻️ Refactoring & Code Quality
- Refactor the release publishing logic from the workflow file into a
### 🔧 Infrastructure & Tooling
- Update `.github/workflows/publish-release.yml` to utilize the new
- Update `Taskfile.yml` to include new tasks.
- Update `.vscode/settings.json`.
- Update `auto-semver.yml` and `promote.yml` to use the new
- Update project dependencies in `uv.lock`.
- Update regex pattern in `src/auto_semver/git/ops.py` to handle
### 🐛 Bug Fixes & Resolutions
- Resolve issue where HTTPS URLs with credentials (e.g.,
### 📝 Other Changes
- ** 1.3.0-dev
- ** 24-01-2026
- Release 1.2.5-dev
- Implement `promote` functionality foundation in the CLI and git
- [x] Unit tests added/updated
- Extracted release logic into a composite action to separate concerns
- Enhanced git operations to support tag promotion logic.
- Minor - new feature logic added.
- `feature/support-tag-promotion`
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [ ] Documentation updated
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch
- Migrate from `secrets.GH_TOKEN`/`GITHUB_TOKEN` to a dedicated GitHub
- Better reliability and security by using GitHub App tokens with
- Consistent git author identity for automated commits (using the App's
- Centralized authentication logic in a reusable composite action.
- [x] Infrastructure changes tested
- [x] Compatibility verified
- Describe only the changes that are already committed and
- Verify support for SSH, clean HTTPS, and authenticated HTTPS URLs
- Cover edge cases including invalid/non-GitHub URLs
- [x] Unit tests added/updated
- [x] Integration tests pass
- [ ] Manual testing completed
- [x] Edge cases covered
- //github\.com/([^/]+)/(.+?)(?:\.git)?$",  # HTTPS format
- [x] Code comments and docstrings updated
- [ ] README updated if needed
- [ ] API documentation updated
- # (no issue linked in context)
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [x] Documentation updated
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch

## License
This project is licensed under the MIT License.