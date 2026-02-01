# Documentation UX BDD Tests

This directory contains BDD acceptance tests for dioxide documentation UX.
These tests are designed to **FAIL** against current documentation, validating
that improvements defined in Epic #366 are needed.

## Purpose

These tests verify that developers can find answers quickly through the
documentation. Each test represents a user story:

1. **Quickstart** - New user finds working code in under 30 seconds
2. **Service vs Adapter** - Developer finds decision guidance for decorators
3. **Why Dioxide** - Skeptic finds justification and comparison
4. **Testing Patterns** - Tester finds fakes-at-seams philosophy and fixtures
5. **Design Decisions** - Contributor finds ADRs and architecture docs
6. **Error Messages** - Errors include documentation URLs for troubleshooting

## Running Tests

### Prerequisites

```bash
# Install dependencies
uv sync --group dev --group docs-ux

# Install Playwright browsers
uv run playwright install chromium

# Build documentation
uv run sphinx-build -b html docs docs/_build/html
```

### Run All Tests (Local Docs)

```bash
uv run pytest tests/docs_ux/ -v
```

### Run Specific Scenario

```bash
# By marker
uv run pytest tests/docs_ux/ -v -m quickstart
uv run pytest tests/docs_ux/ -v -m testing

# By keyword
uv run pytest tests/docs_ux/ -v -k "service_adapter"
```

### Run Against HTTP Server (Full Search Testing)

Sphinx search requires HTTP. For full search testing:

```bash
# Terminal 1: Start HTTP server
uv run python -m http.server -d docs/_build/html 8000

# Terminal 2: Run tests with HTTP URL
DOCS_URL=http://localhost:8000 uv run pytest tests/docs_ux/ -v
```

### Run Against ReadTheDocs (Production)

```bash
DOCS_URL=https://dioxide.readthedocs.io/en/latest uv run pytest tests/docs_ux/ -v
```

## Expected Behavior

**All tests should FAIL** against current documentation. This validates that:

1. The acceptance criteria in Epic #366 represent real gaps
2. The blocked issues (#373-#378) will make measurable improvements
3. When issues are completed, tests will turn green

## Test Files

```
tests/docs_ux/
  README.md              # This file
  __init__.py
  conftest.py            # Pytest fixtures and shared setup
  features/
    docs_navigation.feature   # Gherkin scenarios
  step_defs/
    __init__.py
    test_docs_navigation.py   # Step implementations
```

## Writing New Tests

1. Add scenario to `features/docs_navigation.feature` using Gherkin syntax
2. Add step definitions in `step_defs/test_docs_navigation.py`
3. Run to verify test fails (TDD approach)
4. Implement documentation changes
5. Verify test passes

## CI Integration

These tests require Playwright which needs browser installation. For CI:

```yaml
- name: Install Playwright
  run: uv run playwright install chromium --with-deps

- name: Build Docs
  run: uv run sphinx-build -b html docs docs/_build/html

- name: Run Docs UX Tests
  run: uv run pytest tests/docs_ux/ -v
```

## Troubleshooting

### "Search input not found"

Sphinx search requires JavaScript, which doesn't work with `file://` URLs.
Use HTTP server: `uv run python -m http.server -d docs/_build/html 8000`

### "Documentation not available"

Build docs first: `uv run sphinx-build -b html docs docs/_build/html`

### Playwright issues

Reinstall browsers: `uv run playwright install chromium --with-deps`
