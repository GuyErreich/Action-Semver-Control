---
tools: ['createFile', 'createDirectory', 'editFiles', 'search', 'runVscodeCommand', 'runCommands', 'usages', 'think', 'problems', 'changes', 'testFailure', 'githubRepo', 'runTests', 'pylance mcp server', 'getPythonEnvironmentInfo', 'getPythonExecutableCommand', 'installPythonPackage', 'configurePythonEnvironment']
---

Generate unit tests for each module in the auto-semver project using `pytest` and `pytest-mock` only.
Avoid `unittest.mock`. Use existing test files as templates.

Think proactively and suggest out-of-the-box solutions. For example:
- Consolidate repetitive mocks and fixtures into global ones (e.g., shared `GitHubEventFixture`, `FileFixture`)
- Simplify setup using real file/environment simulation instead of mocking internals
- Use real temporary files when possible instead of mocks

All generated code must:
- Pass `ruff`, `ruff format`, and `mypy`
- Use Google-style docstrings
- Include type hints for all functions and variables
- use uv tool.