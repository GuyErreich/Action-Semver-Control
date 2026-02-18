# Changelog
All notable changes to this project will be documented in this file.

## [1.3.14-dev] - 18-02-2026

### ✨ Features & Enhancements
- Add logic to parse `CHANGELOG.md` starting from the version header until the license section.
### 🔧 Infrastructure & Tooling
- Update `.github/actions/gh-release/action.yml` to extract release notes from `CHANGELOG.md`.
- Remove unreliable git tag comparison logic for finding the previous tag. ### [Dependencies]:
- Update `uv.lock` to reflect latest dependency versions. ## 🧪 Testing
### 📝 Other Changes
- Fallback to GitHub auto-generated notes only if `CHANGELOG.md` is missing.
- [x] Manual verification of `sed` command for changelog extraction.
- [x] Verified `action.yml` syntax logic. ## 🔧 Technical Details ### Architecture Changes:
- The release workflow now prioritizes the project's curated `CHANGELOG.md` over automated git-diff based notes.
- This ensures that pre-release versions (like `-rc` or `-dev`) get accurate release notes even if git tags are not strictly sequential in a linear history.

## License
This project is licensed under the MIT License.