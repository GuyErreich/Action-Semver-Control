---
tools: ['changes', 'runInTerminal', 'openSimpleBrowser']
---

# Create GitHub Pull Request

Generate a comprehensive, well-structured pull request following auto-semver conventions and best practices.

## Workflow Steps:

1. **Ensure branch is pushed and up-to-date**
   - `git push -u origin [branch-name]` (if not already pushed)
   - Verify all commits are included

2. **Create PR using GitHub CLI or web interface**
   - **GitHub CLI**: `gh pr create --title "[title]" --body "[description]"`
   - **Web**: Navigate to repository and click "Compare & pull request"

3. **Fill PR details using guidelines below**

## PR Title Format:

Follow conventional commit format aligned with branch type:
```
<type>(<scope>): <description>
```

**Examples by branch type:**
- **Branch: `feature/tag-promotion`** → **Title: `feat: add tag promotion workflow support`**
- **Branch: `fix/memory-leak`** → **Title: `fix: resolve memory leak in version parsing`**
- **Branch: `breaking/api-restructure`** → **Title: `BREAKING CHANGE: restructure API endpoints`**
- **Branch: `chore/upgrade-deps`** → **Title: `chore: upgrade Python runtime to 3.13`**
- **Branch: `docs/readme-update`** → **Title: `docs: update README with new features`**

## PR Description Template:

```markdown
## 🎯 Summary
Brief description of what this PR accomplishes and why it's needed.

## 📋 Changes Made

### [Category 1] (e.g., Core Features, Infrastructure, Bug Fixes):
- Specific change 1
- Specific change 2
- Impact or benefit

### [Category 2]:
- Another change
- Technical details or reasoning

### [Category 3]:
- Additional changes
- Context or dependencies

## 🔄 Auto-Semver Impact
- **Version Bump**: [Major/Minor/Patch] - based on `[branch-prefix]/` naming
- **Branch Type**: `[branch-prefix]/[description]`
- **Expected Version**: [current] → [expected new version]

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases covered

### Test Coverage:
- Describe new test scenarios
- Mention any test fixtures used
- Note any mocking strategies

## 🔧 Technical Details

### Architecture Changes:
- Any new classes, methods, or modules
- Design patterns or principles applied
- Dependencies added or removed

### Configuration Changes:
- New configuration options
- Breaking configuration changes
- Migration steps if applicable

## 💥 Breaking Changes (if applicable)
- **What breaks**: Detailed description of breaking changes
- **Migration**: Steps to update existing usage
- **Alternatives**: Suggested alternatives for deprecated features

## 📚 Documentation
- [ ] Code comments and docstrings updated
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Configuration examples provided

## 🔗 Related Issues
- Closes #[issue-number]
- Related to #[issue-number]
- References #[issue-number]

## 🚀 Deployment Notes
- Any special deployment considerations
- Database migrations needed
- Environment variable changes
- Docker/CI changes

## ✅ Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Branch is up-to-date with base branch
```

## Auto-Semver Specific Guidelines:

### For Feature PRs (`feature/` branches):
```markdown
## 🎯 Summary
Add [feature name] to enhance [functionality area].

## 📋 Changes Made

### Core Features:
- Implement [new functionality]
- Add [new method/class] for [purpose]
- Integrate with existing [component]

### Testing:
- Add comprehensive test suite for [feature]
- Mock [external dependencies] for reliable testing
- Cover edge cases like [specific scenarios]

## 🔄 Auto-Semver Impact
- **Version Bump**: Minor - new feature without breaking changes
- **Branch Type**: `feature/[description]`
- **Expected Version**: 1.2.3 → 1.3.0
```

### For Bug Fix PRs (`fix/`, `bug/`, `hotfix/` branches):
```markdown
## 🎯 Summary
Fix [bug description] that was causing [impact].

## 📋 Changes Made

### Bug Fixes:
- Resolve [specific issue] in [component]
- Add proper error handling for [scenario]
- Update [logic] to handle [edge case]

### Testing:
- Add regression tests for [bug scenario]
- Verify fix doesn't break existing functionality
- Test with various [input types/configurations]

## 🔄 Auto-Semver Impact
- **Version Bump**: Patch - bug fix without breaking changes
- **Branch Type**: `fix/[description]`
- **Expected Version**: 1.2.3 → 1.2.4
```

### For Breaking Change PRs (`breaking/`, `major/` branches):
```markdown
## 🎯 Summary
[BREAKING CHANGE] Restructure [component] for better [reason].

## 📋 Changes Made

### Breaking Changes:
- Change [API/interface] from [old] to [new]
- Remove deprecated [feature/method]
- Update [configuration format]

### Benefits:
- Improved [performance/maintainability/usability]
- Better alignment with [standards/conventions]
- Enhanced [functionality/reliability]

## 💥 Breaking Changes
- **API Changes**: [detailed description]
- **Configuration**: [what needs to be updated]
- **Migration**: See [migration guide/steps]

## 🔄 Auto-Semver Impact
- **Version Bump**: Major - contains breaking changes
- **Branch Type**: `breaking/[description]`
- **Expected Version**: 1.2.3 → 2.0.0
```

### For Infrastructure PRs (`chore/`, `devops/`, `ci/` branches):
```markdown
## 🎯 Summary
Modernize [infrastructure component] for better [performance/maintainability].

## 📋 Changes Made

### Infrastructure:
- Upgrade [dependency] from [old] to [new version]
- Migrate from [old tool] to [new tool]
- Update [configuration/workflow]

### Benefits:
- [X]% faster [build/test/deployment] times
- Better [reliability/security/maintainability]
- Access to [new features/improvements]

## 🔄 Auto-Semver Impact
- **Version Bump**: Patch - infrastructure improvement
- **Branch Type**: `chore/[description]`
- **Expected Version**: 1.2.3 → 1.2.4
```

## PR Best Practices:

### Title Guidelines:
- Use imperative mood ("add", not "added")
- Keep under 50 characters
- Be specific and descriptive
- Align with conventional commit format

### Description Guidelines:
- Explain the "what" and "why"
- Include auto-semver impact information
- Categorize changes logically
- Reference related issues
- Include testing information
- Mention breaking changes prominently

### Review Readiness:
- Self-review code changes
- Ensure CI passes
- Update documentation
- Add comprehensive tests
- Resolve merge conflicts

### Auto-Semver Integration:
- Verify branch name follows conventions
- Confirm expected version bump is correct
- Test promotion scenarios if applicable
- Validate configuration changes
- Check lockfile updates

## GitHub CLI Commands:

**Create PR with template:**
```bash
gh pr create --title "feat: add new feature" --body-file pr-template.md
```

**Create PR interactively:**
```bash
gh pr create --web
```

**Draft PR for early feedback:**
```bash
gh pr create --draft --title "WIP: feature implementation"
```

**Auto-fill from commits:**
```bash
gh pr create --fill
```

## Notes:
- Use draft PRs for early feedback on large changes
- Request specific reviewers familiar with the changed components
- Link related issues and discussions
- Update PR description as changes evolve
- Ensure auto-semver branch naming is correct for proper version bumping
- Consider the impact on existing workflows and users
