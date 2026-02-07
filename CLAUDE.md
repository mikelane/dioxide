# CLAUDE.md

This file provides guidance to Claude Code when working on the dioxide codebase.

## Project Overview

**dioxide** is a declarative dependency injection framework for Python that makes clean architecture simple. It combines:
- **Hexagonal Architecture API** - `@adapter.for_()` and `@service` decorators with type hints
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability
- **Rust-backed core** - Correctness guarantees (circular dependency detection, graph validation) via PyO3

**History**: The package was renamed from `rivet_di` to `dioxide`. Legacy `rivet_di` references in the codebase should be updated to `dioxide`.

**v1.0.0 STABLE**: MLP (Minimum Loveable Product) complete. Hexagonal architecture API, lifecycle management, circular dependency detection, performance benchmarking, framework integrations (FastAPI, Flask, Celery, Click, Django, Ninja), and comprehensive testing guide all implemented. Active development continues on post-MLP features (lazy discovery, strict mode, scan planning, request scoping).

## Design Principles: The North Star

**CRITICAL**: Before making ANY architectural, API, or design decisions, consult **`docs/design-principles.md`**.

The Design Principles document is the **canonical design reference** for Dioxide. It defines:
- **The North Star**: Make the Dependency Inversion Principle feel inevitable
- **Guiding Principles**: 7 core principles (type-safe, explicit, fails fast, etc.)
- **Core API Design**: `@adapter.for_()`, `@service`, `Profile` class, container, lifecycle
- **Testing Philosophy**: Fakes at the seams, NOT mocks
- **What We're NOT Building**: Explicit exclusions list for MLP scope

**Key principle:** If design-principles.md says not to build something for MLP, don't build it. Simplicity over features.

## Quick Reference Commands

### Setup
```bash
uv venv && source .venv/bin/activate
uv sync --group dev
maturin develop
pre-commit install
```

### Testing (pytest)
```bash
uv run pytest tests/                                    # All tests
uv run pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch  # With coverage
uv run pytest tests/ -k "lifecycle"                     # Pattern match
uv run pytest tests/benchmarks/ --benchmark-only        # Benchmarks
```

### Testing (BDD/Behave)
```bash
uv run behave --tags="not @wip"                         # Regression suite (CI default)
uv run behave --tags="@issue-123"                       # Tests for specific issue
uv run behave --tags="@wip"                             # WIP tests (expected to fail)
uv run behave --tags="@issue-123" --tags="@wip"         # WIP tests for specific issue
uv run behave --dry-run --tags="@issue-123"             # Preview what would run
```

### Code Quality
```bash
ruff format python/ && cargo fmt                        # Format
ruff check python/ --fix && isort python/               # Lint Python
cargo clippy --all-targets --all-features -- -D warnings -A non-local-definitions  # Lint Rust
mypy python/                                            # Type check
```

### Building
```bash
maturin develop          # Dev build
maturin develop --release # Release build
maturin build            # Build wheel
```

### Documentation
```bash
uv sync --group docs
uv run sphinx-build -b html docs docs/_build/html
./scripts/docs-serve.sh  # Live reload server
```

## Repository Structure

```
dioxide/
├── python/dioxide/         # PUBLIC Python API
│   ├── __init__.py          # Package exports
│   ├── container.py         # Container with profile-based scanning
│   ├── adapter.py           # @adapter.for_() decorator
│   ├── services.py          # @service decorator
│   ├── lifecycle.py         # @lifecycle decorator
│   ├── profile_enum.py      # Profile class (extensible, type-safe)
│   ├── scope.py             # Scope enum (SINGLETON, FACTORY)
│   ├── exceptions.py        # Custom exceptions (incl. SideEffectWarning)
│   ├── testing.py           # Test utilities (fresh_container)
│   ├── fastapi.py           # FastAPI integration
│   ├── flask.py             # Flask integration
│   ├── celery.py            # Celery integration
│   ├── click.py             # Click CLI integration
│   ├── django.py            # Django integration
│   ├── ninja.py             # Django Ninja integration
│   ├── _registry.py         # Internal registration system
│   ├── _dioxide_core.pyi    # Rust binding type stubs
│   └── py.typed             # PEP 561 marker
├── rust/src/                # PRIVATE Rust implementation
│   └── lib.rs               # PyO3 bindings and container logic
├── tests/                   # Python integration tests
│   ├── type_checking/       # mypy type safety tests
│   ├── benchmarks/          # Performance benchmark tests
│   └── fixtures/            # Test fixtures
├── features/                # BDD/Behave acceptance tests
│   ├── steps/               # Step definitions
│   └── *.feature            # Gherkin feature files
├── examples/                # Example applications
│   ├── fastapi/             # FastAPI integration example
│   ├── flask/               # Flask integration example
│   ├── celery/              # Celery integration example
│   ├── click/               # Click CLI example
│   ├── migrations/          # Migration examples
│   └── patterns/            # Common DI patterns
├── demos/                   # GitHub Pages demo site
│   ├── scripts/             # Recording + narration toolchain
│   └── narration-scripts/   # Voiceover script templates
├── docs/                    # Sphinx documentation (ReadTheDocs)
│   ├── design-principles.md # Canonical design specification
│   ├── TESTING_GUIDE.md     # Testing philosophy and patterns
│   ├── testing/             # Testing docs section
│   ├── user_guide/          # User guide
│   ├── api/                 # API reference
│   ├── integrations/        # Framework integration docs
│   ├── troubleshooting/     # Troubleshooting guides
│   ├── cookbook/             # Recipes and patterns
│   ├── guides/              # How-to guides
│   └── design/              # ADRs and design docs
├── .github/workflows/       # CI/CD pipelines
│   ├── ci.yml               # Main CI (test matrix, lint, BDD)
│   └── deploy-demos.yml     # GitHub Pages deployment
├── .claude/rules/           # Modular guidelines (see below)
└── CLAUDE.md                # This file
```

## Scan API (Post-MLP Features)

Recent additions to the container's `scan()` method:

```python
container = Container(profile=Profile.PRODUCTION)

# Basic scan
container.scan("myapp")

# Scan with statistics
stats = container.scan("myapp", stats=True)  # Returns ScanStats

# Strict mode — detect side effects during import
container.scan("myapp", strict=True)  # Raises SideEffectWarning on side effects

# Lazy discovery — register adapters without importing modules
container.scan("myapp", lazy=True)  # Defers imports until resolution

# Preview what scan would import
plan = container.scan_plan("myapp")  # Returns ScanPlan (no side effects)
```

Key types: `ScanStats`, `ScanPlan`, `AdapterInfo`, `ServiceInfo`, `SideEffectWarning`

## Working with Claude Code

When working on this project, follow these requirements **in order**:

1. **Consult Design Principles** - Check `docs/design-principles.md` before design decisions
2. **Ensure issue exists** - ALL work must have a GitHub issue - NO EXCEPTIONS
3. **Create feature branch** - Never work directly on main
4. **Always follow TDD** - Write tests before implementation
5. **Test through Python API** - Don't write Rust unit tests
6. **Check coverage** - Run coverage before committing (≥90% overall, ≥95% branch)
7. **Use Describe*/it_* pattern** - Follow BDD test structure
8. **Keep tests simple** - No logic in tests
9. **Update documentation** - ALL code changes MUST include doc updates
10. **Clean commits** - No attribution lines, always reference issue number
11. **Update issue** - Keep the GitHub issue updated as you work
12. **Create Pull Request** - ALL changes MUST go through PR process
13. **Close properly** - Use "Fixes #N" in PR description to auto-close issue

**CRITICAL**:
- Step 2 (Issue exists) is MANDATORY - no issue means no work
- Step 4 (TDD) and 9 (Documentation) are NOT optional
- Step 12 (Pull Request) is ENFORCED by branch protection

## Modular Guidelines

For detailed guidelines, see `.claude/rules/`:

| Topic | Rule File | Summary |
|-------|-----------|---------|
| Architecture | `architecture.md` | Python = public API, Rust = private implementation |
| TDD Workflow | `tdd-workflow.md` | Uncle Bob's Three Rules, red-green-refactor |
| Testing | `testing.md` + `testing-summary.md` | Describe*/it_* pattern, no logic in tests |
| Issue Tracking | `issue-tracking.md` | All work needs a GitHub issue |
| Pull Requests | `pull-requests.md` | All changes go through PRs |
| Documentation | `documentation.md` | Docs are NOT optional |
| Git Commits | `git-commits.md` | Conventional commits with issue reference |
| Design Principles | `mlp-vision-summary.md` | 7 guiding principles summary |

### BDD Workflow

The project uses Behave for acceptance testing with Gherkin feature files in `features/`. See `docs/design/bdd-workflow.md` for full details.

Key conventions:
- Tag features with `@issue-NNN` to link to GitHub issues
- Use `@wip` for tests under development (expected to fail)
- CI runs `--tags="not @wip"` for the regression suite
- BDD tests are separate from pytest unit tests

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python config: maturin build, pytest (Describe*/it_*), coverage, behave |
| `Cargo.toml` | Rust config: pyo3, petgraph |
| `.pre-commit-config.yaml` | Quality gates: ruff, mypy, cargo clippy, pytest coverage |
| `.github/workflows/ci.yml` | CI pipeline: test matrix, lint, BDD, docs build |
| `.gitattributes` | Binary file handling (MP4, GIF), line ending normalization |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Maturin build issues | `cargo clean && maturin develop --release` |
| Import errors after Rust changes | `maturin develop` |
| Test discovery issues | Check `pyproject.toml`: `python_classes = ["Describe*", "Test*"]` |
| Coverage not running | Check `.pre-commit-config.yaml` includes coverage args |
| `SideEffectWarning` during strict scan | Expected behavior — strict mode flags side effects during import |
| mypy error on bare `return` | Use `return None` explicitly in functions returning `X \| None` |
| Worktree missing dependencies | Run `uv sync --all-groups && maturin develop` in the worktree |

## Reference Documentation

| Document | Purpose |
|----------|---------|
| `docs/design-principles.md` | **CANONICAL DESIGN DOCUMENT** - The north star |
| `README.md` | Project overview and quick start |
| `CHANGELOG.md` | Release history and breaking changes |
| `COVERAGE.md` | Coverage requirements and documentation |
| `docs/TESTING_GUIDE.md` | Testing philosophy (fakes > mocks) |
| `docs/design/bdd-workflow.md` | BDD conventions, Gherkin tags, CI jobs |
| `docs/design/ADR-001-container-architecture.md` | Container architecture decisions |
| `docs/design/ADR-002-pyo3-binding-strategy.md` | PyO3 binding strategy |
| `demos/README.md` | Demo video recording pipeline |

## Tool Usage

- Use **uv** for Python tooling: `uv run`, `uv sync`, `uv add`
- Do NOT use `uv pip` commands
- Use groups/extras where appropriate: `uv sync --group dev`

## Profile Class API

Profile is an **extensible str subclass**, NOT a StrEnum. This enables custom profiles while maintaining type safety:

```python
# Built-in profiles (class constants)
Profile.PRODUCTION  # == 'production'
Profile.TEST        # == 'test'
Profile.DEVELOPMENT # == 'development'
Profile.STAGING     # == 'staging'
Profile.CI          # == 'ci'
Profile.ALL         # == '*'

# Custom profiles are first-class citizens
INTEGRATION = Profile('integration')
LOAD_TEST = Profile('load-test')

# Type-safe usage
@adapter.for_(Port, profile=INTEGRATION)
@adapter.for_(Port, profile=[LOAD_TEST, Profile.STAGING])
```

**Patterns that DON'T work (StrEnum remnants):**

| Wrong | Why | Correct |
|-------|-----|---------|
| `profile.value` | No `.value` attribute | `str(profile)` or just use `profile` |
| `profile.name` | No `.name` attribute | Not available |
| `for p in Profile:` | Not iterable | Use explicit list of constants |

## Worktree Cleanup

After merging a PR, clean up worktrees from the **main repo directory**, not from inside the worktree:

```bash
cd /Users/mikelane/dev/dioxide  # Main repo, NOT inside worktree
safe-worktree-remove .worktrees/issue-XXX-name
```

**Never** run `git worktree remove` directly - use `safe-worktree-remove` which prevents self-deletion errors.

## Merging PRs

### CI-Aware Merge

Don't poll CI manually. Use `--watch` to wait for CI then merge:

```bash
gh pr checks <number> --watch && gh pr merge <number> --squash --delete-branch
```

### Self-Authored PRs

For self-authored PRs where worktree branch deletion may fail:

```bash
gh pr merge <number> --squash  # Omit --delete-branch
# Then manually clean up:
safe-worktree-remove .worktrees/issue-XXX-name
```

**Note**: GitHub prohibits self-approval. Use `gh pr review --comment` for self-authored PRs, not `--approve`.
