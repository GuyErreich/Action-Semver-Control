---
tools: ['codebase', 'runCommands', 'changes', 'GitKraken (bundled with GitLens)', 'github', 'sequentialthinking', 'memory']
---

# Create New Branch

Follow proper Git workflow to create a new branch with all current changes.

## Workflow Steps:

1.. **Create new feature branch**
   - Use descriptive branch name following auto-semver conventions (see below)

7. **Push branch with upstream tracking**
   - `git push -u origin [branch-name]`

## Auto-Semver Branch Naming Conventions:

### Major Version Bumps (Breaking Changes):
- `breaking/[description]` - For breaking changes that require major version bump
- `major/[description]` - For major feature releases
- Examples: `breaking/api-restructure`, `major/new-authentication-system`

### Minor Version Bumps (New Features):
- `feature/[description]` - For new features that don't break existing functionality
- Examples: `feature/user-authentication`, `feature/email-notifications`

### Patch Version Bumps (Bug Fixes & Maintenance):
- `fix/[description]` - For bug fixes
- `bug/[description]` - Alternative for bug fixes
- `hotfix/[description]` - For urgent production fixes
- `chore/[description]` - For maintenance tasks, dependency updates
- `devops/[description]` - For DevOps and infrastructure changes
- Examples: `fix/memory-leak`, `bug/login-error`, `hotfix/security-patch`, `chore/update-dependencies`

### Other Branch Types (Default to Patch):
- `docs/[description]` - For documentation changes
- `refactor/[description]` - For code refactoring
- `style/[description]` - For code style changes
- `test/[description]` - For adding or updating tests
- `ci/[description]` - For CI/CD changes
- Examples: `docs/api-documentation`, `refactor/cleanup-utils`, `test/add-unit-tests`

## Naming Guidelines:
- Use kebab-case (lowercase with hyphens)
- Be descriptive but concise
- Always include the appropriate prefix for auto-semver detection
- Use meaningful descriptions that explain the change
- Avoid generic names like `fix/bug` or `feature/new-stuff`

## Version Bump Detection:
The auto-semver system will automatically detect the version bump type based on your branch name:
- **Major**: `breaking/`, `major/` → 1.0.0 → 2.0.0
- **Minor**: `feature/` → 1.0.0 → 1.1.0  
- **Patch**: `fix/`, `bug/`, `hotfix/`, `chore/`, `devops/` → 1.0.0 → 1.0.1
- **Default**: Any other prefix defaults to patch bump

## Notes:
- Always stash before switching branches to avoid losing work
- Ensure you're on the latest main/dev before creating new branch
- Use `-u` flag on first push to set upstream tracking
- Choose the prefix carefully as it determines the version bump type
- Consider the impact of your changes when selecting the branch type