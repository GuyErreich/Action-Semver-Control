---
description: Create a commit for existing changes without modifying code or files.
agent: agent
tools: ['codebase', 'runCommands', 'think', 'changes', 'todos', 'github', 'memory']
---

# Create Proper Commit Message

Generate a comprehensive, well-structured commit message following auto-semver best practices with descriptive titles (no conventional commit prefixes).

## Requirements:

### 1. Analyze Current Changes
- Review staged/unstaged files using `git status` and `git diff`
- Understand the scope and impact of changes
- Identify the primary purpose (feature, fix, refactor, etc.)
- Consider if changes are breaking, additive, or maintenance

### 2. Create Structured Commit Message

#### Title Format:
<description>

**Description:** 
- Use imperative mood ("Add", not "added")
- Keep under 50 characters
- Don't end with period
- Be specific and meaningful
- **Start with capital letter** for proper imperative mood
- **NO conventional commit prefixes** (no `fix:`, `feat:`, `chore:`, etc.)
- Branch name already indicates the type and version bump

#### Body Format:

[Category 1]:
- Specific change 1
- Specific change 2

[Category 2]:
- Another change
- Impact or reasoning

Breaking Changes:
- Any breaking changes (if applicable)
- Migration steps or notes

Additional Notes:
- Context, reasoning, or future considerations
- References to issues or PRs


### 3. Examples:

**Simple patch fix:**

Resolve token expiration handling

- Fix JWT token validation logic
- Add proper error handling for expired tokens
- Update error messages for better user experience

**New feature (minor bump):**

Add tag promotion workflow support

Core Features:
- Implement _detect_tag_source_branch() for version detection
- Add _is_tag_promotion_scenario() to identify promotions
- Preserve version numbers during tag promotions

Testing:
- Add comprehensive test suite for promotion scenarios
- Mock git operations for reliable testing

Documentation:
- Update README with promotion workflow examples
- Add inline documentation for new methods

**Breaking change (major bump):**

Restructure API endpoint naming

Breaking Changes:
- Change all API endpoints from /v1/ to /api/v2/
- Rename 'files_to_update' config to 'version_files'
- Update response format for version endpoints

Migration Guide:
- Update client code to use new endpoint structure
- Update configuration files with new property names
- See MIGRATION.md for detailed steps

Benefits:
- More consistent API design
- Better alignment with REST conventions
- Improved error handling and responses

**Infrastructure/DevOps:**

Upgrade Python runtime to 3.13

Infrastructure:
- Update Dockerfile to use Python 3.13
- Update CI workflows for new Python version
- Add .python-version for development consistency

Dependencies:
- Migrate from pip to uv for faster builds
- Update pyproject.toml with new dependency groups
- Remove legacy requirements.txt files

Benefits:
- 20% faster dependency resolution with uv
- Better development environment consistency
- Access to latest Python performance improvements

**Documentation:**

Update branch naming conventions in README

Documentation Updates:
- Add auto-semver branch naming conventions
- Include version bump detection examples
- Update development workflow guidelines

Additional Notes:
- Ensures team alignment on branch naming
- Helps new contributors understand version impact
- References implementation in version.py

## Auto-Semver Integration:

Your branch name determines the version bump type, NOT your commit title:
- **Branch: `feature/`** → Minor bump (commit title: descriptive only, no prefixes)
- **Branch: `fix/`, `bug/`, `hotfix/`** → Patch bump (commit title: descriptive only, no prefixes)
- **Branch: `breaking/`, `major/`** → Major bump (commit title: descriptive only, no prefixes)
- **Branch: `chore/`, `devops/`** → Patch bump (commit title: descriptive only, no prefixes)
- **Branch: `docs/`** → No version bump (commit title: descriptive only, no prefixes)

**Important**: Do NOT use conventional commit prefixes like `fix:`, `feat:`, `chore:`, etc. in commit titles. The branch name already indicates the type and determines the version bump.

## Guidelines:
- Be specific about what changed and why
- Group related changes logically using categories
- Explain impact and benefits for significant changes
- Keep each line under 72 characters in body
- Use bullet points for clarity
- Include context for future developers
- Reference issues/PRs when applicable
- Consider the audience (team members, future maintainers)
- **Never use conventional commit prefixes in titles** - the branch name determines version bump type
- Use descriptive, imperative titles without type prefixes

## Commit Message Quality Checklist:
- [ ] Title uses descriptive language without conventional commit prefixes
- [ ] Description is clear and under 50 characters
- [ ] Body explains what, why, and impact (for non-trivial changes)
- [ ] Breaking changes are clearly documented
- [ ] Branch name (not commit title) determines version bump type
- [ ] Grammar and spelling are correct
- [ ] No `fix:`, `feat:`, `chore:`, or other conventional prefixes used