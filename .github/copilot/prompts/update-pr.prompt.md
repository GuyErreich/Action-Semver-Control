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
   - **Only includes relevant sections** - removes sections that don't apply

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

### Step 3: Create Updated PR Body in Markdown File
- **Always create markdown file first**: `/tmp/updated-pr-body.md`
- Use the provided template structure
- Include specific code examples and diffs
- Document all test updates and new functionality
- Explain technical decisions and their benefits
- **Remove irrelevant sections** based on the actual changes

### Step 4: Review and Iterate
- Review the markdown file content
- Test formatting and content accuracy
- Listen to user feedback about section relevance
- Remove or modify sections based on feedback

### Step 5: Update PR via GitHub CLI
```bash
gh pr edit <PR_NUMBER> --body-file /tmp/updated-pr-body.md
```

## PR Body Template

### Core Required Sections:
```markdown
## 🎯 Summary
[Brief overview of what this PR accomplishes]

## 📋 Changes Made

### [Relevant Category]:
- **[Specific Component]**: [Specific change with technical details]
- **[Specific Component]**: [Specific change with technical details]

## 🧪 Testing
- [x] [Specific test changes and what they verify]
- [x] [New tests added and their purpose]

## 🔧 Technical Details

### Architecture Changes:
- **[Component]**: [Change description]

### Code Diff:
```diff
[Include actual code diff showing before/after]
```

## �� Documentation
- [x] [Specific documentation updates]

## 🔗 Related Issues
[Link to issues this PR addresses]

## ✅ Checklist
- [x] [Specific completion items based on actual changes]
```

### Optional Sections (Include Only When Relevant):

**Auto-Semver Impact** (only for auto-semver projects):
```markdown
## 🔄 Auto-Semver Impact
- **Version Bump**: [Major/Minor/Patch]
- **Branch Type**: `[branch-prefix]/[description]`
- **Expected Version**: [current] → [expected new version]
```

**Test Strategy** (only for complex testing scenarios):
```markdown
### Test Strategy:
- [Specific testing approach used]
- [Test fixtures and mocking strategies employed]
- [Edge cases and scenarios covered]
```

**Breaking Changes** (only when there ARE breaking changes):
```markdown
## 💥 Breaking Changes
- **What breaks**: [Detailed description of breaking changes]
- **Migration**: [Steps to update existing usage]
- **Alternatives**: [Suggested alternatives for deprecated features]
```

**Deployment Notes** (only when special deployment considerations exist):
```markdown
## 🚀 Deployment Notes
- [Specific deployment considerations]
- [Migration steps if needed]
- [Compatibility notes]
```

## Key Requirements

### Always Include:
1. **Specific technical details** - Don't use generic descriptions
2. **Actual code diffs** - Show before/after for important changes
3. **Test coverage details** - List specific tests and what they verify
4. **Accurate categorization** - Use categories that match the actual changes

### Section Relevance Guidelines:
- **Always assess relevance** - Don't include sections just because they're in a template
- **Remove empty sections** - If there are no breaking changes, don't include that section
- **Listen to user feedback** - Remove sections users identify as irrelevant
- **Focus on actual changes** - Only describe what was actually modified

### Use Markdown Files for Examples:
- **Always create markdown file first**: `/tmp/updated-pr-body.md`
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
cat > /tmp/updated-pr-body.md << 'CONTENT'
## 🎯 Summary
[Accurate summary based on actual changes]

## 📋 Changes Made
[Only categories that actually apply]
...
CONTENT

# 4. Review and iterate on the markdown file
cat /tmp/updated-pr-body.md

# 5. Apply using GitHub CLI
gh pr edit <PR_NUMBER> --body-file /tmp/updated-pr-body.md
```

## Quality Checklist

Before updating the PR body, ensure:
- [ ] All actual changes are documented
- [ ] Technical details are specific and accurate
- [ ] Test updates are clearly explained
- [ ] Code diffs show meaningful changes
- [ ] Benefits and reasoning are explained
- [ ] Only relevant sections are included
- [ ] Irrelevant sections are removed
- [ ] Markdown formatting is correct
- [ ] Links and references work properly

## Common Pitfalls to Avoid

1. **Generic descriptions** - Always be specific about what changed
2. **Missing test coverage** - Document all test updates and new tests
3. **Incomplete technical details** - Include code diffs and specifics
4. **Poor formatting** - Use consistent markdown structure
5. **Missing context** - Explain why changes were made
6. **Outdated information** - Ensure body reflects current state of PR
7. **Irrelevant sections** - Don't include sections that don't apply to the changes
8. **Template following blindly** - Adapt template to match actual changes

## Advanced Tips

### For Simple Bug Fixes:
- Focus on the core fix and testing
- Remove complex sections like "Architecture Changes" if not applicable
- Keep deployment notes only if there are special considerations

### For Complex Features:
- Break changes into logical categories
- Use collapsible sections for detailed technical info
- Include performance benchmarks if applicable
- Add diagrams or flowcharts for architectural changes

### For Refactoring PRs:
- Show before/after code structure
- Quantify improvements (line count, complexity reduction)
- Explain benefits of the new approach
- Remove irrelevant sections like "Breaking Changes" if there are none

### For Infrastructure Changes:
- Focus on deployment and compatibility impacts
- Include configuration changes and migration steps
- Document testing of infrastructure changes
- Remove feature-related sections that don't apply

## Iteration Based on User Feedback

### Listen for these feedback patterns:
- "Remove [section name] - it's not relevant"
- "This doesn't apply to this PR"
- "Too much detail in [section]"
- "Missing information about [specific aspect]"

### Respond by:
- Immediately removing identified irrelevant sections
- Simplifying overly complex sections
- Adding missing information as requested
- Adapting the template to match the actual changes

### Remember:
- **User knows their codebase best** - trust their judgment on relevance
- **Templates are starting points** - not rigid requirements
- **Iteration improves quality** - embrace feedback for better PRs
- **Flexibility is key** - adapt to the specific needs of each PR
