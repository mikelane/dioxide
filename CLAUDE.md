# CLAUDE.md

This file provides guidance to Claude Code when working on the dioxide codebase.

## Project Overview

**dioxide** is a declarative dependency injection framework for Python that makes clean architecture simple. It combines:
- **Hexagonal Architecture API** - `@adapter.for_()` and `@service` decorators with type hints
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability
- **Rust-backed core** - Fast container operations via PyO3

**Note**: The package was recently renamed from `rivet_di` to `dioxide`.

**v1.0.0 STABLE**: MLP Complete! Hexagonal architecture API, lifecycle management, circular dependency detection, performance benchmarking, framework integrations (FastAPI, Flask, Celery, Click), and comprehensive testing guide all implemented.

## MLP Vision: The North Star

**CRITICAL**: Before making ANY architectural, API, or design decisions, consult **`docs/MLP_VISION.md`**.

The MLP Vision document is the **canonical design reference** for Dioxide. It defines:
- **The North Star**: Make the Dependency Inversion Principle feel inevitable
- **Guiding Principles**: 7 core principles (type-safe, explicit, fails fast, etc.)
- **Core API Design**: `@adapter.for_()`, `@service`, `Profile` enum, container, lifecycle
- **Testing Philosophy**: Fakes at the seams, NOT mocks
- **What We're NOT Building**: Explicit exclusions list for MLP scope

**Key principle:** If MLP_VISION.md says not to build something for MLP, don't build it. Simplicity over features.

## Quick Reference Commands

### Setup
```bash
uv venv && source .venv/bin/activate
uv sync --group dev
maturin develop
pre-commit install
```

### Testing
```bash
uv run pytest tests/                                    # All tests
uv run pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch  # With coverage
uv run pytest tests/ -k "lifecycle"                     # Pattern match
uv run pytest tests/benchmarks/ --benchmark-only        # Benchmarks
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
│   ├── profile_enum.py      # Profile enum (PRODUCTION, TEST, etc.)
│   ├── scope.py             # Scope enum (SINGLETON, FACTORY)
│   ├── exceptions.py        # Custom exceptions
│   ├── testing.py           # Test utilities (fresh_container)
│   ├── fastapi.py           # FastAPI integration
│   ├── flask.py             # Flask integration
│   ├── celery.py            # Celery integration
│   ├── click.py             # Click CLI integration
│   └── _registry.py         # Internal registration system
├── rust/src/                # PRIVATE Rust implementation
│   └── lib.rs               # PyO3 bindings and container logic
├── tests/                   # Python integration tests
│   ├── type_checking/       # mypy type safety tests
│   └── benchmarks/          # Performance benchmark tests
├── examples/                # Example applications
├── docs/                    # Documentation
│   ├── MLP_VISION.md        # Canonical design specification
│   ├── TESTING_GUIDE.md     # Testing philosophy and patterns
│   └── design/              # Architecture Decision Records
├── .claude/rules/           # Modular guidelines (see below)
└── CLAUDE.md                # This file
```

## Working with Claude Code

When working on this project, follow these requirements **in order**:

1. **Consult MLP Vision** - Check `docs/MLP_VISION.md` before design decisions
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
| MLP Vision | `mlp-vision-summary.md` | 7 guiding principles summary |

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python config: maturin build, pytest (Describe*/it_*), coverage |
| `Cargo.toml` | Rust config: pyo3, petgraph |
| `.pre-commit-config.yaml` | Quality gates: ruff, mypy, cargo clippy, pytest coverage |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Maturin build issues | `cargo clean && maturin develop --release` |
| Import errors after Rust changes | `maturin develop` |
| Test discovery issues | Check `pyproject.toml`: `python_classes = ["Describe*", "Test*"]` |
| Coverage not running | Check `.pre-commit-config.yaml` includes coverage args |

## Reference Documentation

| Document | Purpose |
|----------|---------|
| `docs/MLP_VISION.md` | **CANONICAL DESIGN DOCUMENT** - The north star |
| `README.md` | Project overview and quick start |
| `STATUS.md` | Current sprint status and progress |
| `ROADMAP.md` | Long-term vision |
| `docs/TESTING_GUIDE.md` | Testing philosophy (fakes > mocks) |
| `COVERAGE.md` | Coverage requirements and documentation |

## Tool Usage

- Use **uv** for Python tooling: `uv run`, `uv sync`, `uv add`
- Do NOT use `uv pip` commands
- Use groups/extras where appropriate: `uv sync --group dev`
