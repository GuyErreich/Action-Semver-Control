# Changelog
All notable changes to this project will be documented in this file.

## [0.6.0-dev] - 31-10-2025

### ✨ Features & Enhancements
- Add auto-promotion detection and PR creation in finalize workflow
- Add find_promotion_rule(), validate_promotion(), and get_auto_promotion_targets()
- Add promote.yml GitHub Actions workflow for manual promotions
- Add comprehensive integration tests for auto-promotion scenarios
- Add test fixtures for promotion workflow scenarios
- Add promotion rules to auto_semver_config.yml
### 🔧 Infrastructure & Tooling
- Use eager initialization pattern with _parse_repository_name()
- Update ci.yml to support promotion branch detection
- Update all promotion tests to use ConfigData instance methods
### 📝 Other Changes
- Release 0.5.5-dev
- Implement promote CLI command for manual version promotions
- Extend ConfigData model with promotion validation methods
- Cache repository name on GitOps initialization for better performance
- Remove redundant repo_full_name parameters from create_pr() and close_old_release_prs()
- Configure workflow permissions for PR creation
- Fix FileHelper to create YAML lock files (not JSON) for pyfakefs compatibility
- Ensure tests don't touch real .semver.lock file
- Support auto_promote flag for automatic promotion triggers
- Enable chained promotions (dev → staging → main)
- Promotion logic moved from utils to ConfigData model for better encapsulation
- Tests now properly use pyfakefs for all file operations

## License
This project is licensed under the MIT License.