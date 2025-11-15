# Changelog
All notable changes to this project will be documented in this file.

## [0.7.2-dev] - 15-11-2025

### 🔧 Infrastructure & Tooling
- -rc)
### 📝 Other Changes
- Release 0.7.1-dev
- Transform source version to target branch suffix in finalize
- Create tag on target branch using transformed version
- Remove redundant tag-exists handling in auto_promote (unique tags)
- Prevents 'tag already exists' errors
- Ensures correct, branch-specific tag names during promotion
- No public API changes; logic isolated to finalize/ops
- Compatible with existing suffix configuration mapping

## License
This project is licensed under the MIT License.