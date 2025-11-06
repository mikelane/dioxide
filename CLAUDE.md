# CLAUDE.md

This file provides guidance to Claude Code when working on the dioxide codebase.

## Project Overview

**dioxide** is a fast, Rust-backed declarative dependency injection framework for Python that combines:
- **Declarative Python API** - Simple `@component` decorators and type hints
- **Rust-backed performance** - Fast container operations via PyO3
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability

**Note**: The package was recently renamed from `rivet_di` to `dioxide`. All references in code, tests, and documentation have been updated to use `dioxide`.

## Critical Architecture Decision: Public API vs Private Implementation

**IMPORTANT**: This is a hybrid Python/Rust project with a clear separation:

- **Python code** (`python/dioxide/`) is the **PUBLIC API** that users interact with
- **Rust code** (`rust/src/`) is the **PRIVATE implementation** for performance-critical operations

### Testing Strategy

**DO NOT write Rust unit tests directly.** The Rust code is an implementation detail. Instead:

1. Write comprehensive Python tests that exercise the Python API
2. The Python tests will exercise the Rust implementation through PyO3 bindings
3. Test through the public Python API to ensure correctness from the user's perspective
4. This approach correctly treats Rust as a private optimization detail

**Why?** The Rust code is compiled as a Python extension (.so file) via maturin. Users interact with the Python API, not the Rust code directly. Testing through Python ensures we test what users actually use.

See `COVERAGE.md` for detailed coverage documentation.

## Test Structure and Standards

### BDD-Style Test Pattern

Use the Describe*/it_* pattern for ALL tests:

```python
class DescribeComponentFeature:
    """Tests for @component decorator functionality."""

    def it_registers_the_decorated_class(self) -> None:
        """Decorator adds class to global registry."""
        @component
        class UserService:
            pass

        registered = _get_registered_components()
        assert UserService in registered
```

**pytest configuration** (in `pyproject.toml`):
```toml
python_classes = ["Describe*", "Test*"]
python_functions = ["it_*", "test_*"]
```

### Test Naming Standards

**DO**: Use declarative test names that can be false
```python
def it_returns_the_email_string_value(self) -> None:
    """Returns email as string."""
```

**DON'T**: Use "should" in test names
```python
def it_should_return_the_email_string_value(self) -> None:  # WRONG
    """This statement is ALWAYS true whether or not it returns email."""
```

**Why?** "It should return X" is always true as a statement, even when the test fails. "It returns X" can be false, making test failures meaningful.

### Test Simplicity

**CRITICAL**: Tests must be simple and contain no logic:

- ❌ NO branching (if/else)
- ❌ NO loops (for/while)
- ❌ NO complex logic
- ✅ YES to parametrization (if language supports it)
- ✅ YES to multiple simple tests instead of one complex test

**Why?** We never want to need a test suite for our tests.

## Development Workflow

### Test-Driven Development (TDD)

**MUST follow Kent Beck's Three Rules of TDD**:

1. Write a failing test first
2. Write minimal code to make the test pass
3. Refactor while keeping tests green

**DO NOT**:
- Write implementation code before tests
- Write multiple features without tests
- Skip the refactor step

If you find yourself writing Rust code without Python tests, **STOP** and write the tests first.

### Coverage Requirements

Run coverage before every commit:

```bash
pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch
```

**Requirements**:
- Overall coverage: ≥ 90%
- Branch coverage: ≥ 95%

The pre-commit hook enforces these requirements. See `COVERAGE.md` for detailed documentation.

## Common Development Commands

### Setup
```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e ".[dev]"

# Build Rust extension
maturin develop

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch

# Run specific test file
pytest tests/test_component.py

# Run tests matching a pattern
pytest tests/ -k "singleton"
```

### Code Quality
```bash
# Format code
ruff format python/
cargo fmt

# Lint Python
ruff check python/ --fix
isort python/

# Lint Rust
cargo clippy --all-targets --all-features -- -D warnings -A non-local-definitions

# Type check
mypy python/

# Run all quality checks
tox
```

### Building
```bash
# Build Rust extension for development
maturin develop

# Build release version
maturin develop --release

# Build wheel
maturin build
```

## Repository Structure

```
dioxide/
├── python/dioxide/       # Public Python API
│   ├── __init__.py        # Package exports
│   ├── container.py       # Container class with scan() for auto-discovery
│   ├── decorators.py      # @component decorator and registry
│   └── scope.py           # Scope enum (SINGLETON, FACTORY)
├── rust/src/              # Private Rust implementation
│   └── lib.rs             # PyO3 bindings and container logic
├── tests/                 # Python integration tests
│   ├── test_component.py           # @component decorator tests
│   └── test_rust_container_edge_cases.py  # Container behavior tests
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── pyproject.toml         # Python project configuration
├── Cargo.toml             # Rust project configuration
├── COVERAGE.md            # Coverage documentation
└── CLAUDE.md              # This file
```

## Key Components

### @component Decorator

The `@component` decorator marks classes for auto-discovery:

```python
from dioxide import component, Scope

@component  # Default: SINGLETON scope
class UserService:
    pass

@component(scope=Scope.FACTORY)  # Create new instance each time
class RequestHandler:
    pass
```

**Implementation**: `python/dioxide/decorators.py:13`

**How it works**:
1. Stores scope metadata on the class as `__dioxide_scope__` attribute
2. Adds the class to a global registry (`_component_registry`)
3. Container.scan() discovers all registered classes and creates auto-injecting factories

### Container.scan()

Auto-discovers and registers all `@component` decorated classes:

```python
container = Container()
container.scan()  # Finds all @component classes
controller = container.resolve(UserController)  # Dependencies auto-injected
```

**Features**:
- Finds all classes decorated with `@component`
- Inspects `__init__` type hints for dependencies
- Creates auto-injecting factory functions
- Registers with appropriate scope (SINGLETON or FACTORY)

**Implementation**: `python/dioxide/container.py:96`

**Important details**:
- SINGLETON components are wrapped in a Python-level singleton factory (using closure)
- FACTORY components are registered directly without singleton wrapping
- The Rust container caches ALL provider results in its singleton cache (see bug fix below)

### Rust Container

The Rust implementation (`rust/src/lib.rs`) provides:
- Fast provider registration and resolution
- Singleton caching (Factory providers are called once and cached)
- Type-based dependency lookup

**Recent Bug Fix**: Factory providers now correctly cache singleton results in the resolve() method.

## Configuration Files

### pyproject.toml

Key configurations:
- **Build system**: maturin for Rust extensions
- **Python source**: `python-source = "python"`
- **Module name**: `module-name = "dioxide._dioxide_core"`
- **Test discovery**: Describe*/it_* pattern
- **Coverage**: Branch coverage enabled

### .pre-commit-config.yaml

Pre-commit hooks enforce:
- Trailing whitespace removal
- YAML/TOML validation
- Ruff formatting and linting
- isort import sorting
- mypy type checking
- Cargo fmt and clippy for Rust
- pytest with ≥95% branch coverage

### Cargo.toml

Rust dependencies:
- **pyo3**: Python FFI bindings
- **petgraph**: Dependency graph algorithms (planned)

## Git Commit Standards

When committing code:

- ✅ Write clear, descriptive commit messages
- ✅ Focus on the "why" not just the "what"
- ❌ DO NOT add co-authored lines to Claude
- ❌ DO NOT add attribution lines to Claude
- ❌ DO NOT add generated-by comments

Keep commits clean and professional without unnecessary attribution.

## Work Tracking and Project Management

**IMPORTANT**: dioxide uses a three-tier tracking system to maintain visibility into project status and prevent work from being "lost" or forgotten.

### Three-Tier Tracking System

#### 1. STATUS.md (Weekly Updates - Single Source of Truth)

**Location**: `/STATUS.md`
**Update Frequency**: Every Friday (or after major milestones)
**Purpose**: Current sprint status at a glance

The STATUS.md file shows:
- Current milestone progress (e.g., "67% complete - 4 of 6 issues done")
- This week's completed work
- In-progress items
- Next actions
- Quality metrics (test coverage, CI status)
- Known blocking issues

**When to update**:
- Every Friday afternoon
- After completing major features
- Before sprint planning meetings
- When milestones change

#### 2. GitHub Milestone

**Location**: https://github.com/mikelane/dioxide/milestone/4 (0.0.1-alpha)
**Purpose**: Real-time progress tracking with visual progress bar

GitHub milestones show:
- Open vs. closed issues
- Visual progress percentage
- Due date (if set)
- Automatic updates when issues close

**How to use**:
- Assign ALL release-related issues to the milestone
- Close issues immediately when PRs merge
- GitHub updates progress automatically

#### 3. GitHub Project Board

**Location**: https://github.com/users/mikelane/projects/2
**Purpose**: Kanban-style visual workflow

Project board features:
- Drag-and-drop issue organization
- Visual columns (Backlog, In Progress, Done)
- Auto-moves issues when they close
- Links to milestones and issues

**When to use**:
- Planning what to work on next
- Reviewing overall project status
- Demonstrating progress to stakeholders

### Workflow: Starting New Work

1. **Pick an issue** from the project board or milestone
2. **Assign to yourself** on GitHub
3. **Move to "In Progress"** on project board (if using columns)
4. **Create branch**: `git checkout -b fix/issue-description` or `feat/issue-description`
5. **Follow TDD**: Write tests first, then implementation
6. **Commit with issue reference**: `git commit -m "fix: description (#22)"`

### Workflow: Completing Work

1. **Open PR** with `Fixes #22` in description
2. **Request review** if needed
3. **Merge PR** - GitHub auto-closes issue
4. **Issue moves to "Done"** on project board automatically
5. **Milestone progress updates** automatically

### Workflow: Weekly Status Update (Friday)

```bash
# 1. Review what was completed this week
gh issue list --milestone "0.0.1-alpha" --state closed --search "closed:>=$(date -v-7d +%Y-%m-%d)"

# 2. Check milestone progress
gh api repos/mikelane/dioxide/milestones/4 | jq '{open: .open_issues, closed: .closed_issues}'

# 3. Update STATUS.md
# - Move completed items from "In Progress" to "Completed This Week"
# - Update milestone progress percentage
# - Add new "Next Actions" for upcoming week
# - Update "Last Updated" date

# 4. Commit STATUS.md
git add STATUS.md
git commit -m "docs: weekly status update for $(date +%Y-%m-%d)"
```

### Planning Documents

Long-term planning documents (updated less frequently):

- **ROADMAP.md**: Long-term vision, updated quarterly
- **docs/0.0.1-ALPHA_SCOPE.md**: Release scope definition
- **docs/RELEASE_CHECKLIST_0.0.1-alpha.md**: Pre-release verification

These documents provide historical context but should NOT be the primary source of current status. Always check STATUS.md first.

### Why This System Works

**Problem solved**: Previously, completed work (like the singleton caching bug fix) wasn't reflected in planning documents, causing confusion about what still needed to be done.

**Solution**:
1. **GitHub milestone** shows real-time completion (auto-updates)
2. **STATUS.md** provides weekly snapshots (manual but quick)
3. **Project board** gives visual overview (auto-updates from issues)

All three stay synchronized with minimal manual effort:
- Issue closes → Milestone updates automatically
- Issue closes → Project board updates automatically
- Weekly STATUS.md update → Takes 5 minutes
- Planning docs → Only update when scope/vision changes

### Git Commit Messages and Issue Linking

**ALWAYS** reference the issue number in commit messages:

```bash
# Good - auto-links commit to issue
git commit -m "fix: singleton caching in Rust container (#19)"
git commit -m "feat: add manual provider registration (#20)"
git commit -m "docs: update API documentation (#24)"

# Bad - no link to issue
git commit -m "fix: singleton caching bug"
git commit -m "add new feature"
```

**Why?** GitHub automatically creates links between commits and issues, making it easy to see what code fixed which issue.

### Preventing Work from Being "Lost"

**Before this system**: Work was completed (singleton bug fixed) but planning docs still showed it as incomplete. PM recommended working on already-done tasks.

**With this system**:
1. Issue #19 closed → Milestone shows 3/6 complete
2. STATUS.md updated weekly → Shows #19 in "Completed This Week"
3. Project board → Shows #19 in "Done" column
4. Planning docs updated → Reference actual issue numbers

**Result**: No confusion about what's done vs. what's pending.

## Recent Development History

### @component Decorator Implementation
- Implemented flexible decorator supporting both `@component` and `@component(scope=...)`
- Global registry tracks decorated classes
- Supports SINGLETON (default) and FACTORY scopes

### Container.scan() Auto-Discovery
- Scans global registry for `@component` decorated classes
- Inspects `__init__` type hints to build dependency graph
- Creates auto-injecting factory functions
- Handles classes with/without __init__ parameters

### Rust Singleton Cache Bug Fix
- **Bug**: Factory providers were called multiple times instead of being cached
- **Fix**: Modified resolve() in rust/src/lib.rs to populate singleton cache for Factory providers
- **Test**: `tests/test_rust_container_edge_cases.py` verifies singleton behavior

### Coverage Achievement
- Achieved 100% branch coverage for Python code
- Added comprehensive test suite with edge cases
- Documented coverage approach for Python/Rust hybrid projects

## Release Process (Automated)

### Fully Automated Semantic Versioning

Dioxide uses automated semantic versioning via GitHub Actions:

1. **Commit to main** using [Conventional Commits](https://www.conventionalcommits.org/)
   - `feat:` triggers minor version bump (0.1.0 → 0.2.0)
   - `fix:`, `perf:`, `refactor:` trigger patch version bump (0.1.0 → 0.1.1)
   - `BREAKING CHANGE:` in commit body triggers major version bump (0.1.0 → 1.0.0)

2. **Semantic-release analyzes** commits and determines version bump

3. **Version synchronized** between:
   - Cargo.toml (Rust crate version)
   - Maturin reads from Cargo.toml for Python package

4. **Wheels built** for all platforms and architectures:
   - Linux (x86_64, ARM64)
   - macOS (x86_64 Intel, ARM64 Apple Silicon)
   - Windows (x86_64)
   - Python versions: 3.11, 3.13, 3.14

5. **Tested** on all target platforms with comprehensive smoke tests

6. **Published to PyPI** via Trusted Publishing (no API tokens)

7. **GitHub release created** with changelog

### Supported Platforms & Architectures

| Platform | x86_64 | ARM64/aarch64 |
|----------|--------|---------------|
| Linux    | ✅     | ✅            |
| macOS    | ✅     | ✅ (M1/M2/M3) |
| Windows  | ✅     | ❌            |

### Build Times

Approximate build times per wheel:
- **Linux x86_64**: 8-10 minutes
- **Linux ARM64** (via QEMU): 12-15 minutes
- **macOS x86_64**: 10-12 minutes
- **macOS ARM64**: 8-10 minutes
- **Windows x86_64**: 10-12 minutes

Total release time: ~90-120 minutes (all platforms + tests)

### Security Features

- **PyPI Trusted Publishing**: No API tokens, OIDC authentication
- **SHA-pinned Actions**: All GitHub Actions pinned to commit SHAs
- **Cross-platform Testing**: Built wheels tested on all target platforms
- **Automated Validation**: Tests, linting, type checking before publish

### Manual Release (if needed)

For emergency releases or testing:

```bash
# 1. Update version in Cargo.toml
./scripts/sync_version.sh 0.2.0

# 2. Commit and tag
git add Cargo.toml Cargo.lock
git commit -m "chore(release): 0.2.0"
git tag v0.2.0
git push origin main --tags

# 3. GitHub Actions will automatically build and publish
```

### Conventional Commit Examples

```bash
# Feature (minor version bump)
git commit -m "feat: add provider function support"

# Bug fix (patch version bump)
git commit -m "fix: resolve circular dependency detection issue"

# Performance improvement (patch version bump)
git commit -m "perf: optimize dependency graph construction"

# Breaking change (major version bump)
git commit -m "feat: redesign Container API

BREAKING CHANGE: Container.register() now requires explicit scope parameter"

# Non-release commits (no version bump)
git commit -m "docs: update README examples"
git commit -m "chore: update dependencies"
git commit -m "ci: improve workflow caching"
```

## Troubleshooting

### Maturin Build Issues
```bash
# Clean and rebuild
cargo clean
maturin develop --release
```

### Import Errors
Make sure to rebuild after Rust changes:
```bash
maturin develop
```

### Test Discovery Issues
Check pytest configuration in `pyproject.toml`:
```toml
python_classes = ["Describe*", "Test*"]
python_functions = ["it_*", "test_*"]
```

### Coverage Not Running
Check pre-commit configuration targets the correct test file:
```yaml
args: [tests/test_component.py, --cov=dioxide, --cov-fail-under=95, --cov-branch, -q]
```

## Working with Claude Code

When working on this project:

1. **Always follow TDD** - Write tests before implementation
2. **Test through Python API** - Don't write Rust unit tests
3. **Check coverage** - Run coverage before committing
4. **Use Describe*/it_* pattern** - Follow BDD test structure
5. **Keep tests simple** - No logic in tests
6. **Clean commits** - No attribution or co-authored lines

## Reference Documentation

- **README.md**: Project overview and quick start
- **COVERAGE.md**: Detailed coverage documentation
- **pyproject.toml**: Python configuration
- **Cargo.toml**: Rust configuration
- **.pre-commit-config.yaml**: Quality checks configuration
- this project uses uv. Use the uv commands to run pytest and other python cli tools. Avoid `uv pip` commands and use the built-in uv commands instead.
