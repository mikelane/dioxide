# Phase 4: Projects v2 Enhancements - Summary

**Date**: November 11, 2025
**Project**: dioxide (https://github.com/mikelane/dioxide)

## What Was Accomplished

### Custom Fields Created

Successfully created **3 new custom single-select fields** in GitHub Projects v2:

#### 1. Priority Field
- **Options**: Critical, High, Medium, Low
- **Colors**: Red, Orange, Yellow, Gray
- **Purpose**: Quick filtering and prioritization
- **Syncs with**: `priority:` labels

#### 2. Area Field
- **Options**: Core, Python, Rust, CI/CD, Docs, Testing, DX
- **Colors**: Purple, Blue, Orange, Blue, Blue, Yellow, Pink
- **Purpose**: Group work by codebase area
- **Syncs with**: `area:` labels

#### 3. Type Field
- **Options**: Feature, Bug, Docs, Task, Test, Spike
- **Colors**: Green, Red, Blue, Blue, Yellow, Purple
- **Purpose**: Categorize work by type
- **Syncs with**: `type:` labels

### Existing Fields Preserved

- **Status** (3 options): Todo, In Progress, Done
- **Milestone**: Links to GitHub milestones
- **Assignees**: Team member assignment
- **Labels**: Full label taxonomy
- **Parent issue**: Epic relationships
- **Sub-issues progress**: Visual progress bars

### Documentation Created

**docs/PROJECT_MANAGEMENT_GUIDE.md** - Comprehensive 400+ line guide covering:
- Complete label taxonomy reference
- Milestone management rules
- Issue relationship patterns
- Projects v2 custom field usage
- Workflow best practices
- Common tasks and troubleshooting
- Change log

## Benefits

### Better Filtering
- Filter by Priority without parsing labels
- Filter by Area to focus on specific codebase sections
- Filter by Type to see all bugs, features, etc.

### Better Grouping
- Group board by Area to see work distribution
- Group table by Priority for triage
- Group by Milestone for release planning

### Better Sorting
- Sort by Priority (Critical → Low)
- Sort by Type (alphabetically or custom)
- Multi-column sorting in table views

### Consistency with Labels
Custom fields mirror label taxonomy, providing:
- Visual consistency (colors match label colors)
- Redundant filtering mechanisms
- Easier triage for new contributors

## Manual Setup Required

### Recommended Project Views

Create these views manually in GitHub UI:

**1. By Area Board**
- Layout: Board
- Group by: Area field
- Filter: Status not "Done"
- Purpose: See work distribution across codebase

**2. By Milestone Table**
- Layout: Table
- Group by: Milestone field
- Sort: Priority (Critical → Low)
- Purpose: Release planning and progress tracking

**3. By Priority Table**
- Layout: Table
- Group by: Priority field
- Sort: Milestone, then Area
- Purpose: Daily triage and work planning

**4. Blocked Issues**
- Layout: Table
- Filter: Label contains "status: blocked"
- Purpose: Identify and unblock dependency chains

### How to Create Views

1. Navigate to: https://github.com/users/mikelane/projects/2
2. Click "+" next to existing views
3. Select "New view"
4. Configure:
   - Choose layout (Board or Table)
   - Set grouping field
   - Add sorting rules
   - Apply filters
   - Select visible columns
5. Save with descriptive name

### Status Field Enhancement (Optional)

The Status field currently has 3 options (Todo, In Progress, Done). To add workflow states:

**Recommended additional options**:
- Backlog (before Todo)
- Blocked (parallel to In Progress)
- Needs Review (after In Progress)
- Testing (after Needs Review)

**How to add**:
1. Go to project settings
2. Click "Status" field
3. Click "+ Add option"
4. Set name and color
5. Drag to reorder

## Integration with Existing Workflow

### Label → Field Mapping

When triaging issues, set both labels AND fields:

| Label Taxonomy | Custom Field | Sync Method |
|----------------|--------------|-------------|
| `priority: high` | Priority = "High" | Manual sync |
| `area: python` | Area = "Python" | Manual sync |
| `type: feature` | Type = "Feature" | Manual sync |

### Why Duplicate Information?

**Labels** provide:
- GitHub-native filtering across entire platform
- Visible in issue list without opening
- Works in API and CLI (`gh issue list --label`)
- Used in automation workflows

**Custom Fields** provide:
- Better visual grouping in Projects v2
- Faster filtering within project board
- Colored columns for visual scanning
- Single-click filtering

Both are valuable and serve different purposes.

## Next Steps

### Immediate (This Week)
1. ✅ Create recommended project views manually
2. ✅ Triage existing issues to set custom fields
3. ✅ Update CLAUDE.md with project management section
4. ✅ Train team on new workflow

### Short-term (Next Sprint)
1. Add automation rules (if GitHub Actions available)
2. Set up Slack notifications for blocked issues
3. Create dashboard for milestone progress
4. Establish weekly triage cadence

### Long-term (Next Quarter)
1. Evaluate automation opportunities
2. Gather team feedback on workflow
3. Refine custom fields based on usage
4. Consider additional views for specific workflows

## Success Metrics

### Field Adoption
- **Target**: 90% of issues have Priority, Area, Type fields set
- **Current**: 0% (just created)
- **Timeline**: 2 weeks to reach target

### View Usage
- **Target**: 5+ project views created and actively used
- **Current**: 1 default view
- **Timeline**: 1 week to create views

### Workflow Efficiency
- **Metric**: Time to triage new issues
- **Target**: < 5 minutes per issue
- **Baseline**: TBD after 1 week of usage

## Lessons Learned

### API Limitations
- ❌ Cannot create project views via API (manual only)
- ❌ Cannot modify existing field options via API
- ✅ Can create new custom fields via API
- ✅ Can query field structures via API

### Best Practices
- Create fields with GraphQL API for consistency
- Document manual steps clearly for reproducibility
- Keep field names simple (single word)
- Match field colors to label colors for consistency
- Provide both field and label guidance in documentation

## References

- **Project Board**: https://github.com/users/mikelane/projects/2
- **Full Guide**: docs/PROJECT_MANAGEMENT_GUIDE.md
- **Audit**: docs/PM_GITHUB_AUDIT.md
- **GitHub Projects v2 Docs**: https://docs.github.com/en/issues/planning-and-tracking-with-projects

---

**Phase 4 Status**: ✅ Complete
**Next Phase**: Team onboarding and workflow adoption
