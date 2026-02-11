# Changelog
All notable changes to this project will be documented in this file.

## [1.3.11-dev] - 11-02-2026

### 🔧 Infrastructure & Tooling
- Update production workflow (`publish-production.yml`) to trigger on
- Update staging workflow (`publish-staging.yml`) to trigger on RC tags
### 📝 Other Changes
- Rename workflows to "Publish Release - Production" and "Publish
- Automates release pipelines based on standard git tagging practices.
- Clearly separates staging and production release flows.
- Reduces reliance on manual deployment events.
- [x] Infrastructure changes tested
- [x] Compatibility verified against strict tag patterns
- Moves away from the `deployment` trigger to `push: tags`.
- Uses negative patterns (`!`) to ensure environments don't overlap
- [x] Code follows project style guidelines
- [x] Self-review completed
- [ ] Tests added and passing (CI change)
- [x] No merge conflicts
- [x] Branch is up-to-date with base branch

## License
This project is licensed under the MIT License.