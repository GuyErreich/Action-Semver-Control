> 🧭 This project is an **auto-semver GitHub Action** that automates semantic versioning, changelog management, and pull request creation. It follows strict conventions for Python 3.12+, modern tooling (uv for dependency management), full test coverage, CI-enforced validation, and clean architecture. These guidelines apply to **all contributors and tools**, including GitHub Copilot.

---

## 🎯 Project Overview
This is a **GitHub Action** written in Python that:
- Automatically bumps semantic versions based on branch naming conventions
- Updates version files (`version.txt`, `README.md`, etc.)
- Manages changelogs with Jinja2 templates
- Creates and manages release branches and pull requests
- Handles Git operations via GitPython and GitHub API operations via PyGithub
- Supports multiple branch strategies (`single` vs `multi` release workflows)
- Uses semver lockfiles (`.semver.lock`) to track release state

### 🏗️ Core Architecture

The tool operates in two primary modes:
- **Bump mode**: Creates version bumps on PR merge, applies suffixes based on target branch
- **Finalize mode**: Promotes versions between branches (removes/changes suffixes)

Core modules follow strict domain separation:
- **`auto_semver.cli`**: Command-line interface with `bump` and `finalize` workflows
- **`auto_semver.git.ops`**: GitPython wrapper for branch operations, commits, and pushes
- **`auto_semver.gh.event`**: GitHub Actions event parsing and context extraction
- **`auto_semver.semver`**: Version parsing, bumping, and file updating logic
- **`auto_semver.changelog`**: Changelog generation with Jinja2 templates
- **`auto_semver.config`**: Pydantic-based YAML configuration with Jinja2 template validation

---

### ✅ General Development
- Use **Python 3.13+** with modern language features.
- Use **uv** for dependency management instead of pip for faster, more reliable builds.
- Prefer built-in `types` (`list`, `dict`, `tuple`, etc.) over legacy `typing.List`, etc.
- Write clean, maintainable, and modular code.
- Apply **Google-style docstrings** for all functions, classes, and modules.
- Use `dataclass` for simple structured data.
- Use **Pydantic v2+** when validation, serialization, or parsing is required.
- Always include **explicit type annotations**.
- For CLI tools:
  - Use `argparse` or `typer` depending on complexity.
  - Use `if __name__ == "__main__"` guard in scripts.

### 🧭 Imports & Structure
- Prefer **explicit relative imports** (e.g. `from ..core.utils import MyFunc`) within internal modules.
- Avoid **implicit absolute imports** (e.g. `import core.utils`) inside your own package — these break under CLI/test contexts and are flagged by tools like `ruff`.
- All imports must work from:
  - IDE (e.g. VS Code, PyCharm)
  - CLI scripts (e.g. `python scripts/do_something.py`)
  - `pytest` (without needing `PYTHONPATH`)
  - CI/CD runners
- Group and sort imports: 
  - 1. Standard library
  - 2. Third-party
  - 3. Internal
- Use `isort` if manual sorting is needed (optional if `ruff` handles it).
- Avoid exposing internals via `__init__.py`.
- Use `__all__` to define public interfaces in shared modules.

---

### 🔍 Testing
- Use **`pytest` and `pytest-mock`** only.  
- Do **not** use `unittest.mock`.
- Use shared fixtures like `GitHubEventFixture`, `FileFixture`, etc. from `tests/fixtures/`.
- Prefer realistic tests using **real files** or `tmp_path` over excessive mocking.
- Reuse and compose fixtures. Avoid copy-pasting boilerplate test setup.
- Follow existing test file patterns.
- Prefer `pyfakefs` for file-related test cases instead of creating actual temporary files.
- Use `fs` fixture from `pyfakefs` to mock the file system when testing file-related logic.
- **Project-specific testing patterns:**
  - Mock `GitPython` operations for Git-related tests using `pytest-mock`
  - Use `GitHubEventFixture` for simulating GitHub Actions event payloads
  - Test version parsing with edge cases (quotes, prefixes, suffixes)
  - Validate Jinja2 template rendering in configuration tests
  - Test both `single` and `multi` branch strategies in workflow tests

---

### 🛠 Validation and CI
Every change **must pass** the following checks:
- ✅ Unit tests (`pytest`)
- ✅ Type checking (`mypy`)
- ✅ Linting (`ruff`)
- ✅ Formatting (`ruff format`)  
  (💡 Do not use `black`; `ruff format` replaces it.)

Validation must be automated:
- Use the `Taskfile.yml` for all developer tasks (`task test`, `task lint`, etc.).
- CI must enforce test and formatting rules.
- Keep utility scripts in `scripts/` and document them clearly.

### 🔀 Git Workflow and Branch Management
- **Always follow proper Git workflow**: stash → checkout dev → pull → create branch → pop stash → commit → push
- **Never switch branches with uncommitted changes** - use `git stash` to preserve work
- **Use conventional branch naming** that aligns with auto-semver detection:
  - `breaking/` or `major/` for breaking changes (major bump)
  - `feature/` for new features (minor bump)
  - `fix/`, `bug/`, `hotfix/`, `chore/`, `devops/` for fixes and maintenance (patch bump)
  - Other prefixes (`docs/`, `refactor/`, `style/`, `test/`, `ci/`) default to patch bump
- **Use descriptive branch names** in kebab-case: `feature/tag-promotion-workflow`
- **Create feature branches from latest dev/main** to avoid conflicts
- **Push with upstream tracking** using `-u` flag on first push

### 📝 Commit Standards and Messaging
- **Follow conventional commits** format: `<description>`
- **Write structured commit messages** for complex changes:
  - Clear, imperative title under 50 characters
  - Organized body with categories and bullet points
  - Explain what, why, and impact
  - Include breaking changes and migration notes when applicable
- **Use reusable commit and branch prompts** from `.github/copilot/prompts/`
- **Keep commits atomic** - one logical change per commit
- **Include context for future maintainers** in commit bodies

---

### 📋 Project-Specific Guidelines

#### 🔄 Semantic Versioning Logic
- Use `Version.parse()` to handle complex version formats with prefixes, suffixes, and quotes
- Version bumping follows branch naming conventions:
  - `major/*`, `breaking/*` → major bump
  - `feature/*` → minor bump  
  - `fix/*`, `bug/*`, `hotfix/*`, `chore/*`, `devops/*` → patch bump
- Preserve original formatting when updating version files (titles, quotes, prefixes)
- Support tag promotion scenarios where versions are promoted between branches without bumping
- Tag promotion logic detects source branch from version suffixes and preserves version numbers

#### 🌿 Git Operations Safety & Patterns
- Use `GitOps` class for all Git operations - never call git commands directly
- Always use `GitOps(ensure_safe=True)` in CI environments - marks repo as safe in Git config to avoid permission issues
- Always use lockfiles (`.semver.lock`) to track release state and prevent version regressions
- Support both `single` and `multi` branch strategies for different workflow types
- Handle GitHub API operations through `GitOps._get_github_repo()` method
- `SemverLock` class prevents race conditions by checking for existing release branches

#### 📝 Configuration Management
- All behavior is controlled by `auto_semver_config.yml` with configuration-driven patterns:
  ```yaml
  suffixes:
    dev: "-dev"      # Development releases
    staging: "-rc"   # Release candidates  
    master: ""       # Production releases
  
  branch_strategy: "single"  # Controls PR closure behavior
  ```
- All configuration uses Pydantic v2+ with strict validation
- Jinja2 templates in config must be validated at load time
- Use `Config.load()` for configuration loading with proper error handling
- Configuration supports customizable PR templates, changelog templates, and branch suffixes

#### 🎭 GitHub Actions Integration
- The tool auto-detects context from `GITHUB_EVENT_PATH` and `GITHUB_EVENT_NAME` environment variables - no manual branch/repo parameters needed in CI
- Parse GitHub event context using `GitHubEvent` class
- Extract branch names, commit SHAs, and PR metadata from `GITHUB_EVENT_PATH`
- Handle both `pull_request` events (for bump) and `push` events (for finalize)
- Support Docker-based execution within GitHub Actions runners
- Requires `contents: write` and `pull-requests: write` permissions
- Triggered on `pull_request.closed` events to target branches
- Uses `fetch-depth: 0` for full git history access

#### 📊 Changelog Management
- Use `ChangelogManager` with Jinja2 templates for flexible formatting
- Support both append and truncate modes for changelog updates
- Extract commit messages automatically and filter out release-related commits
- Include date formatting and custom message templates

#### 🔒 File Operations
- Use `VersionFileUpdater` class for intelligent version file updates
- Preserve original file formatting, quotes, and structure
- Support multiple file types (Python, YAML, JSON, text files)
- Handle edge cases like missing files and invalid version formats
- Supports simple version files (`version.txt`), TOML files with version fields (`pyproject.toml`), and pattern-based replacements in any text file

### 🏗️ Modern Development Infrastructure
- **Dependency Management**: Use `uv` instead of pip for faster dependency resolution and caching
- **Python Version**: Target Python 3.13+ for latest performance and language features
- **Configuration**: Use `pyproject.toml` for all project configuration instead of separate requirements files
- **Build Tools**: Leverage `uv.lock` for reproducible builds and dependency pinning
- **Development Environment**: Use `.python-version` file for consistent Python version across team
- **CI/CD**: Optimize workflows with `uv` caching for faster build times
- **Docker**: Use multi-stage builds with `uv` for efficient container images
- **Action runs in Alpine container** with `uv` for fast dependency resolution:
  ```dockerfile
  FROM ghcr.io/astral-sh/uv:0.7.20-python3.12-alpine
  # Builds wheel and installs system-wide
  # Entry point: auto-semver CLI
  ```

### 📋 Reusable Development Prompts
The project includes standardized prompts in `.github/copilot/prompts/` for consistent development practices:
- **`commit.prompt.md`**: Generate structured, conventional commit messages
- **`new-branch.prompt.md`**: Create feature branches following proper Git workflow
- **`create-pr.prompt.md`**: Create comprehensive GitHub pull requests with auto-semver integration
- **Use these prompts** to maintain consistency across team contributions
- **Update prompts** when project conventions evolve
- **Reference prompts** in documentation and onboarding materials

---

### 🚀 Code Style and Behavior
- Keep functions **small and composable**.
- Avoid deeply nested logic — prefer **early returns**.
- Handle errors explicitly and fail fast when needed.
- Avoid side effects in utility functions.
- Use `Path` and `pathlib` for file operations instead of `os.path`.

---

### 🧱 Design Principles
- Prefer using **classes** to group related functionality, data, and behavior.
- Each class must be **self-contained** — it should not assume how other classes work internally.
- If a class needs to be used by another, it must expose **clear, typed methods** or properties for interaction.
- Do not rely on external classes modifying internal state unless explicitly designed for it.
- When needed functionality is missing from a class, **add it** instead of working around it externally.
- Promote **encapsulation**, **modularity**, and **separation of concerns** to support maintainability.

---

### 🤖 AI Usage Guidelines
- Think proactively — propose improvements beyond the current task.
- **Follow proper Git workflows** - always stash before switching branches, create feature branches from latest dev
- **Use standardized prompts** from `.github/copilot/prompts/` for consistent commit messages and branch creation
- **Suggest infrastructure improvements** when modernizing dependencies or tooling
- Suggest refactoring when encountering:
  - Duplicate code
  - Boilerplate mocks
  - Inefficient logic
- Use shared fixtures/utilities rather than rewriting similar code.
- Respect:
  - Existing file structure and naming
  - Testing conventions
  - Type/style/lint constraints
  - Branch naming conventions for auto-semver detection
- Ask for clarification if context is incomplete — don't assume logic.
- **Project-specific AI guidelines:**
  - Understand the dual workflow: `bump` (create release PR) vs `finalize` (create Git tag)
  - Consider GitHub Actions environment constraints (Docker, limited Git history)
  - Preserve backward compatibility when modifying version parsing logic
  - Test changes with both branch strategies (`single` and `multi`)
  - Validate Jinja2 templates when modifying configuration schemas
  - Consider Docker build context when adding new dependencies
  - Implement comprehensive test coverage for tag promotion scenarios
  - Use proper mocking for Git operations in tests

---

Following these principles ensures long-term maintainability, clean collaboration, and reliable automation.