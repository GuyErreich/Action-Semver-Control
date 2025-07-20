---
description: Update the pull request body to accurately reflect the changes made in the codebase.
mode: agent
tools: ['changes', 'codebase', 'runCommands', 'terminalLastCommand', 'activePullRequest']
---
# Update PR Body Prompt

## Overview
This prompt helps you analyze code changes in a pull request and generate a comprehensive, accurate PR body that reflects the actual changes made.

## Instructions

You are an expert code reviewer and technical writer. Your task is to:

1. **Analyze the current PR** using GitHub tools to understand:
   - Current PR title and body
   - All file changes and diffs
   - Test updates and new functionality
   - Infrastructure/configuration changes

2. **Review the actual codebase** to understand:
   - What files were modified and how
   - New tests added or existing tests updated
   - Configuration changes (Dockerfile, CI/CD, etc.)
   - Documentation updates

3. **Generate an updated PR body** that:
   - Accurately reflects all changes made
   - Includes specific technical details with code diffs
   - Documents new test coverage and functionality
   - Explains the reasoning behind changes
   - Follows the established PR template format

## Process Steps

### Step 1: Gather Current PR Information
```bash
# Use the GitHub PR tool to get current state
github-pull-request_activePullRequest()
```

### Step 2: Analyze Code Changes
- Read modified files to understand scope of changes
- Look for new tests, updated functionality, configuration changes
- Identify key technical improvements or refactoring

### Step 3: Create Updated PR Body
- Use the provided template structure
- Include specific code examples and diffs
- Document all test updates and new functionality
- Explain technical decisions and their benefits

### Step 4: Update PR via GitHub CLI
```bash
gh pr edit <PR_NUMBER> --body "$(cat updated_pr_body.md)"
```

## PR Body Template

Use this template structure for consistent, comprehensive PR descriptions:

```markdown
## 🎯 Summary
[Brief overview of what this PR accomplishes]

## 📋 Changes Made

### Infrastructure Improvements:
- **[Category]**: [Specific change with technical details]
- **[Category]**: [Specific change with technical details]

### Test Updates:
- **[Test Category]**: [Specific test changes and what they verify]
- **[Test Category]**: [New tests added and their purpose]

### Technical Changes:
- [Bullet point of specific technical change]
- [Bullet point of specific technical change]

## 🧪 Testing

### New Test Coverage:
- **[Test Name]**: [What it tests and why it's important]

### Test Updates:
- [x] `[test_name]`: [What was changed and why]
- [x] `[test_name]`: [What was changed and why]

## 🔧 Technical Details

### Architecture Changes:
- **[Component]**: [Change description]
- **[Component]**: [Change description]

### [Category] Improvements:
```diff
[Include actual code diff showing before/after]
```

## 📚 Documentation
- [x] [Documentation update description]

## 🔗 Related Issues
[Link to issues this PR addresses]

## 🚀 Deployment Notes
- [Important deployment considerations]
- [Migration steps if needed]
- [Compatibility notes]

## ✅ Checklist
- [x] [Completion item]
- [x] [Completion item]
```

## Key Requirements

### Always Include:
1. **Specific technical details** - Don't use generic descriptions
2. **Actual code diffs** - Show before/after for important changes
3. **Test coverage details** - List specific tests and what they verify
4. **Migration/deployment notes** - Any important considerations
5. **Quantifiable improvements** - Line count reductions, performance gains, etc.

### Use Markdown Files for Examples:
- Create example PR bodies in separate markdown files
- Reference specific files and line numbers when possible
- Include actual code snippets rather than placeholders
- Test the markdown formatting before applying

### Technical Writing Best Practices:
- Use clear, concise language
- Include context for why changes were made
- Explain the benefits and impact of changes
- Use consistent formatting and structure
- Include relevant emojis for visual organization

## Example Usage

```bash
# 1. Analyze current PR
github-pull-request_activePullRequest()

# 2. Review code changes
read_file("/path/to/modified/file", 1, 50)
grep_search("test_", true, "tests/")

# 3. Create updated body in markdown file
create_file("/tmp/updated_pr_body.md", "[new content]")

# 4. Review and iterate on the markdown file
read_file("/tmp/updated_pr_body.md", 1, 100)

# 5. Apply using GitHub CLI
gh pr edit <PR_NUMBER> --body "$(cat /tmp/updated_pr_body.md)"
```

## Quality Checklist

Before updating the PR body, ensure:
- [ ] All actual changes are documented
- [ ] Technical details are specific and accurate
- [ ] Test updates are clearly explained
- [ ] Code diffs show meaningful changes
- [ ] Benefits and reasoning are explained
- [ ] Deployment considerations are noted
- [ ] Markdown formatting is correct
- [ ] Links and references work properly

## Common Pitfalls to Avoid

1. **Generic descriptions** - Always be specific about what changed
2. **Missing test coverage** - Document all test updates and new tests
3. **Incomplete technical details** - Include code diffs and specifics
4. **Poor formatting** - Use consistent markdown structure
5. **Missing context** - Explain why changes were made
6. **Outdated information** - Ensure body reflects current state of PR

## Advanced Tips

### For Complex PRs:
- Break changes into logical categories
- Use collapsible sections for detailed technical info
- Include performance benchmarks if applicable
- Add diagrams or flowcharts for architectural changes

### For Refactoring PRs:
- Show before/after code structure
- Quantify improvements (line count, complexity reduction)
- Explain benefits of the new approach
- Document any breaking changes

### For Bug Fix PRs:
- Describe the issue being fixed
- Explain root cause analysis
- Show how the fix addresses the problem
- Include regression test details
