# dioxide Project Management Guide

**Last Updated**: November 11, 2025
**Project**: https://github.com/users/mikelane/projects/2

## Overview

This guide documents dioxide's GitHub project management setup after the comprehensive improvements made in November 2025. The project now uses a structured label taxonomy, clear milestones, issue relationships, and custom project fields for enhanced visibility and workflow management.

## Label Taxonomy

All issues MUST be tagged with appropriate labels following this taxonomy:

### TYPE Labels (What kind of work)
- `type: feature` - New feature or enhancement
- `type: bug` - Bug or defect
- `type: docs` - Documentation improvements
- `type: task` - Development task or chore
- `type: test` - Testing improvements
- `type: spike` - Research/investigation task

### AREA Labels (Which part of codebase)
- `area: core` - Core container/DI logic
- `area: python` - Python API layer
- `area: rust` - Rust implementation
- `area: ci-cd` - CI/CD pipelines
- `area: docs` - Documentation
- `area: testing` - Test infrastructure
- `area: dx` - Developer experience

### PRIORITY Labels (How urgent)
- `priority: critical` - Critical/breaking issues
- `priority: high` - High priority
- `priority: medium` - Medium priority
- `priority: low` - Low priority

### STATUS Labels (Current state)
- `status: blocked` - Blocked by other work
- `status: needs-review` - Waiting for review
- `status: needs-decision` - Needs architecture/design decision
- `status: in-progress` - Currently being worked on

### SCOPE Labels (Impact level)
- `scope: breaking-change` - Breaking API changes
- `scope: mlp-core` - Core MLP feature (v0.1.0-beta)

### WORKFLOW Labels (Process)
- `workflow: good-first-issue` - Good for newcomers
- `workflow: help-wanted` - Extra attention needed
- `workflow: post-mlp` - Deferred to post-MLP (v0.2.0+)

### Label Best Practices

**Every issue should have**:
- At least ONE `type:` label
- At least ONE `area:` label
- At least ONE `priority:` label (if not in Backlog)

**Optional labels**:
- `status:` labels for workflow state
- `scope:` labels for special characteristics
- `workflow:` labels for contributor guidance

## Milestones

Every issue MUST be assigned to a milestone. No exceptions.

### Active Milestones

**0.0.2-alpha** (Due: Nov 15, 2025)
- Focus: MLP API realignment
- Features: `@component.factory`, `@profile`, global container
- Status: 10/11 complete

**0.0.4-alpha** (Due: Nov 29, 2025)
- Focus: Circular dependency detection and lifecycle protocols
- Features: Initializable/Disposable protocols, graceful shutdown
- Status: 0/2 complete

**0.1.0-beta** (Due: Dec 15, 2025)
- Focus: MLP complete - production ready
- Features: API freeze, performance benchmarks
- Status: 0/1 complete

**Backlog** (No due date)
- Focus: Post-MLP enhancements and nice-to-have features
- Contains: Research spikes, deferred features, user feedback

### Milestone Assignment Rules

1. **In-scope work** → Assign to appropriate release milestone
2. **Future work** → Assign to Backlog
3. **No milestone = Invalid** → Triage immediately

## Issue Relationships

Use GitHub's relationship keywords to establish dependencies and hierarchies.

### Relationship Keywords

**In issue body or comments**, use these keywords:

- `Part of #N` - This issue belongs to epic #N
- `Depends on #N` - This issue requires #N to be completed first
- `Blocks #N` - This issue prevents #N from starting
- `Related to #N` - This issue is connected to #N

### Epic Structure

**Epics** are large features broken into sub-issues:

```
[EPIC] Feature Name (#N)
├─ [SPIKE] Research task (#N+1)
├─ [DECISION] Architecture decision (#N+2)
│   └─ Blocks → [IMPL] Implementation (#N+3)
└─ [IMPL] Implementation (#N+4)
```

**Current Epics**:
- #94 [EPIC] Auto-Detection Research & Implementation
- #95 [EPIC] Lifecycle Management & Resource Cleanup

### Creating Epics

1. Create parent issue with `[EPIC]` prefix
2. List all sub-issues in the body
3. Add `Part of #EPIC` to each sub-issue body
4. Use `Depends on #`, `Blocks #` for dependencies
5. Apply `status: blocked` label to blocked issues

## GitHub Projects v2

**Project URL**: https://github.com/users/mikelane/projects/2

### Custom Fields

The project now has custom fields for better filtering and organization:

**Priority** (Single-select)
- 🔴 Critical
- 🟠 High
- 🟡 Medium
- 🟢 Low

**Area** (Single-select)
- 🎯 Core
- 🐍 Python
- 🦀 Rust
- 🏗️ CI/CD
- 📚 Docs
- 🧪 Testing
- 🎨 DX

**Type** (Single-select)
- ✨ Feature
- 🐛 Bug
- 📝 Docs
- 🔧 Task
- 🧪 Test
- 🔬 Spike

### Using Custom Fields

**When creating/updating issues**:
1. Set Priority field based on `priority:` label
2. Set Area field based on `area:` label
3. Set Type field based on `type:` label

**Note**: Custom fields and labels should stay in sync. Update both when triaging issues.

### Project Views (Manual Setup Required)

The following views should be configured manually in the GitHub UI:

**1. Default Board (By Status)**
- Layout: Board
- Group by: Status
- Columns: Todo → In Progress → Done

**2. By Area Board**
- Layout: Board
- Group by: Area
- Filter: Status not Done
- Columns: Core | Python | Rust | CI/CD | Docs | Testing | DX

**3. By Milestone Table**
- Layout: Table
- Group by: Milestone
- Sort: Priority (Critical → Low)
- Columns: Title, Type, Area, Priority, Status, Assignee

**4. By Priority Table**
- Layout: Table
- Group by: Priority
- Sort: Milestone, Area
- Columns: Title, Type, Area, Milestone, Status, Assignee

**5. Blocked Issues**
- Layout: Table
- Filter: Status = "blocked" OR has label "status: blocked"
- Columns: Title, Blocks (custom text), Type, Area, Assignee

### Creating Views

To create these views manually:

1. Go to: https://github.com/users/mikelane/projects/2
2. Click "+" next to existing views
3. Select "New view"
4. Choose layout (Board or Table)
5. Configure grouping and sorting
6. Add filters as needed
7. Select visible columns
8. Save with descriptive name

## Workflow

### Creating New Issues

1. **Create issue** with descriptive title
   - Use prefixes: `[EPIC]`, `[SPIKE]`, `[DECISION]`, `[IMPL]`

2. **Add labels** (required)
   - At least one `type:`, `area:`, `priority:` label

3. **Assign milestone** (required)
   - Choose appropriate release or Backlog

4. **Set custom fields** (recommended)
   - Priority, Area, Type (should match labels)

5. **Add relationships** (if applicable)
   - Use `Part of #`, `Depends on #`, `Blocks #` keywords

6. **Assign to project** (automatic for repository issues)

### Working on Issues

1. **Assign yourself** to the issue

2. **Update Status** to "In Progress"

3. **Create feature branch**
   ```bash
   git checkout -b feat/issue-123-description
   # or
   git checkout -b fix/issue-123-description
   ```

4. **Update issue** as you work
   - Add progress comments
   - Update relationships if scope changes
   - Add `status: blocked` if dependencies arise

5. **Create Pull Request** when ready
   - Use `Fixes #123` in PR description to auto-close issue
   - Request reviews from CODEOWNERS

### Completing Issues

1. **Merge Pull Request**
   - Issue auto-closes via `Fixes #123` keyword
   - Project status auto-updates to "Done"

2. **Verify closure**
   - Check that issue moved to "Done" column
   - Verify milestone progress updated

3. **Update related issues**
   - Remove `status: blocked` from dependent issues
   - Comment on epic with progress update

## Weekly Status Updates

**Every Friday**:

1. **Review completed work**
   ```bash
   gh issue list --milestone "CURRENT" --state closed --search "closed:>=$(date -v-7d +%Y-%m-%d)"
   ```

2. **Update STATUS.md**
   - Move completed items from "In Progress" to "Completed This Week"
   - Update milestone progress percentage
   - Add "Next Actions" for upcoming week
   - Update "Last Updated" date

3. **Triage new issues**
   - Ensure all issues have labels, milestones, custom fields
   - Assign priorities
   - Create epics for large features

4. **Check for blocked work**
   ```bash
   gh issue list --label "status: blocked" --state open
   ```

## Common Tasks

### Finding Issues to Work On

**Good first issues**:
```bash
gh issue list --label "workflow: good-first-issue" --state open
```

**High priority for current milestone**:
```bash
gh issue list --milestone "0.0.4-alpha" --label "priority: high" --state open
```

**Blocked issues** (to unblock):
```bash
gh issue list --label "status: blocked" --state open
```

### Checking Milestone Progress

```bash
gh api repos/mikelane/dioxide/milestones/8 | jq '{open: .open_issues, closed: .closed_issues, progress: ((.closed_issues * 100) / (.open_issues + .closed_issues))}'
```

### Finding Related Issues

In issue body, look for relationship keywords:
- `Part of #N` - Find parent epic
- `Depends on #N` - Find dependency
- `Blocks #N` - Find what this blocks
- `Related to #N` - Find related work

### Bulk Label Updates

```bash
# Add label to multiple issues
gh issue edit 1 2 3 --add-label "priority: high"

# Remove label from multiple issues
gh issue edit 4 5 6 --remove-label "priority: low"
```

## Troubleshooting

### Issue has no milestone
**Problem**: Issue created without milestone
**Solution**: Triage immediately and assign to appropriate milestone or Backlog

### Custom field not syncing with labels
**Problem**: Field and label mismatch
**Solution**: Manually update both to keep in sync

### Epic not showing sub-issues
**Problem**: Sub-issues missing "Part of #N" keyword
**Solution**: Add relationship keyword to sub-issue bodies

### Blocked issue not visible
**Problem**: Missing `status: blocked` label
**Solution**: Add label and document blocking dependency

## Best Practices

### Labels
- ✅ Apply labels at creation time
- ✅ Use consistent prefixes (`type:`, `area:`, etc.)
- ✅ Update labels if scope changes
- ❌ Don't use deprecated labels
- ❌ Don't leave issues unlabeled

### Milestones
- ✅ Every issue has a milestone
- ✅ Close milestones when 100% complete
- ✅ Set realistic due dates
- ❌ Don't leave issues without milestones
- ❌ Don't create duplicate milestones

### Relationships
- ✅ Document dependencies clearly
- ✅ Use relationship keywords in issue body
- ✅ Create epics for large features
- ✅ Mark blocked issues with label
- ❌ Don't create circular dependencies

### Project Fields
- ✅ Set custom fields to match labels
- ✅ Use fields for filtering and sorting
- ✅ Keep fields updated as work progresses
- ❌ Don't leave fields empty
- ❌ Don't mismatch fields and labels

## Reference

- **Repository**: https://github.com/mikelane/dioxide
- **Project Board**: https://github.com/users/mikelane/projects/2
- **Milestones**: https://github.com/mikelane/dioxide/milestones
- **Labels**: https://github.com/mikelane/dioxide/labels
- **Audit Document**: docs/PM_GITHUB_AUDIT.md

## Change Log

**November 11, 2025** - Initial project management overhaul
- Consolidated from 46+ to 25 labels with consistent taxonomy
- Assigned 100% of issues to milestones
- Created epic structure with relationship keywords
- Added custom Priority, Area, Type fields to Projects v2
- Documented complete workflow and best practices
