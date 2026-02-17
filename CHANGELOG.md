# Changelog
All notable changes to this project will be documented in this file.

## [1.3.13-dev] - 17-02-2026

### ✨ Features & Enhancements
- Add regression test `test_parse_multiline_bullets` for simple multiline lists.
- Add regression test `test_parse_multiline_groups_complex` for complex sectioned lists with multiline items.
### ♻️ Refactoring & Code Quality
- Ensured the token comes from the `app-authentication` step (`steps.app-token.outputs.token`). ## 🔧 Technical Details ### Architecture Changes:
- Ensure full commit message context is preserved for both simple lists and sectioned groups. ### Testing:
### 🔧 Infrastructure & Tooling
- Updated `.github/workflows/publish-staging.yml` to explicitly pass `github_token` input to `gh-release` action.
- Updated `.github/workflows/publish-production.yml` to explicitly pass `github_token` input to `gh-release` action.
- Update parsing logic to append subsequent indented or text lines to the previous bullet point instead of ignoring them.
- Updated `tests/auto_semver/git/test_parser.py` with new test cases. ## 📚 Documentation
### 🐛 Bug Fixes & Resolutions
- Resolve issue in `CommitParser` where only the first line of a multiline bullet point was captured.
### 📝 Other Changes
- Validated `gh-release` permissions failure in CI logs (403 Forbidden).
- The `gh-release` composite action requires a token with write permissions to create releases.
- Previously, it might have been falling back to default `GITHUB_TOKEN` or failing if no token was provided, resulting in 403.
- By passing the installation token from the GitHub App authentication step, we ensure correct permissions. ### Code Diffs (for significant changes): ```diff
- name: GH Release uses: ./.github/actions/gh-release +       with: +         github_token: ${{ steps.app-token.outputs.token }} ```
- Verify existing tests pass with no regressions. ## 🧪 Testing
- [x] Regression tests added for multiline bullet points
- [x] Existing functionality verified unaffected
- [x] Edge cases for indented lines covered ## 🔧 Technical Details ### Code Diffs:
- Modified `src/auto_semver/git/parser.py` to handle continuation lines.
- [x] Code comments updated to explain continuation line logic. ## ✅ Checklist
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch

## License
This project is licensed under the MIT License.