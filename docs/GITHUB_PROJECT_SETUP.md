# GitHub Project Setup Guide

**Last Updated:** 2025-10-21
**Status:** Ready for Setup

---

## Overview

This guide provides step-by-step instructions for setting up the GitHub Project board for dioxide. The GitHub CLI and API have limited support for Projects v2, so the board must be created manually through the GitHub web interface.

---

## Current Issue Status

### v0.1 Walking Skeleton Issues (Created)

**Infrastructure & Documentation:**
- #7 - [INFRA] Set up CI/CD pipeline
- #8 - [DOC] ADR-001: Container Architecture
- #9 - [DOC] ADR-002: PyO3 Binding Strategy
- #15 - [TEST] Set up pytest-bdd framework
- #16 - [INFRA] Configure maturin build and create installable package
- #17 - [DOC] Create usage documentation and examples
- #18 - [INFRA] Set up performance benchmarks

**Implementation:**
- #10 - Implement basic Container structure (Rust core)
- #11 - Implement Instance Provider registration
- #12 - Implement Class Provider registration
- #13 - Implement Factory Provider registration
- #14 - Implement basic dependency resolution

**Edge Cases:**
- #3 - Prevent duplicate component registration

**Total v0.1 Issues:** 12

### v0.2 Core Features Issues (Deferred)

- #1 - Resolve dependencies by type
- #2 - Inject values by parameter name
- #4 - Graceful shutdown of singleton resources
- #5 - Detect and report circular dependencies
- #6 - Support named tokens for disambiguation

**Total v0.2 Issues:** 5

---

## Step 1: Create GitHub Project

1. Go to https://github.com/mikelane/dioxide
2. Click the **Projects** tab
3. Click **New project** button
4. Choose **Table** template (we'll add Board view later)
5. Name it: **Dioxide Development**
6. Click **Create project**

---

## Step 2: Configure Project Fields

### Add Custom Fields

Click the **⋮** (more options) next to any column header, then **Settings**.

Add these custom fields:

#### 1. Status (Single select)
**Important:** GitHub automatically creates a Status field. Edit it to have these values:
- 📋 Backlog
- 🔍 Ready for BDD
- ✅ BDD Complete
- 🚧 In Development
- 👀 In Review
- 🧪 QA Validation
- 🚀 Ready to Deploy
- ✔️ Done

#### 2. Type (Single select)
**Note:** Use existing GitHub labels, but this provides better filtering.
- Feature
- Bug
- Story
- Task
- Docs
- Test
- Infrastructure

#### 3. Area (Single select)
- Core
- Lifecycle
- Rust
- Python
- Testing
- Docs
- Infrastructure

#### 4. Sprint (Single select)
- Sprint 1 (v0.1 - Weeks 1-2)
- Sprint 2 (v0.2 - Weeks 3-4)
- Sprint 3 (v0.2 - Weeks 5-6)
- Backlog

#### 5. Story Points (Number)
For estimation (optional for v0.1)
- 1 = <4 hours
- 2 = 4-8 hours
- 3 = 1-2 days
- 5 = 2-3 days
- 8 = 3-5 days

---

## Step 3: Add Issues to Project

1. In the project, click **+ Add item** (bottom of any column)
2. Type `#` to search for issues
3. Add all issues #1-18 to the project

**Or use the bulk import:**
1. Click **⋮** (more options) → **Settings**
2. Click **Manage access**
3. Scroll to **Danger zone** → **Import items**
4. Select repository: `mikelane/dioxide`
5. Click **Import all open issues**

---

## Step 4: Configure Initial Status

Set the initial status for each issue:

### Backlog (Not yet started)
- #1, #2, #4, #5, #6 (v0.2 features)

### Ready for BDD (Needs BDD scenarios written)
- All v0.1 issues start here initially

### Priority Order (v0.1 Issues)

**High Priority (Week 1 - Days 1-2):**
1. #7 - CI/CD setup
2. #8 - ADR-001
3. #9 - ADR-002
4. #15 - pytest-bdd setup

**High Priority (Week 1 - Days 3-5):**
5. #10 - Container structure
6. #11 - Instance Provider
7. #12 - Class Provider
8. #13 - Factory Provider
9. #14 - Resolution
10. #3 - Duplicate prevention

**Medium Priority (Week 2):**
11. #16 - Maturin build
12. #17 - Documentation
13. #18 - Benchmarks

---

## Step 5: Create Project Views

### View 1: Sprint Board (Board Layout)

1. Click **+ New view**
2. Select **Board** layout
3. Name it: **Sprint Board**
4. Group by: **Status**
5. Filter: `milestone:"v0.1 Walking Skeleton"`
6. Sort: **Manual** (drag to reorder)
7. Save view

This view shows the current sprint (v0.1) in a kanban board.

### View 2: v0.1 Checklist (Table Layout)

1. Click **+ New view**
2. Select **Table** layout
3. Name it: **v0.1 Checklist**
4. Filter: `milestone:"v0.1 Walking Skeleton"`
5. Group by: **Status**
6. Sort by: **Priority** (high to low)
7. Show fields: Title, Status, Type, Area, Assignee, Labels
8. Save view

This view shows all v0.1 tasks in priority order.

### View 3: v0.2 Backlog (Table Layout)

1. Click **+ New view**
2. Select **Table** layout
3. Name it: **v0.2 Backlog**
4. Filter: `milestone:"v0.2 Core Features"`
5. Group by: **Type**
6. Sort by: **Priority** (high to low)
7. Show fields: Title, Status, Type, Area
8. Save view

This view shows all v0.2 features for future planning.

### View 4: All Issues (Table Layout)

1. Click **+ New view**
2. Select **Table** layout
3. Name it: **All Issues**
4. Filter: None (show everything)
5. Group by: **Milestone**
6. Sort by: **Created** (newest first)
7. Show all fields
8. Save view

This view shows everything for comprehensive overview.

---

## Step 6: Configure Automation (Optional)

GitHub Projects supports automated workflows:

### Auto-close on PR merge
1. Go to **⋮** → **Settings** → **Workflows**
2. Enable: **Item closed** → when linked PR is closed
3. Set Status to: **✔️ Done**

### Auto-add new issues
1. Enable: **Auto-add to project**
2. Set filter: `is:open is:issue repo:mikelane/dioxide`
3. Set initial Status: **📋 Backlog**

---

## Step 7: Project Workflow

### Issue Lifecycle

```
📋 Backlog
    ↓
🔍 Ready for BDD (QA writes BDD scenarios)
    ↓
✅ BDD Complete (Scenarios written and failing)
    ↓
🚧 In Development (Developer implements)
    ↓
👀 In Review (Code reviewer reviews)
    ↓
🧪 QA Validation (QA validates BDD passes)
    ↓
🚀 Ready to Deploy (Merged to main)
    ↓
✔️ Done (Deployed/released)
```

### Who Moves Issues

| Transition | Who | When |
|------------|-----|------|
| Backlog → Ready for BDD | Product Lead | Issue is prioritized for sprint |
| Ready for BDD → BDD Complete | QA Engineer | BDD scenarios written and failing |
| BDD Complete → In Development | Developer | Developer starts implementation |
| In Development → In Review | Developer | PR created |
| In Review → In Development | Code Reviewer | Changes requested |
| In Review → QA Validation | Code Reviewer | PR approved |
| QA Validation → In Development | QA Engineer | BDD tests failing or security issues |
| QA Validation → Ready to Deploy | QA Engineer | All tests pass, security clean |
| Ready to Deploy → Done | SRE/Platform | Merged to main |

---

## Step 8: Project Dashboard (README)

Create a project README with key metrics:

1. In the project, click **⋮** → **Settings**
2. Scroll to **README**
3. Click **Add README**
4. Add this content:

```markdown
# Dioxide Development Project

## Current Sprint: v0.1 Walking Skeleton

**Target:** Installable package with basic container and provider functionality
**Timeline:** 2 weeks (2025-10-21 to 2025-11-04)
**Goal:** Developer can install and use in <15 minutes

## Sprint Progress

- [ ] 0/12 issues completed
- [ ] 0/7 BDD scenarios passing

## Key Metrics

**Velocity:** 0 story points completed
**Burndown:** On track / Behind / Ahead
**Blockers:** 0

## Links

- [Product Requirements](https://github.com/mikelane/dioxide/blob/main/docs/PRD.md)
- [Sprint Plan](https://github.com/mikelane/dioxide/blob/main/docs/SPRINT_PLAN.md)
- [Recommendations](https://github.com/mikelane/dioxide/blob/main/docs/RECOMMENDATIONS.md)

## Quick Actions

- [Create Issue](https://github.com/mikelane/dioxide/issues/new/choose)
- [Create PR](https://github.com/mikelane/dioxide/compare)
- [View Milestones](https://github.com/mikelane/dioxide/milestones)
```

---

## Step 9: Team Notifications

Set up notifications for the team:

1. **Watch the repository:** Click **Watch** → **All Activity**
2. **Subscribe to project:** Click **⋮** → **Settings** → **Notifications**
3. **Configure issue mentions:** GitHub Settings → Notifications → Participating

---

## Step 10: Initial Sprint Setup

Before starting Sprint 1, ensure:

### Day 0 (Project Setup - Today)
- [ ] GitHub Project created and configured
- [ ] All issues added to project
- [ ] Issues prioritized and assigned to Sprint 1
- [ ] Team has access and notifications configured

### Day 1 (Sprint Start)
- [ ] Sprint kickoff meeting (review sprint plan)
- [ ] Assign issues to team members
- [ ] Move first issues to "Ready for BDD"
- [ ] Begin infrastructure work (#7, #8, #9, #15)

---

## Daily Workflow

### Morning Standup (Async)
Each team member updates their issues:
- Move current issue to appropriate status
- Add comment with progress update
- Flag any blockers

### Pull Request Workflow
1. Developer creates PR
2. Link PR to issue (use keywords: "Closes #10")
3. Issue automatically moves to "In Review"
4. Code Reviewer reviews within 24 hours
5. QA Engineer validates after approval
6. SRE/Platform merges when ready

### Issue Updates
- Update issue with progress comments daily
- Use checkboxes in issue description for sub-tasks
- Tag blockers with `status: blocked` label
- Close issue when fully complete (BDD passes, merged, documented)

---

## Metrics to Track

### Sprint Metrics (Update Weekly)
- **Velocity:** Story points completed per week
- **Burndown:** Issues remaining vs. time remaining
- **Cycle Time:** Average time from "Ready for BDD" to "Done"
- **Blockers:** Count and duration of blockers

### Quality Metrics (Continuous)
- **BDD Pass Rate:** Percentage of BDD scenarios passing
- **Code Coverage:** Percentage of code covered by tests
- **Review Time:** Average time for PR approval
- **Bug Count:** Number of bugs found in QA

### Project Health (Monthly)
- **Community Engagement:** Stars, forks, issues from community
- **Downloads:** PyPI download count
- **Contributors:** Number of active contributors
- **Documentation:** Pages of documentation written

---

## Tips for Success

1. **Keep the board updated:** Move issues promptly, don't let them stagnate
2. **Use comments liberally:** Document decisions and blockers in issue comments
3. **Link PRs to issues:** Use "Closes #X" in PR description for auto-linking
4. **Review often:** Check the Sprint Board daily to stay aligned
5. **Celebrate wins:** Mark issues as Done and celebrate progress
6. **Retrospect weekly:** What went well? What to improve?

---

## Troubleshooting

### Issue not showing in project
- Check if issue is assigned to project (click "Projects" in issue sidebar)
- Verify project filters aren't excluding the issue
- Try refreshing the browser

### Can't move issue between columns
- Check if you have write access to the project
- Verify the Status field is configured correctly
- Try using the Status dropdown in the issue details

### Automation not working
- Check project settings → Workflows
- Verify the workflow is enabled
- Check if the trigger conditions are met

---

## Next Steps

After completing this setup:

1. ✅ Review this document
2. ✅ Create the GitHub Project following steps above
3. ✅ Add all issues to project
4. ✅ Configure views and fields
5. ✅ Invite team members
6. 🚀 Begin Sprint 1!

---

## Questions?

If you have questions about the project setup, create an issue with the `question` label or discuss in GitHub Discussions.

**Happy Building! 🚀**
