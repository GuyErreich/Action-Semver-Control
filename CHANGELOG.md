# Changelog
All notable changes to this project will be documented in this file.

## [1.2.0-dev] - 06-12-2025

### ✨ Features & Enhancements
- Enhance promote command in main.py to handle new arguments
- Enhance argument parsing for manual promotion
- Add command handling for from-branch and to-branch options
### 🔧 Infrastructure & Tooling
- Update promote command to support dry run validation
- Update main.py to support promote subcommand
### 📝 Other Changes
- Release 1.1.1-dev
- Simplify promotion validation logic in promote.py
- Modify promote.yml to utilize new promote command structure
- Ensure proper handling of GitHub token and branch inputs
- Improve logging for better debugging during promotion process
- Bump auto-semver version to 1.1.0.dev0 in uv.lock
- Remove steps for stashing and restoring changes
- Simplify workflow by focusing on creating a new feature branch
- Emphasize using descriptive branch names following auto-semver conventions
- Streamlines the process for creating new branches
- Reduces complexity for users by eliminating unnecessary steps
- Establish fail fast strategy for input validation
- Define logging practices with severity levels
- Outline error handling best practices
- Specify documentation standards in Google style
- Emphasize strict typing and test coverage requirements
- Include guidelines for function signatures and type safety
- Ensure alignment with project best practices
- Introduce CLI usage section in README
- Detail manual promotion command with examples
- Include options for dry-run validation
- Adjust test_main.py to accommodate new command structure
- Ensure proper argument handling in tests

## License
This project is licensed under the MIT License.