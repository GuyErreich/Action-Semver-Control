Generate unit tests for each module in the auto-semver project using `pytest` and `pytest-mock` only.
Avoid `unittest.mock`. Use existing test files as templates.
Use shared fixtures like `GitHubEventFixture` and `FileFixture`.

All code must:
- Pass `ruff`, `black`, and `mypy`
- Use Google-style docstrings
- Include type hints for all functions and variables