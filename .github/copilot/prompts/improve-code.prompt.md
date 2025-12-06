# Code Improvement Guidelines

When asked to improve code or implement features, you must strictly adhere to the following best practices:

## 1. Fail Fast Strategy
- Validate inputs and preconditions at the beginning of functions/methods.
- Raise errors immediately when an invalid state is detected.
- Avoid deep nesting by returning early or raising exceptions.

## 2. Logging
- Use the project's logging infrastructure.
- Log meaningful events with appropriate severity levels (DEBUG, INFO, WARNING, ERROR).
- Ensure logs provide context (e.g., variable values, operation IDs) to aid debugging.

## 3. Error Handling
- Raise specific, semantic exceptions rather than generic `Exception` or `Error`.
- Define custom exception classes if the existing ones do not cover the failure mode.
- Ensure error messages are descriptive and actionable.

## 4. Documentation (Google Style)
- **Modules**: Include a module-level docstring describing its purpose.
- **Classes**: Document the class purpose, attributes, and usage.
- **Methods/Functions**:
  - Use Google-style docstrings.
  - Include `Args:`, `Returns:`, and `Raises:` sections.
  - Describe the behavior clearly.

## 5. Function/Method Signatures
- **Keyword-Only Arguments**: Prefer declaring arguments after a bare `*` to enforce keyword usage, especially for functions with multiple arguments.
- **Explicit Optionality**:
  - Avoid implicit optionality.
  - If an argument is optional, explicitly provide a default value (e.g., `arg: str | None = None`).
  - Do not leave arguments "optional" without a default value unless they are required.

## 6. Type Safety
- **Strict Typing**: 100% type hint coverage is required.
- **Prohibited Types**: NEVER use `Any` or `object`.
- **Custom Types**: Create `TypeAlias`, `NewType`, or `Pydantic` models to represent complex data structures or domain concepts.

## 7. Test Coverage
- Ensure all new logic is covered by unit tests.
- Update existing tests if logic changes.
- Aim for high branch coverage.

## 8. Documentation Updates
- If the changes affect how the tool is used, configured, or behaves, update `README.md` immediately.
- Keep documentation in sync with the code.
