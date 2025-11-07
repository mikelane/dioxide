# Issue Lifecycle Documentation

This document describes the complete lifecycle of issues in the dioxide repository, from creation to resolution.

## Table of Contents

- [Overview](#overview)
- [Issue States](#issue-states)
- [Issue Labels](#issue-labels)
- [Workflow Stages](#workflow-stages)
- [Service Level Agreements (SLAs)](#service-level-agreements-slas)
- [Automation](#automation)
- [Best Practices](#best-practices)

## Overview

The dioxide project uses GitHub Issues and Projects to track bugs, features, enhancements, and other work. Our issue lifecycle is designed to provide transparency, clear expectations, and efficient resolution of issues.

**Key Principles:**

1. **Transparency**: Issue status is always clear through labels and project boards
2. **Predictability**: SLAs define expected response and resolution times
3. **Automation**: Workflows reduce manual overhead and ensure consistency
4. **Quality**: Issues are triaged, prioritized, and tracked systematically

## Issue States

Issues flow through these states:

```
┌──────────┐
│  Opened  │ (New issue created)
└────┬─────┘
     │
     ▼
┌──────────┐
│ Triage   │ (status: triage) - Needs review by maintainers
└────┬─────┘
     │
     ├───► [Closed: Duplicate/Invalid/Won't Fix]
     │
     ▼
┌──────────┐
│ Backlog  │ Validated, not yet scheduled
└────┬─────┘
     │
     ▼
┌──────────┐
│ Planned  │ Scheduled for development
└────┬─────┘
     │
     ▼
┌──────────┐
│ In Prog  │ (status: in-progress) - Actively being worked on
└────┬─────┘
     │
     ├───► [Blocked] (status: blocked) - Cannot proceed
     │
     ▼
┌──────────┐
│ Needs    │ (status: needs-review) - PR open, awaiting review
│ Review   │
└────┬─────┘
     │
     ├───► [Waiting on Author] (status: waiting-on-author)
     │
     ▼
┌──────────┐
│  Done    │ Issue closed, changes merged
└──────────┘
```

### State Transitions

| From | To | Trigger |
|------|----|----|
| Opened | Triage | Automatic (issue created) |
| Triage | Backlog | Maintainer validates issue |
| Triage | Closed | Duplicate/invalid/won't fix |
| Backlog | Planned | Maintainer schedules work |
| Planned | In Progress | Work begins |
| In Progress | Blocked | Dependency or blocker identified |
| In Progress | Needs Review | PR opened |
| Needs Review | Waiting on Author | Changes requested in PR |
| Waiting on Author | Needs Review | Author pushes updates |
| Needs Review | Done | PR merged |
| Blocked | In Progress | Blocker resolved |

## Issue Labels

dioxide uses a comprehensive label taxonomy to categorize and track issues.

### Type Labels (What kind of issue)

| Label | Description | Use Case |
|-------|-------------|----------|
| `type: bug` | Something isn't working | Crashes, errors, unexpected behavior |
| `type: feature` | New functionality | Entirely new capabilities |
| `type: enhancement` | Improvement to existing feature | Making existing features better |
| `type: docs` | Documentation improvements | README, API docs, guides |
| `type: refactor` | Code restructuring | Internal improvements without behavior change |
| `type: security` | Security vulnerability | Security issues (use private reporting for critical) |
| `type: performance` | Performance optimization | Speed or efficiency improvements |
| `type: question` | Question or support request | Usage questions, clarifications |

### Priority Labels (How urgent)

| Label | Description | Response SLA | Resolution SLA |
|-------|-------------|--------------|----------------|
| `priority: critical` | Blocking production, security vulnerability | 4 hours | 24 hours |
| `priority: high` | Important for next release | 1 day | 1 week |
| `priority: medium` | Should be addressed soon | 3 days | 2 weeks |
| `priority: low` | Nice to have | Best effort | Best effort |

### Status Labels (Where in workflow)

| Label | Description |
|-------|-------------|
| `status: triage` | Needs review and categorization |
| `status: blocked` | Cannot proceed, waiting on dependency |
| `status: in-progress` | Actively being worked on |
| `status: needs-review` | Implementation ready for review |
| `status: waiting-on-author` | Waiting for issue author response |
| `status: stale` | No activity for extended period |

### Area Labels (What part of system)

| Label | Description |
|-------|-------------|
| `area: core` | Core container/graph implementation |
| `area: python` | Python bindings and API |
| `area: rust` | Rust implementation |
| `area: api` | API design and endpoints |
| `area: cli` | Command-line interface |
| `area: ui` | User interface |
| `area: infrastructure` | CI/CD, deployment, infrastructure |
| `area: testing` | Test infrastructure and coverage |
| `area: lifecycle` | Lifecycle management |

### Meta Labels

| Label | Description |
|-------|-------------|
| `good-first-issue` | Good for newcomers |
| `help-wanted` | Extra attention needed |
| `duplicate` | Already reported elsewhere |
| `wontfix` | Will not be addressed |
| `needs-reproduction` | Cannot reproduce the issue |
| `breaking-change` | Will require major version bump |
| `dependencies` | Dependency updates |

See the [Label Guide](label-guide.md) for detailed guidance on when to use each label.

## Workflow Stages

### 1. Triage Stage

**Duration:** Within 1-3 business days for most issues

**Activities:**
- Maintainer reviews new issue
- Validates issue is legitimate (not spam, duplicate, or invalid)
- Adds appropriate labels (type, priority, area)
- Asks clarifying questions if needed
- Assigns to GitHub Project board

**Outcomes:**
- **Accept**: Issue moves to Backlog with appropriate labels
- **Reject**: Issue closed with explanation (duplicate, won't fix, invalid)
- **Clarify**: `status: waiting-on-author` label added, awaiting more information

### 2. Backlog Stage

**Description:** Validated issues that are not yet scheduled for work

**Activities:**
- Issue sits in backlog
- Community can discuss, refine, provide additional context
- Maintainers periodically review backlog for planning

**Stay Duration:** Variable (days to months)

### 3. Planned Stage

**Description:** Issues scheduled for upcoming development

**Activities:**
- Issue assigned to milestone or sprint
- Work estimates may be added
- Related issues linked

**Stay Duration:** Until development begins (typically < 2 weeks)

### 4. In Progress Stage

**Label:** `status: in-progress`

**Activities:**
- Developer actively working on implementation
- Regular updates posted to issue
- Questions/blockers raised early

**Best Practices:**
- Comment on issue when starting work (avoids duplicate effort)
- Push WIP branches to show progress
- Ask questions early if blocked

**Stay Duration:** Depends on complexity (hours to weeks)

### 5. Needs Review Stage

**Label:** `status: needs-review`

**Activities:**
- Pull request opened, linked to issue with "Closes #XXX"
- Automated checks run (CI, linting, tests)
- Code review by maintainers
- Changes requested/approved

**Stay Duration:** 1-3 business days for initial review

### 6. Done Stage

**Activities:**
- PR merged
- Issue automatically closed
- Changes included in next release
- User notified

## Service Level Agreements (SLAs)

dioxide aims to meet these response and resolution times:

### Acknowledgement SLAs

Time from issue creation to first maintainer response:

| Priority | Target | Actions |
|----------|--------|---------|
| Critical | **4 hours** | Immediate notification, start investigation |
| High | **1 business day** | Review, triage, assign priority |
| Medium | **3 business days** | Review and initial triage |
| Low | **Best effort** | Review when capacity allows |

### Resolution SLAs

Time from issue creation to resolution (merge or close):

| Priority | Target | Notes |
|----------|--------|-------|
| Critical | **24 hours** | Security vulnerabilities, production blockers |
| High | **1 week** | Important features/fixes for upcoming release |
| Medium | **2 weeks** | Standard feature/bug priority |
| Low | **Best effort** | Nice-to-have improvements |

**Important Notes:**

1. **These are targets, not guarantees** - dioxide is maintained by volunteers
2. **Complexity affects timeline** - Simple fixes faster than complex features
3. **Community involvement helps** - PRs from community accelerate resolution
4. **Stale issues** - Issues inactive for 90 days marked stale, closed after 104 days

### SLA Escalation

If your issue hasn't received a response within the SLA:

1. **Comment on the issue** with a polite reminder
2. **Check labels** - ensure correct priority is set
3. **Provide additional information** if requested
4. **Consider contributing** a PR if you can

## Automation

dioxide uses GitHub Actions to automate issue management:

### Issue Triage Automation

**Trigger:** Issue opened or reopened

**Actions:**
- Add `status: triage` label
- Add to "dioxide Development" project
- Post welcome comment with SLA expectations
- Auto-assign based on area label (via CODEOWNERS)

**Workflow:** `.github/workflows/issue-triage.yml`

### Stale Issue Management

**Trigger:** Daily at 00:00 UTC

**Actions:**
- Mark issues inactive for 90 days as `status: stale`
- Post comment asking if still relevant
- Close issues stale for 14 additional days (104 days total inactivity)

**Exempt Labels:**
- `status: blocked`
- `priority: critical`
- `priority: high`
- `good-first-issue`
- `help-wanted`

**Workflow:** `.github/workflows/stale-issues.yml`

### Auto-Close on PR Merge

**Trigger:** Pull request merged

**Actions:**
- Parse PR body/title for "Closes #XXX", "Fixes #YYY", "Resolves #ZZZ"
- Close referenced issues
- Add comment linking to closing PR

**Workflow:** `.github/workflows/auto-close-issues.yml`

### Issue Metrics & Reporting

**Trigger:** Monthly (1st of month at 09:00 UTC), or manual

**Actions:**
- Calculate metrics:
  - Issues opened/closed
  - Time to first response
  - Time to close
  - SLA compliance rates
- Generate report
- Create issue with monthly metrics

**Workflow:** `.github/workflows/issue-metrics.yml`

## Best Practices

### For Issue Reporters

**Do:**
- ✅ Search for existing issues before creating new ones
- ✅ Use appropriate issue templates
- ✅ Provide minimal reproducible examples for bugs
- ✅ Include environment details (versions, OS)
- ✅ Respond promptly when maintainers ask questions
- ✅ Keep discussion focused and respectful
- ✅ Mark issues as closed if you've resolved them

**Don't:**
- ❌ Create duplicate issues
- ❌ Hijack existing issues with unrelated problems
- ❌ Demand immediate fixes
- ❌ Post "+1" or "me too" comments (use 👍 reactions instead)
- ❌ Share sensitive information (credentials, private data)

### For Contributors

**Do:**
- ✅ Comment on issue before starting work
- ✅ Link PRs to issues with "Closes #XXX"
- ✅ Keep PRs focused on single issue
- ✅ Update issue status as work progresses
- ✅ Ask questions early if blocked
- ✅ Follow coding standards and test requirements

**Don't:**
- ❌ Start work without commenting (avoids duplicate effort)
- ❌ Create PRs without linked issues (for non-trivial changes)
- ❌ Mix multiple unrelated fixes in one PR
- ❌ Leave issues assigned if not actively working

### For Maintainers

**Do:**
- ✅ Respond within SLA targets
- ✅ Use labels consistently
- ✅ Keep project board up to date
- ✅ Close duplicates with links to original
- ✅ Provide clear explanations for rejections
- ✅ Acknowledge good first contributions
- ✅ Keep community guidelines positive

**Don't:**
- ❌ Let issues languish in triage
- ❌ Close issues without explanation
- ❌ Mix personal opinions with technical decisions
- ❌ Let SLA breaches go unnoticed

## Metrics & Transparency

dioxide tracks issue health through:

1. **Time to First Response** - How quickly maintainers respond
2. **Time to Close** - How long issues take to resolve
3. **Open Issue Count** - Total open issues by label
4. **SLA Compliance** - Percentage meeting SLA targets
5. **Stale Issue Rate** - Issues becoming inactive

Monthly reports posted as issues with `metrics` label.

## Questions?

For questions about issue lifecycle:
- 📖 Read the [Label Guide](label-guide.md)
- 💬 Ask in [GitHub Discussions](https://github.com/mikelane/dioxide/discussions)
- 🐛 Open an issue with `type: question` label

---

**Last Updated:** 2025-11-07
