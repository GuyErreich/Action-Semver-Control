# Changelog
All notable changes to this project will be documented in this file.

## [1.3.8-dev] - 28-01-2026

### ✨ Features & Enhancements
- Add `.wtp.yml` configuration file.
- Add `.github/actions/app-authentication` composite action to
- Add proper validation for various URL formats
- Add comprehensive test suite
- Implement `promote` functionality foundation in the CLI and git
- Enhanced git operations to support tag promotion logic.
- Better reliability and security by using GitHub App tokens with
- Enhances commit consistency across different environments
- Improves traceability of commit authorship
- Improves accuracy in version detection for releases
- Improves clarity in release process by distinguishing between release
- Add new patterns for features and enhancements
- Improves accuracy of changelog generation
- Enhances clarity and organization of commit messages
- Add unit tests for push failure scenarios
- false' to promote workflowto make we use the
### ♻️ Refactoring & Code Quality
- Refactor the release publishing logic from the workflow file into a
- Extracted release logic into a composite action to separate concerns
- Centralized authentication logic in a reusable composite action.
- Explicitly set author and committer using GitPython's Actor
- Simplifies the workflow for versioned releases
- Aligns with semantic versioning best practices
- Refactor bump.py to remove branch strategy logic
- Simplifies the configuration and logic for version bumping
### 🔧 Infrastructure & Tooling
- Update `.github/workflows/publish-release.yml` to utilize the new
- Update `Taskfile.yml` to include new tasks.
- Update `.vscode/settings.json`.
- Update `auto-semver.yml` and `promote.yml` to use the new
- Update project dependencies in `uv.lock`.
- Update regex pattern in `src/auto_semver/git/ops.py` to handle
- Update tag patterns to support semantic versioning formats
- Update documentation patterns for better matching
- Update tests to reflect removal of branch strategy
- Update push method to handle multiple PushInfo results
### 🐛 Bug Fixes & Resolutions
- Resolve issue where HTTPS URLs with credentials (e.g.,
### 📝 Other Changes
- ** 1.3.7-dev
- ** 28-01-2026
- [x] Unit tests added/updated
- Minor - new feature logic added.
- `feature/support-tag-promotion`
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [ ] Documentation updated
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch
- Migrate from `secrets.GH_TOKEN`/`GITHUB_TOKEN` to a dedicated GitHub
- Consistent git author identity for automated commits (using the App's
- [x] Infrastructure changes tested
- [x] Compatibility verified
- Describe only the changes that are already committed and
- Verify support for SSH, clean HTTPS, and authenticated HTTPS URLs
- Cover edge cases including invalid/non-GitHub URLs
- [x] Unit tests added/updated
- [x] Integration tests pass
- [ ] Manual testing completed
- [x] Edge cases covered
- \.git)?$",  # HTTPS format
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
- Prevent "GitHub" as committer by using user config values
- Remove specific branch restrictions for tag pushes
- Allows for more flexible tagging and release management
- Replace installation ID with app ID in app authentication step
- Ensures correct authentication for GitHub App usage
- Modify tag patterns to use semantic versioning format
- Ensure compatibility with release triggers for versioning
- Modify tag detection logic to identify pre-release tags
- Adjust conditions for setting release flags based on tag type
- Ensures correct handling of release types for staging and production
- Include additional patterns for code refactoring
- Expand testing patterns to cover unit and integration tests
- Introduce ignore patterns for release commits and version numbers
- Ensure ignored commits do not appear in changelog
- Eliminate branch strategy configuration from README and config files
- Ensures consistent behavior without branch strategy variations
- Log detailed error messages for different push failure scenarios
- Raise RuntimeError with specific messages for rejected and error flags
- Mock Git repository and PushInfo for reliable testing
- Change publish-release trigger from tag push to deployment for

## License
This project is licensed under the MIT License.