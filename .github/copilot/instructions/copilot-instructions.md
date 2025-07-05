> 🧭 This project is an **auto-semver GitHub Action** that automates semantic versioning, changelog management, and pull request creation. It follows strict conventions for Python 3.12+, modern typing, full test coverage, CI-enforced validation, and clean architecture. These guidelines apply to **all contributors and tools**, including GitHub Copilot.

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
- **`auto_semver.cli`**: Command-line interface with `bump` and `finalize` workflows
- **`auto_semver.git.ops`**: Git operations (branch, commit, push, PR creation)
- **`auto_semver.gh.event`**: GitHub Actions event parsing and context extraction
- **`auto_semver.semver`**: Version parsing, bumping, and file updating
- **`auto_semver.changelog`**: Changelog generation with Jinja2 templates
- **`auto_semver.config`**: Pydantic-based configuration management

---

### ✅ General Development
- Use **Python 3.12+**.
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

---

### 📋 Project-Specific Guidelines

#### 🔄 Semantic Versioning Logic
- Use `Version.parse()` to handle complex version formats with prefixes, suffixes, and quotes
- Version bumping follows branch naming conventions:
  - `major/*`, `breaking/*` → major bump
  - `minor/*`, `feature/*`, `feat/*` → minor bump  
  - `patch/*`, `fix/*`, `hotfix/*`, `bugfix/*` → patch bump
- Preserve original formatting when updating version files (titles, quotes, prefixes)
- Support tag promotion scenarios where versions are promoted between branches without bumping

#### 🌿 Git Operations
- Use `GitOps` class for all Git operations - never call git commands directly
- Always use lockfiles (`.semver.lock`) to track release state and prevent version regressions
- Support both `single` and `multi` branch strategies for different workflow types
- Handle GitHub API operations through `GitOps._get_github_repo()` method

#### 📝 Configuration Management
- All configuration uses Pydantic v2+ with strict validation
- Jinja2 templates in config must be validated at load time
- Use `Config.load()` for configuration loading with proper error handling
- Configuration supports customizable PR templates, changelog templates, and branch suffixes

#### 🎭 GitHub Actions Integration
- Parse GitHub event context using `GitHubEvent` class
- Extract branch names, commit SHAs, and PR metadata from `GITHUB_EVENT_PATH`
- Handle both `pull_request` events (for bump) and `push` events (for finalize)
- Support Docker-based execution within GitHub Actions runners

#### 📊 Changelog Management
- Use `ChangelogManager` with Jinja2 templates for flexible formatting
- Support both append and truncate modes for changelog updates
- Extract commit messages automatically and filter out release-related commits
- Include date formatting and custom message templates

#### 🔒 File Operations
- Use `VersionFileUpdater` for intelligent version file updates
- Preserve original file formatting, quotes, and structure
- Support multiple file types (Python, YAML, JSON, text files)
- Handle edge cases like missing files and invalid version formats

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
- Suggest refactoring when encountering:
  - Duplicate code
  - Boilerplate mocks
  - Inefficient logic
- Use shared fixtures/utilities rather than rewriting similar code.
- Respect:
  - Existing file structure and naming
  - Testing conventions
  - Type/style/lint constraints
- Ask for clarification if context is incomplete — don't assume logic.
- **Project-specific AI guidelines:**
  - Understand the dual workflow: `bump` (create release PR) vs `finalize` (create Git tag)
  - Consider GitHub Actions environment constraints (Docker, limited Git history)
  - Preserve backward compatibility when modifying version parsing logic
  - Test changes with both branch strategies (`single` and `multi`)
  - Validate Jinja2 templates when modifying configuration schemas
  - Consider Docker build context when adding new dependencies

---

Following these principles ensures long-term maintainability, clean collaboration, and reliable automation.