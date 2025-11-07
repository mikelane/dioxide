# Label Guide

This guide provides detailed guidance on when and how to use labels in the dioxide repository.

## Table of Contents

- [Label Philosophy](#label-philosophy)
- [Type Labels](#type-labels)
- [Priority Labels](#priority-labels)
- [Status Labels](#status-labels)
- [Area Labels](#area-labels)
- [Meta Labels](#meta-labels)
- [Label Combinations](#label-combinations)
- [Common Scenarios](#common-scenarios)

## Label Philosophy

**Goals:**
1. **Clarity** - Labels make issue state immediately obvious
2. **Searchability** - Filter issues by type, priority, area
3. **Automation** - Workflows use labels to trigger actions
4. **Communication** - Set expectations (SLAs tied to priority)

**Principles:**
- Every issue should have **at least one type label**
- Most issues should have **a priority label** (exceptions: questions, docs)
- Status labels are **managed by automation and maintainers**
- Area labels help **route issues to domain experts**

## Type Labels

### type: bug

**Color:** `#d73a4a` (red)

**When to use:**
- Something is broken or not working as designed
- Crashes, errors, exceptions
- Unexpected behavior that contradicts documentation

**Examples:**
- "Container crashes when adding circular dependency"
- "Python bindings segfault on shutdown"
- "Memory leak in graph traversal"
- "Function returns incorrect result for negative numbers"

**Not for:**
- Missing features (use `type: feature`)
- Performance issues (use `type: performance`)
- Unclear documentation (use `type: docs`)

---

### type: feature

**Color:** `#a2eeef` (light blue)

**When to use:**
- Entirely new functionality that doesn't exist
- New API surface
- New capabilities

**Examples:**
- "Add support for weighted edges"
- "Implement async API for container operations"
- "Add JSON serialization for graph"
- "Support named tokens in lifecycle management"

**Not for:**
- Improvements to existing features (use `type: enhancement`)
- API redesigns (use `type: enhancement` or `type: refactor`)

---

### type: enhancement

**Color:** `#84b6eb` (blue)

**When to use:**
- Improvements to existing functionality
- Making something better, faster, or more convenient
- API changes that improve usability

**Examples:**
- "Make Container::add_node return &mut Node for chaining"
- "Improve error messages for lifecycle violations"
- "Add builder pattern for graph construction"
- "Support custom hash functions for node IDs"

**Not for:**
- Bug fixes (use `type: bug`)
- New features (use `type: feature`)
- Performance fixes (use `type: performance`)

---

### type: docs

**Color:** `#0075ca` (dark blue)

**When to use:**
- Documentation is missing
- Documentation is incorrect
- Documentation is unclear
- Examples are needed
- Docstrings incomplete

**Examples:**
- "README missing quickstart guide"
- "Container::resolve docstring incorrect"
- "Add examples for lifecycle management"
- "API reference outdated after v0.2.0"

**Always for:**
- Any pure documentation changes
- README updates
- Docstring improvements
- Guide additions

---

### type: refactor

**Color:** `#fbca04` (yellow)

**When to use:**
- Internal code improvements without behavior change
- Code cleanup
- Architecture improvements
- Reducing technical debt

**Examples:**
- "Extract graph algorithms into separate module"
- "Replace custom HashMap with standard library"
- "Simplify Container construction logic"
- "Remove deprecated internal APIs"

**Requirements:**
- Must not change external behavior
- Must not break existing tests
- Should improve maintainability or readability

---

### type: security

**Color:** `#b60205` (dark red)

**When to use:**
- Security vulnerabilities
- Unsafe code patterns
- Memory safety issues
- Potential DoS vectors

**Examples:**
- "Unbounded recursion allows stack overflow"
- "Missing input validation enables code injection"
- "Race condition in concurrent container access"

**Important:**
- For **critical vulnerabilities**, use [private security reporting](https://github.com/mikelane/dioxide/security/advisories/new)
- Always set `priority: critical` for security issues
- Never share exploits publicly before fix is released

---

### type: performance

**Color:** `#5319e7` (purple)

**When to use:**
- Optimization opportunities
- Slow operations
- Memory usage improvements
- Algorithm improvements

**Examples:**
- "Graph traversal is O(n²), should be O(n)"
- "Container::resolve clones unnecessarily"
- "Reduce allocations in hot path"
- "Cache expensive computations"

**Include:**
- Benchmarks showing the problem
- Profiling data if available
- Expected improvement

---

### type: question

**Color:** `#d876e3` (pink)

**When to use:**
- Usage questions
- Clarifications needed
- "How do I...?" questions
- API confusion

**Examples:**
- "How do I create a singleton with dependencies?"
- "What's the difference between transient and scoped?"
- "Can Container be used in async context?"

**Consider:**
- Use [GitHub Discussions](https://github.com/mikelane/dioxide/discussions) instead for open-ended questions
- Use this label only for specific, answerable questions

---

## Priority Labels

### priority: critical

**Color:** `#b60205` (dark red)

**SLA:** 4-hour acknowledgement, 24-hour resolution

**When to use:**
- Production-blocking bugs
- Security vulnerabilities
- Data loss issues
- System crashes

**Examples:**
- "Entire application crashes on startup"
- "SQL injection vulnerability in API"
- "Container deallocates memory while in use"

**Requirements:**
- Must have `type: bug` or `type: security`
- Include reproduction steps
- Describe production impact

---

### priority: high

**Color:** `#ff9800` (orange)

**SLA:** 1-day acknowledgement, 1-week resolution

**When to use:**
- Important bugs with workarounds
- Key features for upcoming release
- Significant performance issues

**Examples:**
- "Cannot use feature X without hacky workaround"
- "Major performance regression in v0.3.0"
- "API inconsistency blocks common use cases"

---

### priority: medium

**Color:** `#fbca04` (yellow)

**SLA:** 3-day acknowledgement, 2-week resolution

**When to use:**
- Standard bugs
- Nice-to-have features
- Minor performance improvements
- Most enhancements

**Examples:**
- "Error message unclear for common mistake"
- "Add convenience method for frequent operation"
- "Support additional data types in API"

**Default priority** for most issues.

---

### priority: low

**Color:** `#bfdadc` (light gray)

**SLA:** Best effort

**When to use:**
- Minor improvements
- Edge cases
- Cosmetic issues
- Nice-to-have enhancements

**Examples:**
- "Typo in debug output"
- "Improve formatting of error message"
- "Add example for rare use case"

---

## Status Labels

Status labels are typically managed by maintainers and automation.

### status: triage

**Color:** `#ededed` (gray)

**Automatically added when:** Issue is opened

**Meaning:** Issue needs maintainer review

**Removed when:** Issue triaged and moved to backlog or closed

---

### status: blocked

**Color:** `#000000` (black)

**When to use:**
- Issue cannot proceed due to dependency
- Waiting on external library
- Blocked by another issue

**Add comment explaining:** What is blocking and what unblocks

**Examples:**
- "Blocked by #123 - needs graph API redesign"
- "Blocked by upstream Rust RFC"
- "Waiting for Python 3.12 release"

---

### status: in-progress

**Color:** `#c2e0c6` (light green)

**When to use:**
- Someone is actively working on the issue
- PR is being drafted

**Add comment:** Who is working on it and expected timeline

---

### status: needs-review

**Color:** `#1d76db` (blue)

**When to use:**
- PR is open and ready for review
- Waiting on maintainer code review

**Automatically added by:** Some workflows

---

### status: waiting-on-author

**Color:** `#e99695` (light red)

**When to use:**
- Waiting for issue reporter to respond
- Waiting for PR author to address feedback

**Removed when:** Author responds or pushes changes

---

### status: stale

**Color:** `#fef2c0` (light yellow)

**Automatically added when:** Issue inactive for 90 days

**Meaning:** Issue will close in 14 days if no activity

**Removed when:** Anyone comments or updates the issue

---

## Area Labels

Area labels help route issues to domain experts.

| Label | Maintainer | Use For |
|-------|-----------|---------|
| `area: core` | @mikelane | Core container/graph |
| `area: python` | @mikelane | Python bindings |
| `area: rust` | @mikelane | Rust implementation |
| `area: api` | @mikelane | API design |
| `area: cli` | @mikelane | Command-line tools |
| `area: infrastructure` | @mikelane | CI/CD, deployment |
| `area: testing` | @mikelane | Test infrastructure |

**Use when:**
- Issue clearly affects specific component
- Helps with auto-assignment via CODEOWNERS
- Helps filter issues by domain

**Can combine multiple area labels** if issue spans multiple areas.

---

## Meta Labels

### good-first-issue

**Color:** `#7057ff` (purple)

**When to use:**
- Issue is well-defined
- Small scope (< 100 lines of code)
- Clear acceptance criteria
- Good for newcomers

**Examples:**
- "Add missing docstring to public function"
- "Fix typo in error message"
- "Add test for edge case"

**Requirements:**
- Detailed description
- Clear steps to implement
- No deep domain knowledge required

---

### help-wanted

**Color:** `#008672` (teal)

**When to use:**
- Maintainers would appreciate community help
- Non-critical but valuable
- Well-defined scope

**Often combined with** `good-first-issue` for newcomers.

---

### duplicate

**Color:** `#cfd3d7` (light gray)

**When to use:**
- Issue already reported elsewhere

**Always include:** Link to original issue in comment

**Example comment:**
> "Duplicate of #123. Closing in favor of the earlier report."

---

### wontfix

**Color:** `#ffffff` (white)

**When to use:**
- Issue is valid but won't be addressed
- Outside project scope
- Design decision not to support

**Always explain why** in closing comment.

---

### needs-reproduction

**Color:** `#fef2c0` (light yellow)

**When to use:**
- Bug report lacks reproduction steps
- Cannot reproduce the issue
- Need more information to investigate

**Example comment:**
> "Thanks for the report! Could you provide a minimal code example that reproduces this issue? I wasn't able to reproduce it with the information provided."

---

### breaking-change

**Color:** `#d73a4a` (red)

**When to use:**
- Change will break existing code
- API changes requiring migration
- Major version bump required

**Document:**
- What breaks
- How to migrate
- Why change is necessary

---

## Label Combinations

### Common Combinations

**Bug Fix (Critical):**
- `type: bug`
- `priority: critical`
- `area: core` (or relevant area)

**New Feature:**
- `type: feature`
- `priority: medium` or `priority: high`
- `area: *` (relevant area)

**Good First Issue:**
- `type: *` (any type)
- `good-first-issue`
- `help-wanted`
- `area: *` (helps newcomers know what to learn)

**Blocked Work:**
- `type: *`
- `priority: *`
- `status: blocked`

**Security Issue:**
- `type: security`
- `priority: critical`
- `area: *`

### Invalid Combinations

**Don't combine:**
- Multiple type labels (pick the most specific)
  - Exception: `type: security` + another type is okay
- Multiple priority labels (pick one)
- `type: bug` + `wontfix` (if it's truly a bug, we should fix it)

---

## Common Scenarios

### Scenario: User reports a crash

**Labels:**
- `type: bug`
- `priority: high` (if common) or `priority: critical` (if widespread)
- `area: core` (or relevant area)
- `status: triage` (automatic)

**Next steps:**
1. Validate with reproduction
2. Determine severity
3. Assign or mark `help-wanted`

---

### Scenario: User suggests new feature

**Labels:**
- `type: feature`
- `priority: medium` (default) or adjust based on impact
- `area: *` (relevant area)
- `status: triage` (automatic)

**Next steps:**
1. Discuss design in issue
2. Determine if in scope
3. Mark `help-wanted` if accepting contributions

---

### Scenario: Documentation is wrong

**Labels:**
- `type: docs`
- `priority: low` (usually) or `priority: medium` if impactful
- `good-first-issue` (if straightforward fix)
- `help-wanted`

---

### Scenario: Performance issue

**Labels:**
- `type: performance`
- `priority: medium` or `priority: high` (if severe regression)
- `area: *` (relevant area)

**Require:** Benchmarks or profiling data

---

### Scenario: Issue inactive for 90 days

**Labels:**
- (existing labels)
- `status: stale` (automatic)

**Action:** Automation posts comment, closes after 14 more days if no response

---

## Label Management

### Syncing Labels

Labels are defined in `.github/scripts/sync-labels.sh`.

**Run script:**
```bash
cd .github/scripts
./sync-labels.sh --dry-run  # Preview changes
./sync-labels.sh            # Apply changes
```

**Workflow:** Periodic script runs keep labels consistent.

### Adding New Labels

1. Add to `sync-labels.sh` in appropriate category
2. Include name, color, description
3. Run `./sync-labels.sh` to create
4. Update this guide with usage instructions

### Deprecating Labels

1. Move issues to new label
2. Remove from `sync-labels.sh`
3. Delete label via GitHub UI or API
4. Update this guide

---

## Questions?

For questions about labels:
- 📖 Read [Issue Lifecycle Documentation](issue-lifecycle.md)
- 💬 Ask in [GitHub Discussions](https://github.com/mikelane/dioxide/discussions)
- 🐛 Open issue with `type: question`

---

**Last Updated:** 2025-11-07
