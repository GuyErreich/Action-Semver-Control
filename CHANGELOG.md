# Changelog
All notable changes to this project will be documented in this file.

## [0.7.0-dev] - 06-11-2025

### ✨ Features & Enhancements
- Add auto_promote() method to GitOps for SCM-agnostic promotions
- Add fetch() method for remote synchronization
- Add checkout() method with branch creation support
- Add pull() method for updating local branches
- Add merge() method with conflict detection and abort logic
- Add mock for get_auto_promotion_targets() in unit tests
### ♻️ Refactoring & Code Quality
- Refactor auto_promote() to use GitOps helper methods
### 🔧 Infrastructure & Tooling
- Update integration tests to expect auto_promote() calls
### 📝 Other Changes
- Release 0.6.0-dev
- fetch, checkout, pull, merge, tag, push
- Replace PR-based promotion with direct branch merging
- Remove GitHub token requirement for auto-promotion
- Eliminate PR creation in favor of direct merges
- Maintain SCM-agnostic approach using GitPython
- Preserve merge commit history with --no-ff strategy
- Mock new GitOps methods (fetch, checkout, pull, merge)
- Remove PR-based test assertions
- Truly automatic promotion without manual PR merges
- Works with any Git remote (GitHub, GitLab, Bitbucket)
- Cleaner GitOps abstraction with reusable methods
- Better error handling for merge conflicts
- Faster promotion cycle in CI/CD pipelines
- Auto-promotion no longer creates PRs (uses direct merge)
- GitHub token optional for auto-promotion workflow
- Existing auto-promotion PRs won't be closed automatically

## License
This project is licensed under the MIT License.