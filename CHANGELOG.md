# Changelog
All notable changes to this project will be documented in this file.

## [0.5.2-dev] - 22-10-2025

### ✨ Features & Enhancements

**add standardized development workflow prompts**  
Development Infrastructure:
- Add commit.prompt.md for structured commit message generation
- Add create-pr.prompt.md for comprehensive PR creation
- Add new-branch.prompt.md for proper Git workflow
- Add instruction-improvement.prompt.md for iterative docs

Documentation Updates:
- Update copilot-instructions.md with modern tooling (uv, Python 3.13+)
- Add Git workflow and commit standards sections
- Include reusable development prompts guidelines
- Enhance AI usage guidelines for consistency

Benefits:
- Ensures consistent commit and PR formatting across team
- Improves onboarding for new contributors
- Aligns with auto-semver branch naming conventions
- Promotes modern Python development practices
**Add error handling for unconfigured target branches**  
- Log an error if the target branch is not found in suffixes
- Raise a ValueError to prevent further execution
**Add console script entry point for Docker**  
Package Distribution:
- Add console script 'auto-semver' in pyproject.toml
- Map to auto_semver.cli:main entry point
- Enable direct command execution without python -m

Docker Optimization:
- Update Dockerfile ENTRYPOINT to use 'auto-semver' directly
- Change from 'python -m auto_semver.cli' to 'auto-semver'
- Update PATH comment to reflect console script usage
- Maintain editable install with uv for development workflow

Benefits:
- Cleaner command-line interface for end users
- Standard Python packaging best practices
- Simplified Docker container execution
- Better integration with package managers
- Easier distribution and installation
**Enhance changelog template formatting**  
Core Changes:
- Improve changelog message formatting for clarity
- Add section headers for each message in the changelog

Benefits:
- Enhances readability of changelog entries
- Provides better structure for release notes
**Add comprehensive E2E and integration test suite**  
Test Infrastructure:
- Add modular fixtures for isolated testing (git_repo, github_api_mock, env_isolation, network_block)
- Create 17 comprehensive E2E/integration tests covering full release workflows
- Implement test_e2e_workflows.py with 6 workflow scenarios
- Implement test_action_integration.py with 5 GitHub Actions simulations
- Implement test_full_e2e.py with 6 complete release cycle tests

Template System Improvements:
- Extract shared template utilities to templates/utils.py
- Add comprehensive template function registry
- Implement custom Jinja2 filters for PR/changelog generation
- Add date formatting and commit grouping utilities

Pull Request Builder:
- Create new PR builder architecture (pr/builder.py)
- Implement GitHubPRBuilder with template rendering
- Add custom Jinja2 functions for PR title/body generation
- Support dynamic data injection for templates

Changelog Enhancements:
- Refactor ChangelogManager to use template engine
- Move changelog template logic to engine integration
- Add manager-engine integration tests

Testing Coverage:
- Add 173 lines of test improvements
- Add template engine integration tests
- Add GitHub PR builder tests with custom functions
- All 17 E2E/integration tests passing with full isolation

Configuration:
- Update pyproject.toml with new test dependencies
- Add responses library for API mocking
- Update uv.lock with new dependency tree

Isolation Guarantees:
- All tests use tmp_path for temporary git repos
- No real git repositories touched during testing
- All GitHub API calls mocked with responses
- Network access blocked via fixture
- Environment variables isolated per test
### ♻️ Refactoring & Code Quality

**modernize project infrastructure and add promotion workflow support**  
Modernize project infrastructure and add comprehensive tag promotion workflow support

### Major Infrastructure Changes:
- Upgrade Python runtime from 3.12 to 3.13 in Dockerfile and CI
- Migrate from pip/venv to uv for faster dependency management
- Replace requirements.txt files with pyproject.toml dependency groups
- Update CI workflow to use uv with caching and streamlined task execution
- Add .python-version file for consistent development environment

### Core Feature Addition:
- Implement tag promotion workflow for seamless version advancement between branches
- Add _detect_tag_source_branch() to identify version origins from suffixes
- Add _is_tag_promotion_scenario() to detect promotion vs. regular bump scenarios
- Update bump workflow to preserve version numbers during promotions (only change suffix)
- Add comprehensive test suite for promotion scenarios with mocking support

### Configuration Improvements:
- Rename 'files_to_update' to 'version_files' for clarity
- Update GitHub Copilot instructions with project-specific guidelines
- Add development rules for consistent coding standards across team
- Enhance project documentation with feature details and tooling info

### Development Experience:
- Add format task to Taskfile.yml for code consistency
- Improve test configuration with better error reporting (--tb=short)
- Add pre-commit hooks configuration
- Update pytest configuration with enhanced coverage settings

### Error Handling & Reliability:
- Add proper exception handling in CLI main function
- Improve logging and debugging capabilities
- Add missing import statements for logging and sys modules
- Update mock configurations in tests to handle promotion logic

This modernization maintains backward compatibility while adding powerful
tag promotion capabilities and significantly improving the development
experience with modern Python tooling.
**Clean test output and add comprehensive Docker integration tests**  
- Fix pytest log level from DEBUG to INFO to suppress noisy third-party logs
- Improve logger tests to use NullHandler for clean test execution
- Add comprehensive Docker integration tests with build validation
- Enhance Docker image with git installation and PATH configuration
- Add Docker SDK and type stubs to development dependencies
- Update Taskfile pytest configuration for cleaner output
- Improve CI prompt tools configuration

Fixes verbose Docker SDK debug logs during test execution while maintaining
full test coverage and validation. All 281 tests pass with 89.61% coverage.
**Refactor Docker tests for improved type safety**  
Core Changes:
- Update type hints for Docker client and image in tests
- Replace generic types with specific Docker types for clarity
- Ensure consistent usage of Docker client methods

Testing Improvements:
- Enhance test readability and maintainability
- Facilitate better integration with type checkers
**Refactor Dockerfile and update test cases for user permissions**  
**Dockerfile Changes:**
- Simplify environment variable setup
- Ensure container runs as root user for GitHub Actions compatibility

**Test Updates:**
- Modify tests to reflect root user requirements
- Enhance clarity in test descriptions for permission errors
- Add new test for git safe directory configuration with root user

Additional Notes:
- Aligns Docker setup with GitHub Actions requirements
- Improves test reliability and clarity for future maintainers
**Refactor git repository initialization in tests**  
Core Changes:
- Replace manual git repository setup with `Repo.init()`
- Add initial commit with a dummy file for valid repository state

Testing:
- Ensure that the test for git safe directory configuration works with the new setup
- Improve reliability of tests by using a proper Git repository structure
**Refine GitHub Copilot PR prompt templates for better user experience**  
Documentation Updates:
- Reorganize PR template sections into required vs optional categories
- Add section relevance guidelines to prevent irrelevant template sections
- Emphasize markdown file workflow for better content iteration
- Include user feedback handling instructions for prompt improvement

Template Improvements:
- Streamline create-pr.prompt.md with clearer section organization
- Enhance update-pr.prompt.md with better iteration workflows
- Remove auto-semver impact sections from generic templates
- Add specific guidance for removing non-applicable sections

User Experience:
- Provide clear guidelines on when to include/exclude template sections
- Add feedback response patterns for better prompt adaptation
- Emphasize flexibility over rigid template following
- Improve markdown file creation and iteration processes

Additional Notes:
- Changes maintain existing functionality while improving usability
- Templates now better adapt to actual change scenarios
- Reduces noise in PR descriptions by removing irrelevant sections
- Supports better collaboration through clearer prompt instructions
**Refactor pull request template for clarity**  
Core Changes:
- Improve formatting of the changes section in the pull request template
- Enhance readability by using headings for each change

Impact:
- Provides clearer structure for release notes
- Facilitates better understanding of changes for reviewers
**Refactor configuration system with centralized template engine**  
Architecture Changes:
- Split monolithic config/data.py into focused model modules
- Create centralized Jinja2 template engine with pluggable functions
- Implement automatic template function registration per config model
- Add typed template variable dataclasses for type safety

Configuration Models:
- Extract ChangelogConfig to _models/_changelog.py with auto-registration
- Extract PullRequestConfig to _models/_pull_request.py with domain functions
- Extract CommitGroupConfig to _models/_commit_group.py with grouping logic
- Create unified ConfigData model in _models/_config.py
- Add PromotionRule model for branch promotion validation

Template Engine Implementation:
- Global template engine singleton with function registration
- Domain-specific function sets (changelog, PR, commit grouping)
- Built-in template validation using registered functions
- Extensible function and filter registration system
- Template variable type safety with dataclass structures

Testing Infrastructure:
- Add comprehensive test suite for template function registration
- Add template validation and rendering tests
- Add config model interaction and conflict resolution tests
- Add test fixtures for changelog and config scenarios
- Add engine reset functionality for test isolation

Breaking Changes:
- Rename config/loader.py to config/config.py for clarity
- Remove config/data.py (functionality moved to _models/)
- Template functions now auto-register on model instantiation
- Configuration validation now uses centralized template engine
### 🔧 Infrastructure & Tooling

**Update Dockerfile to use optimized base image**  
Core Changes:
- Switch from python:3.13-slim to ghcr.io/astral-sh/uv:0.7.20-python3.13-alpine
- Remove unnecessary system dependency installations
- Streamline user and group creation for better security

Benefits:
- Reduced image size and improved build performance
- Enhanced security by minimizing installed packages
**Install dependencies in Dockerfile for application setup**  
Core Changes:
- Add `uv pip install --no-deps -e .` to install application dependencies
- Ensure proper ownership of the working directory after installation

Benefits:
- Streamlines the Docker image build process
- Ensures all necessary dependencies are available for the application
**Update commit and PR prompts for clarity and consistency**  
[Commit Prompt Changes]:
- Modify tools list to include 'runCommands' and 'terminalLastCommand'
- Revise commit message generation guidelines to emphasize descriptive titles without conventional prefixes

[PR Prompt Changes]:
- Update tools list to remove 'openSimpleBrowser'
- Simplify PR title format to focus on descriptive language only

Additional Notes:
- Enhances clarity for contributors on commit and PR creation processes
- Aligns with auto-semver best practices for better version management
**Switch Docker installation to system-wide package**  
Build Process:
- Change from uv sync to uv build for proper wheel creation
- Install package system-wide using pip install dist/*.whl
- Add README.md to build context for proper package metadata

Environment:
- Remove virtual environment PATH manipulation
- Simplify container setup by using system Python directly
- Eliminate need for .venv directory in production container

Benefits:
- Cleaner production container without virtual environment overhead
- More reliable package installation for GitHub Actions usage
- Better alignment with Docker best practices for single-purpose containers
**Use repository-level git safe directory configuration**  
Implementation Changes:
- Change git safe directory config from global to repository level in GitOps
- Add try-catch block for OSError and PermissionError handling
- Raise RuntimeError with descriptive message on configuration failures
- Update docstring to reflect repository-level config scope

Testing Updates:
- Update test assertions to expect repository-level config calls
- Add new test case for permission error handling scenarios
- Verify proper RuntimeError is raised with expected error message

Benefits:
- Resolves Docker permission issues where global config is not writable
- Provides same functionality without requiring elevated privileges
- Repository-scoped configuration is more appropriate for CI environments
- Better error handling provides clearer debugging information

Additional Notes:
- Repository-level config provides equivalent security for CI environments
- Change maintains backward compatibility for existing functionality
- Error messages help diagnose configuration issues in containerized environments
### 🐛 Bug Fixes & Resolutions

**Resolve Git safe directory configuration in CI environments**  
Security Improvements:
- Change GitOps safe directory config from repository to global level
- Avoid permission errors when accessing repository-level config
- Ensure proper Git security in containerized CI environments

Implementation Details:
- Update GitOps.__ensure_git_safe_directory() method
- Change config_level from "repository" to "global" in config_writer
- Global config avoids write permission issues in restricted CI contexts

Testing Updates:
- Update test_init_with_ensure_safe() to expect global config calls
- Update test_init_with_ensure_safe_permission_error() assertions
- Maintain test coverage for permission error handling

Infrastructure Impact:
- Improves reliability in Docker-based GitHub Actions
- Reduces CI failures related to Git security policies
- Maintains backwards compatibility with existing workflows

Additional Notes:
- Addresses Git security restrictions in CI environments
- Global config scope is appropriate for safe directory settings
- No functional changes to core auto-semver logic
### 📝 Other Changes

- 
**Align PR template to commit_groups**  
Templates:

- Update pull_request.body to iterate commit_groups

- Keep changelog template compatible (legacy alias supported)

Testing:

- Add PR builder test to validate commit_groups rendering

Behavior:

- Rely on config variable names; no code aliases required

## License
This project is licensed under the MIT License.