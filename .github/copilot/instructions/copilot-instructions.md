> 🧭 This project follows strict conventions for Python 3.12+, modern typing, full test coverage, CI-enforced validation, and clean architecture. These guidelines apply to **all contributors and tools**, including GitHub Copilot.

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

### 🚀 Code Style and Behavior
- Keep functions **small and composable**.
- Avoid deeply nested logic — prefer **early returns**.
- Handle errors explicitly and fail fast when needed.
- Avoid side effects in utility functions.
- Use `Path` and `pathlib` for file operations instead of `os.path`.

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
- Ask for clarification if context is incomplete — don’t assume logic.

---

Following these principles ensures long-term maintainability, clean collaboration, and reliable automation.