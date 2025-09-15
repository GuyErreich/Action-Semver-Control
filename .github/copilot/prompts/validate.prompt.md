---
tools: ['runCommands', 'runTasks', 'editFiles', 'runNotebooks', 'search', 'new', 'extensions', 'usages', 'vscodeAPI', 'think', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'todos', 'runTests', 'pylance mcp server', 'sequentialthinking', 'memory', 'getPythonEnvironmentInfo', 'getPythonExecutableCommand', 'installPythonPackage', 'configurePythonEnvironment']
---

Validate that the entire project CI pipeline works correctly.

For every change or generated code, ensure the following checks pass:
- ✅ Unit tests (pytest)
- ✅ Type checking (mypy)
- ✅ Code formatting (ruff format)
- ✅ Linting (ruff)

Be proactive:
- If any failure occurs, identify and **automatically apply safe and minimal fixes** to resolve it.
- If the issue requires a decision (e.g., missing types), suggest a fix and wait for confirmation.
- Ensure all fixes preserve the current behavior and respect existing code style.
- Fix formatting, typing, or unused imports using the appropriate tools (`ruff`, etc.).
- If needed, install missing tools using the Python environment.

Cross-check:
- Test coverage and test relevance.
- Temporary files or mock setups match the test expectations.
- Prefer end-to-end or integration-style testing where mocks break logic.

Use:
- Always use Taskfiles for validation: `task test`, `task lint`, `task fmt`, etc.
- Do not run tools directly unless Taskfile commands are missing.
- CI workflows (`.github/workflows/`)
- `pyproject.toml` or other config files for tool settings.