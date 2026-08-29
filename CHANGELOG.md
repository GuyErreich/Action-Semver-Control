# Changelog
All notable changes to this project will be documented in this file.

## [1.4.0-dev] - 29-08-2026

### 🐛 Bug Fixes & Resolutions
- Implement `update_version_in_header` in `ChangelogManager` to rewrite version strings in `CHANGELOG.md`.
- Add `post_merge_hook` argument to `GitOps.auto_promote` to support custom logic (like file updates) after merge but before commit.
- Wire up `promote` and `finalize` CLI commands to trigger the changelog update during promotion.
- Ensure `chore: update version metadata` commit is created if the changelog is modified.
- **Parser Logic**: Added pre-processing step to split lines containing embedded headers (like `...text
### 🧪 Testing
- Update `test_promote.py` to verify `auto_promote` calls include the new hook argument.
- Verify `GitOps.auto_promote` correctly handles the `post_merge_hook` execution and subsequent commit.
- Verified that headers like `## 🧪 Testing` are now correctly identified as new sections.
- Confirmed that previous parsing logic (standard `Header:` format) remains supported.
### 📝 Other Changes
- [x] Regression tests added for `promote` CLI command.
- [x] Verified `auto_promote` correctly commits the changelog change.
- [x] Existing functionality verified unaffected.
- `GitOps.auto_promote` now accepts a callable `post_merge_hook` that receives `source_version` and `target_version`.
- This hook allows for modification of files (like `CHANGELOG.md`) within the merge transaction context before the final release tag is created.
- [x] Code comments updated for new methods.
- [x] Code follows project style guidelines
- [x] Self-review completed
- [x] Tests added and passing
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch
- **Regex Update**: Updated `_SECTION_HEADER_PATTERN` to support markdown-style headers (starting with `#`) without requiring a trailing colon.
- **Structure Extraction**: Improved the main loop in `_extract_structure` to correctly switch context when encountering a structural header.
- [x] Regression tests passed.
- [x] Verified fix against the reported issue case.
- [x] Existing functionality verified unaffected.
- Introduced `_EMBEDDED_HEADER_SPLIT` regex to handle inline header definitions.
- Modified `_SECTION_HEADER_PATTERN` to be more permissible with markdown syntax while maintaining strictness for legacy formats.
- Add optional `signed-commits` input (default `false`) to create verified commits via the GitHub Git Data and merge APIs.
- Release bumps, auto-promotions, and tags use server-side commits when enabled so repos with `required_signatures` rulesets stay unblocked.
- Keeps the existing local GitPython path when `signed-commits` is false.
- [x] `uv run ruff check src tests`
- [x] `uv run pytest` (382 passed)
- [ ] Merge to `dev`, promote through `staging` → `master`, re-pin `GuyErreich/AI_Agents` to the production tag SHA --------- Co-authored-by: Cursor <cursoragent@cursor.com>
- Add reusable `semver-bump` and `semver-promote` workflows so consumers only need thin caller workflows pinned at `@v1`
- Add `preflight-app-secrets` composite action that fails fast with a setup link when `GH_APP_ID` / `GH_APP_PRIVATE_KEY` are missing
- Add `auto-semver setup` CLI, prefilled GitHub App registration URLs, and prefilled “add workflow” deep links
- Document end-to-end adoption in `docs/SETUP.md`, add README Quickstart, Marketplace branding, and floating `v1` tag on production releases
- [x] `uv run pytest` — 411 passed
- [x] `uv run auto-semver setup --dry-run --skip-secrets --skip-scaffold` against scratch repo coords
- [x] `python scripts/generate_onboarding_links.py --owner GuyErreich --repo Action-Semver-Control --branch dev`
- [ ] CI green on this PR
- [ ] After merge + first production release: confirm `v1` tag exists and Marketplace listing can be published from that release Made with [Cursor](https://cursor.com) --------- Co-authored-by: Cursor <cursoragent@cursor.com>

## License
This project is licensed under the MIT License.