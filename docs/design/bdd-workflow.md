# BDD Workflow with Tag-Based CI Enforcement

This document describes the BDD (Behavior-Driven Development) workflow using Gherkin feature files
with tag-based CI enforcement. The workflow ensures test-first development discipline through
automated checks.

## Tagging System

### `@issue-XX` - Links Tests to GitHub Issues

Every new feature or bugfix should have its BDD tests tagged with the corresponding issue number:

```gherkin
@issue-42
Feature: User authentication
  As a user
  I want to log in securely
  So that I can access my account

  Scenario: Successful login with valid credentials
    Given a registered user with email "user@example.com"
    When they submit valid credentials
    Then they are redirected to the dashboard
```

**Multiple issues can share a tag** if they're related:

```gherkin
@issue-42 @issue-45
Scenario: Password reset sends email
```

### `@wip` - Marks Work-In-Progress Tests

Tests that are written but not yet passing should be tagged `@wip`:

```gherkin
@issue-42 @wip
Scenario: Two-factor authentication
  Given a user with 2FA enabled
  When they enter their password
  Then they are prompted for a 2FA code
```

**The `@wip` tag is a forcing function**: CI will fail if you try to merge with `@wip` present
on your issue's tests. This ensures developers don't forget to complete their implementation.

## Branch Naming Convention

Branch names must include the issue number for CI to track feature acceptance:

| Pattern | Example | Issue Extracted |
|---------|---------|-----------------|
| `issue-XX-description` | `issue-42-add-auth` | 42 |
| `feat/issue-XX-description` | `feat/issue-42-add-auth` | 42 |
| `fix/issue-XX-description` | `fix/issue-42-fix-login` | 42 |

**Non-issue branches** (e.g., `docs-update-readme`) skip Feature Acceptance checks gracefully.

## CI Jobs

### 1. BDD Regression Suite (Required)

- **Command**: `uv run behave --tags="not @wip"`
- **Purpose**: Ensures all completed features still pass
- **Runs**: All tests except those tagged `@wip`
- **Status**: Required for merge

### 2. BDD Feature Acceptance (Required)

- **Command**: `uv run behave --tags="@issue-XX"`
- **Purpose**: Validates current PR's feature tests pass
- **Behavior**:
  - Extracts issue number from branch name
  - **FAILS if `@wip` tag present** on issue's tests
  - Skips gracefully for non-issue branches
- **Status**: Required for merge

### 3. BDD Pending Features (Informational)

- **Command**: `uv run behave --tags="@wip"`
- **Purpose**: Shows progress on work-in-progress features
- **Status**: Non-blocking (`continue-on-error: true`)

## Developer Workflow

### 1. QA/PM Writes Failing Scenarios

Before implementation begins, write Gherkin scenarios tagged with both `@issue-XX` and `@wip`:

```gherkin
@issue-123 @wip
Feature: Shopping cart checkout
```

### 2. Developer Implements Until Tests Pass

Work through TDD cycles until all scenarios pass locally:

```bash
# Run just your issue's tests
uv run behave --tags="@issue-123"
```

### 3. Developer Removes `@wip` Tag

Once all scenarios pass, remove the `@wip` tag:

```gherkin
@issue-123
Feature: Shopping cart checkout
```

### 4. PR Passes CI

- Regression Suite: Ensures you didn't break existing features
- Feature Acceptance: Verifies your issue's tests pass and `@wip` is removed

## Local Testing Commands

```bash
# Run all BDD tests (excluding WIP)
uv run behave --tags="not @wip"

# Run tests for a specific issue
uv run behave --tags="@issue-123"

# Run WIP tests (expected to fail)
uv run behave --tags="@wip"

# Run tests with both tags (check what's still WIP for an issue)
uv run behave --tags="@issue-123" --tags="@wip"

# Dry run to see what would execute
uv run behave --dry-run --tags="@issue-123" --format=plain

# Verbose output with scenario names
uv run behave --tags="not @wip" --format=pretty
```

## Foundational Tests

The existing feature files in `features/` are **foundational tests** that predate this workflow:

- `basic_container.feature`
- `component-decorator.feature`
- `container-scan.feature`
- `dependency-injection.feature`
- `manual-registration.feature`
- `provider_registration.feature`
- `singleton-caching.feature`
- `type-safety.feature`

These remain **untagged** and always run in the Regression Suite. They're not tied to specific
issues and serve as the baseline for container functionality.

## Common Scenarios

### Scenario: Docs-only PR

Branch: `docs-update-api-guide`

- BDD Regression Suite: Runs (verifies no features broke)
- BDD Feature Acceptance: Skips (no issue number in branch)
- BDD Pending: Runs (informational)

### Scenario: Feature PR with WIP tests

Branch: `issue-42-add-caching`
Tests: Tagged `@issue-42 @wip`

- BDD Regression Suite: Passes (WIP excluded)
- BDD Feature Acceptance: **FAILS** (WIP tag detected)
- BDD Pending: Shows the WIP scenarios

**Resolution**: Complete implementation and remove `@wip` tag.

### Scenario: Feature PR ready to merge

Branch: `issue-42-add-caching`
Tests: Tagged `@issue-42` (no @wip)

- BDD Regression Suite: Passes
- BDD Feature Acceptance: Passes (tests exist and pass)
- BDD Pending: Passes (no WIP tests)

**Result**: PR is ready to merge.

### Scenario: Refactoring PR (no new features)

Branch: `issue-50-refactor-container`
Tests: No new tests (existing tests cover behavior)

- BDD Regression Suite: Passes (verifies refactor didn't break anything)
- BDD Feature Acceptance: Skips (no tests tagged with @issue-50)
- BDD Pending: Passes

**Result**: PR is ready to merge (refactoring validated by regression suite).

## Troubleshooting

### "Feature Acceptance failed - @wip tag detected"

Your issue's tests still have `@wip`. Either:
1. Complete the implementation until tests pass
2. Remove `@wip` tag from passing scenarios

### "No tests tagged with @issue-XX"

This is OK for:
- Refactoring (behavior covered by existing tests)
- Infrastructure changes (no user-facing features)
- Documentation updates

If you expected tests, check your tag spelling matches the issue number.

### "Regression Suite failed"

You broke an existing feature. Check which scenarios failed and fix the regression before merging.
