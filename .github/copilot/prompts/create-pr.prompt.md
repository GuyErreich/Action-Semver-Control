---
description: Create a GitHub Pull Request for existing changes without modifying code or files.
agent: agent
tools: ['edit/createFile', 'search/codebase', 'runCommands', 'github/*', 'memory/*', 'changes', 'fetch', 'githubRepo', 'github.vscode-pull-request-github/copilotCodingAgent', 'github.vscode-pull-request-github/issue_fetch', 'github.vscode-pull-request-github/suggest-fix', 'github.vscode-pull-request-github/searchSyntax', 'github.vscode-pull-request-github/doSearch', 'github.vscode-pull-request-github/renderIssues', 'github.vscode-pull-request-github/activePullRequest', 'github.vscode-pull-request-github/openPullRequest', 'todos']
---

# Create GitHub Pull Request

⚠️ **CRITICAL WARNING: READ-ONLY MODE FOR PR CREATION** ⚠️

**This prompt is ONLY for creating Pull Requests from existing, already-pushed changes.**

**STRICTLY FORBIDDEN:**
- Making new commits or code changes
- Modifying, creating, or deleting any files
- Pushing new changes to the branch
- "Improving" or "fixing" existing code
- Adding features or functionality

**YOUR ONLY TASK:** Create a PR that accurately describes the changes already present in the pushed branch.
 
---

Generate a comprehensive, well-structured pull request following auto-semver conventions and best practices.

## 🤖 Automation Rules (Agent MUST)
1. First check if a PR already exists for (head=current branch, base=default) using: `gh pr list --head <branch> --base <base> --state all`
2. If one exists: OUTPUT the URL and STOP (no body regeneration unless user explicitly asks).
3. If none exists: continue with steps below and attempt creation exactly once.
4. Never modify repository files or create new commits during this prompt.
5. Always build PR body in a temporary markdown file in the current workspace (e.g., `./pr-body.md`) before creation.

## Key Requirements:

### 📝 Use Markdown Files for Examples and Iteration
**ALWAYS use markdown files for PR content creation and examples:**
- Create PR body content in separate markdown files first
- Use files like `./pr-body.md` or `docs/examples/pr-example.md`
- Test and iterate on the markdown content before applying
- This allows for easy editing, formatting verification, and content refinement
- Apply final content using GitHub CLI: `gh pr create --body-file /path/to/file.md`

**Benefits of markdown file approach:**
- Easy iteration and refinement before publishing
- Better formatting control and verification
- Reusable templates and examples
- Version control of PR templates
- Collaborative editing capabilities

## Workflow Steps:

1. **IMPORTANT: Work ONLY with existing pushed changes**
   - **DO NOT** make any new code changes or commits
   - **DO NOT** modify, add, or delete any files
   - **DO NOT** push new changes to the branch
   - Only create a PR for the changes that are already committed and pushed

2. **Verify branch & existing PR (READ-ONLY)**
   - Confirm branch is pushed: `git log --oneline origin/[branch-name]`
   - Check for existing PR: `gh pr list --head [branch] --base [base] --state all`
   - If PR exists: print URL and STOP (do NOT recreate or overwrite)
   - If branch not pushed or diverged unexpectedly: STOP and inform user
   - Confirm working tree clean: `git status` (do not stage/commit anything)

3. **Create PR content in markdown file FIRST**
   - Create markdown file with PR content: `./pr-body.md`
   - Include all sections from the template below
   - Test formatting and content accuracy
   - Iterate and refine as needed

4. **Create PR using GitHub CLI (only if no existing PR)**
   - Run: `gh pr create --base [base] --head [branch] --title "[title]" --body-file ./pr-body.md`
   - If command succeeds: output PR URL and STOP
   - If it fails (network/auth): report error succinctly; do NOT retry automatically more than once

5. **Compliance Checklist (MUST complete mentally before finishing)**
   - [ ] Checked for existing PR first
   - [ ] Did not modify repository files
   - [ ] PR body authored in temp markdown file
   - [ ] Title matches branch intent (no unintended prefixes)
   - [ ] No additional commits created
   - [ ] Stopped immediately after successful creation or existing PR detection

## PR Title Format:

Follow conventional commit format aligned with branch type:
```
<description>
```

**Examples by branch type:**
- **Branch: `feature/tag-promotion`** → **Title: `feat: add tag promotion workflow support`**
- **Branch: `fix/memory-leak`** → **Title: `fix: resolve memory leak in version parsing`**
- **Branch: `breaking/api-restructure`** → **Title: `BREAKING CHANGE: restructure API endpoints`**
- **Branch: `chore/upgrade-deps`** → **Title: `chore: upgrade Python runtime to 3.13`**
- **Branch: `docs/readme-update`** → **Title: `docs: update README with new features`**

## PR Description Template:

**Create this content in a markdown file first (e.g., `./pr-body.md`):**

### Core Required Sections:
```markdown
## 🎯 Summary
Brief description of what this PR accomplishes and why it's needed.

## 📋 Changes Made

**IMPORTANT: Describe only the changes that are already committed and pushed to the branch. Do NOT add new changes.**

### [Category 1] (e.g., Core Features, Infrastructure, Bug Fixes):
- Specific change 1 (already implemented)
- Specific change 2 (already implemented)
- Impact or benefit (of existing changes)

### [Category 2]:
- Another change (already implemented)
- Technical details or reasoning (for existing changes)

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases covered

## 🔧 Technical Details

### Architecture Changes:
- Any new classes, methods, or modules
- Design patterns or principles applied
- Dependencies added or removed

### Code Diffs (for significant changes):
```diff
- old code
+ new code
```

## 📚 Documentation
- [ ] Code comments and docstrings updated
- [ ] README updated if needed
- [ ] API documentation updated

## 🔗 Related Issues
- Closes: (link issue number if applicable)
- Related to: (link issue number if applicable)
- References: (link issue number if applicable)

## ✅ Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Branch is up-to-date with base branch
```

### Optional Sections (Include Only When Relevant):

**Test Strategy** (only for complex testing scenarios):
```markdown
### Test Strategy:
- Describe testing approach and methodology
- Mention test fixtures and mocking strategies
- Document edge cases and scenarios covered
```

**Breaking Changes** (only when there ARE breaking changes):
```markdown
## 💥 Breaking Changes
- **What breaks**: Detailed description of breaking changes
- **Migration**: Steps to update existing usage
- **Alternatives**: Suggested alternatives for deprecated features
```

**Deployment Notes** (only when special deployment considerations exist):
```markdown
## 🚀 Deployment Notes
- Any special deployment considerations
- Database migrations needed
- Environment variable changes
- Docker/CI changes
```

## Markdown File Workflow:

### Step 1: Create PR Body Content
```bash
# Create markdown file with PR content
cat > ./pr-body.md << 'CONTENT'
## 🎯 Summary
[Your PR summary here]

## 📋 Changes Made
[Your changes here]
...
CONTENT
```

### Step 2: Review and Iterate
```bash
# Review the content
cat ./pr-body.md

# Edit if needed
nano ./pr-body.md  # or your preferred editor
```

### Step 3: Create PR with File
```bash
# Create PR only if one does NOT already exist
gh pr list --head feature/your-branch --base dev --state all
# (If no result) then:
gh pr create --base dev --head feature/your-branch --title "feat: your feature title" --body-file ./pr-body.md

# Or for draft PR
gh pr create --draft --title "WIP: feature" --body-file ./pr-body.md
```

## Auto-Semver Specific Templates:

### Feature PR Template (`feature/` branches):
**Save as `/tmp/feature-pr-body.md`:**
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

### Bug Fix PR Template (`fix/`, `bug/`, `hotfix/` branches):
**Save as `/tmp/fix-pr-body.md`:**
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

## 🧪 Testing
- [x] Regression tests added for the specific bug
- [x] Existing functionality verified unaffected
- [x] Edge cases covered

## 🔧 Technical Details

### Breaking Change PR Template (`breaking/`, `major/` branches):
**Save as `/tmp/breaking-pr-body.md`:**
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

### Infrastructure PR Template (`chore/`, `devops/`, `ci/` branches):
**Save as `/tmp/chore-pr-body.md`:**
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

## 🧪 Testing
- [x] Infrastructure changes tested
- [x] Compatibility verified
- [x] Performance improvements validated
```

## GitHub CLI Commands with Markdown Files:

**Create PR with markdown file:**
```bash
gh pr create --title "feat: add new feature" --body-file ./pr-body.md
```

**Create draft PR with file:**
```bash
gh pr create --draft --title "WIP: feature implementation" --body-file ./pr-body.md
```

**Update existing PR with new markdown content:**
```bash
gh pr edit 123 --body-file /tmp/updated-pr-body.md
```

**Create reusable template:**
```bash
# Save template for future use
cp ./pr-body.md docs/templates/feature-pr-template.md
```

## Best Practices with Markdown Files:

### Template Management:
- Create reusable templates for different PR types
- Store templates in `docs/templates/` directory
- Version control your templates for consistency
- Share templates across team members

### Content Iteration:
- Start with basic template, then customize
- Review markdown formatting before applying
- Test with different markdown renderers
- Get feedback on template before creating PR

### Quality Assurance:
- Spell check markdown content
- Verify all links work properly
- Ensure code blocks have proper syntax highlighting
- Test emoji rendering and formatting

### Section Relevance Guidelines:
- **Always include**: Summary, Changes Made, Testing, Technical Details, Documentation, Checklist
- **Include when relevant**: Test Strategy, Breaking Changes, Deployment Notes
- **Remove if not applicable**: Don't include empty sections just to follow a template
- **User feedback**: Listen to user requests to remove irrelevant sections during iteration

## Notes:
- **CRITICAL**: This tool is for creating PRs from EXISTING pushed changes only
- **ALWAYS** check for an existing PR before attempting creation
- **ALWAYS** create PR content in markdown files first for better iteration
- **DO NOT** make any new commits or file modifications during PR creation
