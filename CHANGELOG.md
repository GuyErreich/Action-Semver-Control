# Changelog
All notable changes to this project will be documented in this file.

## [0.7.1-dev] - 15-11-2025

### 🔧 Infrastructure & Tooling
- Update tools list to include specific GitHub Copilot tools
### 📝 Other Changes
- Release 0.7.0-dev
- Renamed ensure_git_identity() to __ensure_git_identity() (private method)
- Git identity now configured automatically in __init__() method
- Removed explicit call from auto_promote() method
- Git identity configured once during GitOps initialization
- Cleaner architecture with proper encapsulation
- Required for merge operations in CI/CD environments like GitHub Actions
- Prevents merge failures due to missing committer identity
- Added comprehensive python.instructions.md for project standards
- Includes auto-semver architecture, testing patterns, and AI guidelines
- Documents Git workflow and branch management conventions
- **
- Change temporary markdown file path from `/tmp/pr-body.md` to `./pr-body.md`
- Ensure all references to markdown file paths are consistent
- Clarify usage of markdown files for PR content creation
- Improve instructions for creating and iterating on PR content

## License
This project is licensed under the MIT License.