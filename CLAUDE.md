# CLAUDE.md

This file provides guidance to Claude Code when working on the dioxide codebase.

## Project Overview

**dioxide** is a declarative dependency injection framework for Python that makes clean architecture simple. It combines:
- **Hexagonal Architecture API** - `@adapter.for_()` and `@service` decorators with type hints
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability
- **Rust-backed core** - Fast container operations via PyO3

**Note**: The package was recently renamed from `rivet_di` to `dioxide`. All references in code, tests, and documentation have been updated to use `dioxide`.

**v1.0.0 STABLE**: MLP Complete! Hexagonal architecture API, lifecycle management, circular dependency detection, performance benchmarking, framework integrations (FastAPI, Flask, Celery, Click), and comprehensive testing guide all implemented.

## MLP Vision: The North Star

**CRITICAL**: Before making ANY architectural, API, or design decisions, consult **`docs/MLP_VISION.md`**.

The MLP Vision document is the **canonical design reference** for Dioxide. It defines:

- **The North Star**: Make the Dependency Inversion Principle feel inevitable
- **Guiding Principles**: 7 core principles that guide ALL decisions (type-safe, explicit, fails fast, etc.)
- **Core API Design**: `@adapter.for_()`, `@service`, `Profile` enum, container, lifecycle protocols
- **Profile System**: Profile enum (PRODUCTION, TEST, DEVELOPMENT, etc.)
- **Testing Philosophy**: Fakes at the seams, NOT mocks
- **What We're NOT Building**: Explicit exclusions list for MLP scope
- **Decision Framework**: 5 questions to ask when making choices

**When to consult MLP_VISION.md:**

- ✅ Before designing new features
- ✅ When choosing between implementation approaches
- ✅ When questions arise about scope ("should we support X?")
- ✅ When making API design decisions
- ✅ When unclear about testing approach
- ✅ When considering architecture patterns

**Key principle:** If MLP_VISION.md says not to build something for MLP, don't build it. Simplicity over features.

## Issue Tracking Requirements

**MANDATORY**: All work must be associated with a GitHub issue.

### Before Starting Any Work

**STOP.** Before writing ANY code, tests, or documentation:

1. **Check for existing issue**
   ```bash
   gh issue list --label "enhancement" --label "bug"
   ```

2. **If no issue exists, create one OR ask to create one**
   ```bash
   gh issue create --title "Brief description" --body "Detailed description"
   ```

3. **Assign the issue to yourself**
   ```bash
   gh issue develop <issue-number> --checkout
   ```

4. **Reference the issue in branch name**
   ```bash
   git checkout -b feat/issue-123-add-profile-system
   git checkout -b fix/issue-456-circular-dependency
   ```

**No exceptions.** Even small changes, bug fixes, documentation updates, or refactoring need an issue.

### Why This Is Required

- **Traceability**: Every change has a reason and context
- **Progress tracking**: Milestone and project board stay accurate
- **Communication**: Team/stakeholders can see what's being worked on
- **History**: Future developers understand why decisions were made
- **Prevents duplicate work**: See what's already in progress

### During Work: Keep Issue Updated

As you work, **keep the issue updated** with progress:

1. **Add comments** when you make important discoveries
   ```bash
   gh issue comment <issue-number> --body "Found that X requires Y, adjusting approach"
   ```

2. **Update description** if scope changes
   ```bash
   gh issue edit <issue-number> --body "Updated description..."
   ```

3. **Add labels** as appropriate
   ```bash
   gh issue edit <issue-number> --add-label "blocked" --add-label "needs-discussion"
   ```

4. **Link related issues**
   ```
   # In issue comment
   Related to #123
   Blocks #456
   Depends on #789
   ```

### When Completing Work

1. **Reference issue in ALL commits**
   ```bash
   git commit -m "feat: add profile system (#123)"
   ```

2. **Use closing keywords in PR description**
   ```markdown
   Fixes #123
   Closes #456
   Resolves #789
   ```

3. **Update issue before closing** with summary
   ```bash
   gh issue comment <issue-number> --body "Completed. Final approach: ..."
   ```

### Issue Requirements Checklist

Before considering ANY task complete:

- [ ] Issue exists for the work
- [ ] Issue is assigned to you
- [ ] Branch name references issue number
- [ ] Commits reference issue number
- [ ] PR description uses "Fixes #N" or "Closes #N"
- [ ] Issue has been updated during work if scope changed
- [ ] Issue will auto-close when PR merges

**If any checkbox is unchecked, the work is NOT complete.**

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
class DescribeAdapterFeature:
    """Tests for @adapter decorator functionality."""

    def it_registers_the_adapter_for_port(self) -> None:
        """Decorator adds adapter to registry for specified port."""
        from typing import Protocol
        from dioxide import adapter, Profile

        class EmailPort(Protocol):
            def send(self, to: str) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def send(self, to: str) -> None:
                pass

        # Test that adapter is registered...
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
uv run pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch
```

**Requirements**:
- Overall coverage: ≥ 90%
- Branch coverage: ≥ 95%

The pre-commit hook enforces these requirements. See `COVERAGE.md` for detailed documentation.

## Documentation Requirements

**CRITICAL**: Documentation is NOT optional. Every code change MUST include corresponding documentation updates.

### Documentation-First Development

All agents and developers are responsible for maintaining documentation as they work:

1. **Before writing code**: Update or create documentation describing the feature/change
2. **During development**: Keep documentation in sync with code changes
3. **Before opening PR**: Verify all affected documentation is updated

### What Must Be Documented

**For every change, update relevant documentation**:

- **API changes**: Update README.md Quick Start, CLAUDE.md examples, docstrings
- **New features**: Add to README.md Features section, update ROADMAP.md if needed
- **Breaking changes**: Document migration path, update all examples
- **Bug fixes**: Update CHANGELOG.md (if significant), relevant docs explaining correct behavior
- **Architecture decisions**: Create/update ADRs in docs/design/
- **Configuration changes**: Update setup instructions in README.md and CLAUDE.md
- **Testing patterns**: Update test documentation if new patterns introduced

### Documentation Sources of Truth

Know which document to update:

| Type of Change | Primary Document | Secondary Documents |
|----------------|------------------|---------------------|
| Public API | README.md | CLAUDE.md, docs/MLP_VISION.md |
| Developer workflow | CLAUDE.md | CONTRIBUTING.md |
| Design decisions | docs/design/ADR-*.md | MLP_VISION.md |
| Sprint status | STATUS.md | GitHub issues, milestones |
| Long-term vision | ROADMAP.md | MLP_VISION.md |
| MLP features | docs/MLP_VISION.md | README.md, ROADMAP.md |

### PR Completion Checklist

**A PR is NOT complete until**:

- [ ] All code changes have corresponding documentation updates
- [ ] README.md examples work with the changes
- [ ] CLAUDE.md reflects any workflow changes
- [ ] Docstrings added/updated for new/modified public APIs
- [ ] CHANGELOG.md updated (if user-facing change)
- [ ] Migration guide written (if breaking change)
- [ ] ADR created (if architectural decision)
- [ ] STATUS.md updated (if affects current sprint)

### Examples of Required Documentation Updates

**Adding a new decorator**:
- ✅ Add example to README.md Quick Start
- ✅ Add detailed explanation to CLAUDE.md Key Components
- ✅ Add docstrings with usage examples
- ✅ Update CHANGELOG.md
- ✅ Create ADR if design decision involved

**Fixing a bug**:
- ✅ Update docstring if behavior clarification needed
- ✅ Add comment in code explaining the fix
- ✅ Update CHANGELOG.md if user-facing
- ✅ Update any examples that showed incorrect usage

**Refactoring internal code**:
- ✅ Update CLAUDE.md if internal architecture changed
- ✅ Update comments explaining new structure
- ✅ Create ADR if significant design change

**Changing workflow**:
- ✅ Update CLAUDE.md with new commands/process
- ✅ Update CONTRIBUTING.md if affects contributors
- ✅ Update STATUS.md if affects current sprint

### Documentation Review in PRs

When reviewing PRs, check:

1. **Accuracy**: Does documentation match the actual code behavior?
2. **Completeness**: Are all changes documented?
3. **Consistency**: Do examples across documents match?
4. **Examples**: Do code examples actually work?
5. **Migration**: Are breaking changes explained with migration path?

**If documentation is missing or incomplete, request changes. Do NOT merge.**

### Why This Matters

Undocumented code is:
- **Unusable**: Users can't learn how to use it
- **Unmaintainable**: Future developers can't understand intent
- **Untrustworthy**: Outdated docs are worse than no docs
- **Incomplete**: The work isn't done until it's documented

**Remember**: If it's not documented, it doesn't exist. Documentation is part of the implementation, not an afterthought.

## Common Development Commands

### Setup
```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies (use uv sync, not uv pip!)
uv sync --group dev

# Build Rust extension
maturin develop

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch

# Run specific test file
uv run pytest tests/test_adapter.py

# Run tests matching a pattern
uv run pytest tests/ -k "lifecycle"

# Run performance benchmarks
uv run pytest tests/benchmarks/ --benchmark-only
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

### Documentation
```bash
# Install docs dependencies
uv sync --group docs

# Build HTML documentation
uv run sphinx-build -b html docs docs/_build/html

# View documentation locally
open docs/_build/html/index.html  # macOS
xdg-open docs/_build/html/index.html  # Linux
start docs/_build/html/index.html  # Windows

# Live reload server (recommended for development)
./scripts/docs-serve.sh              # Opens browser automatically
./scripts/docs-serve.sh --no-open    # Without auto-opening browser
```

**Live Reload Development**: The `docs-serve.sh` script uses `sphinx-autobuild` to provide:
- Automatic rebuild when `.md`, `.rst`, or Python docstring files change
- Browser auto-refresh on rebuild
- Serves at http://localhost:8000
- Watches both `docs/` and `python/dioxide/` directories

## Repository Structure

```
dioxide/
├── python/dioxide/         # Public Python API
│   ├── __init__.py          # Package exports
│   ├── container.py         # Container class with profile-based scanning
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
├── rust/src/                # Private Rust implementation
│   └── lib.rs               # PyO3 bindings and container logic
├── tests/                   # Python integration tests
│   ├── test_adapter.py      # @adapter decorator tests
│   ├── test_services.py     # @service decorator tests
│   ├── test_lifecycle.py    # @lifecycle tests
│   ├── test_container.py    # Container behavior tests
│   ├── type_checking/       # mypy type safety tests
│   └── benchmarks/          # Performance benchmark tests
├── examples/                # Example applications
│   └── fastapi/             # FastAPI integration example
├── docs/                    # Documentation
│   ├── MLP_VISION.md        # Canonical design specification
│   ├── TESTING_GUIDE.md     # Testing philosophy and patterns
│   └── design/              # Architecture Decision Records (ADRs)
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── pyproject.toml           # Python project configuration
├── Cargo.toml               # Rust project configuration
├── COVERAGE.md              # Coverage documentation
└── CLAUDE.md                # This file
```

## Key Components

### Hexagonal Architecture API

dioxide uses a hexagonal architecture (ports-and-adapters) API that makes clean architecture patterns explicit and type-safe.

#### @adapter Decorator

The `@adapter.for_(Port, profile=...)` decorator marks concrete implementations (adapters) for abstract ports (Protocols/ABCs):

```python
from typing import Protocol
from dioxide import adapter, Profile

# Define port (interface)
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        pass

# Test adapter (fake)
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Development adapter
@adapter.for_(EmailPort, profile=['development', 'ci'])
class LoggingEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"Email to {to}: {subject}")
```

**Implementation**: `python/dioxide/adapter.py`

**How it works**:
1. `@adapter.for_(Port, profile=...)` - Registers adapter for a port with profile(s)
2. Port can be any Protocol or ABC
3. Profile can be a string, Profile enum, or list of profiles
4. Multiple adapters can implement the same port for different profiles
5. `container.scan(profile=...)` activates the matching adapter

#### @service Decorator

The `@service` decorator marks core business logic classes that depend on ports:

```python
from dioxide import service

@service
class UserService:
    def __init__(self, email: EmailPort, db: DatabasePort):
        self.email = email
        self.db = db

    async def register_user(self, email_addr: str, name: str):
        # Core logic - doesn't know which adapters are active
        user = await self.db.create_user(name, email_addr)
        await self.email.send(email_addr, "Welcome!", f"Hello {name}")
        return user
```

**Implementation**: `python/dioxide/services.py`

**How it works**:
1. `@service` - Registers as SINGLETON (always shared across app)
2. Available in ALL profiles (doesn't vary by environment)
3. Dependencies injected via constructor type hints
4. Services depend on ports (interfaces), not concrete adapters

#### Profile Enum

The `Profile` enum defines standard environment profiles:

```python
from dioxide import Profile

# Standard profiles
Profile.PRODUCTION  # Production environment
Profile.TEST        # Test environment
Profile.DEVELOPMENT # Development environment
Profile.STAGING     # Staging environment
Profile.CI          # CI environment
Profile.ALL         # Available in all environments (use '*')
```

**Implementation**: `python/dioxide/profile_enum.py`

**How it works**:
1. String-based enum for consistency (`Profile.PRODUCTION.value == 'production'`)
2. Case-insensitive matching (normalized to lowercase)
3. `Profile.ALL` (`'*'`) matches all environments
4. Custom profiles supported (pass string to `@adapter.for_()`)

#### @lifecycle Decorator

The `@lifecycle` decorator enables opt-in lifecycle management for services and adapters that need initialization and cleanup:

```python
from dioxide import service, lifecycle

@service
@lifecycle
class Database:
    """Service with async initialization and cleanup."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = None

    async def initialize(self) -> None:
        """Called automatically when container starts."""
        self.engine = create_async_engine(self.config.database_url)
        logger.info(f"Connected to {self.config.database_url}")

    async def dispose(self) -> None:
        """Called automatically when container stops."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

# Use async context manager for automatic lifecycle
async with container:
    db = container.resolve(Database)
    # db.initialize() was called automatically
# db.dispose() called automatically on exit
```

**Implementation**: `python/dioxide/lifecycle.py`, `python/dioxide/container.py`

**How it works**:
1. `@lifecycle` - Marks class for lifecycle management with `_dioxide_lifecycle = True`
2. Validates `initialize()` and `dispose()` methods exist at decoration time
3. Validates both methods are async coroutines
4. Raises `TypeError` with clear error if validation fails
5. Works with `@service` and `@adapter.for_()` decorators
6. `container.start()` - Initializes all @lifecycle components in dependency order
7. `container.stop()` - Disposes all @lifecycle components in reverse dependency order
8. `async with container` - Context manager automatically calls start/stop

**Type safety**: Type stubs (`lifecycle.pyi`) provide IDE autocomplete and mypy validation of method signatures.

**Status**: Fully implemented (v0.1.0-beta.2).

### Container (Profile-Based Dependency Injection)

dioxide provides a Container class that supports profile-based dependency injection:

```python
from dioxide import Container, Profile, adapter, service
from typing import Protocol

# Define port
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Define adapters
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    pass

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    pass

# Define service
@service
class UserService:
    def __init__(self, email: EmailPort):
        self.email = email

# Production container
prod_container = Container()
prod_container.scan(profile=Profile.PRODUCTION)
prod_service = prod_container.resolve(UserService)
# UserService gets SendGridAdapter

# Test container
test_container = Container()
test_container.scan(profile=Profile.TEST)
test_service = test_container.resolve(UserService)
# UserService gets FakeEmailAdapter

# Port-based resolution
email_adapter = prod_container.resolve(EmailPort)
# Returns SendGridAdapter (the active adapter for this profile)

# Alternative syntax
service = prod_container[UserService]  # Same as resolve()
```

**Features**:
- **Profile-based scanning**: `container.scan(profile=...)` activates profile-specific adapters
- **Port-based resolution**: `container.resolve(Port)` returns the active adapter for that port
- **Type-safe resolution**: `container.resolve(Type)` with full mypy support
- **Automatic dependency injection**: Inspects `__init__` type hints and auto-injects dependencies
- **Bracket syntax**: `container[Type]` as alternative to `resolve(Type)`
- **Circular dependency detection**: Fails fast at scan time with clear error messages
- **Lifecycle management**: Automatic initialization/disposal in dependency order

**Implementation**: `python/dioxide/container.py`

**Important details**:
- Services and adapters are SINGLETON by default (one instance per container)
- Each container instance maintains separate singleton instances
- Profile determines which adapters are active for a given container
- Services depend on ports (Protocols), container injects active adapter
- Circular dependencies are detected and reported at `scan()` time

### Rust Container

The Rust implementation (`rust/src/lib.rs`) provides:
- Fast provider registration and resolution
- Singleton caching
- Type-based dependency lookup
- High-performance resolution (<1μs per resolution)

## Configuration Files

### pyproject.toml

Key configurations:
- **Build system**: maturin for Rust extensions
- **Python source**: `python-source = "python"`
- **Module name**: `module-name = "dioxide._dioxide_core"`
- **Test discovery**: Describe*/it_* pattern
- **Coverage**: Branch coverage enabled
- **Python versions**: 3.11, 3.12, 3.13, 3.14

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
- **petgraph**: Dependency graph algorithms

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

**Location**: https://github.com/mikelane/dioxide/milestones
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

### CRITICAL: Pull Request Requirement

**ALL changes MUST go through the Pull Request process - NO EXCEPTIONS.**

This applies to:
- ✅ External contributors (via forks)
- ✅ Maintainers (via branches in main repository)
- ✅ All code changes, documentation updates, bug fixes, features
- ✅ ALL work must have an associated GitHub issue

Branch protection enforces this requirement on the `main` branch.

### Code Review Requirements

**Review process is CODEOWNERS-based:**

- **External contributor PRs**: MUST be approved by @mikelane (via `.github/CODEOWNERS`)
- **Maintainer PRs**: NO approval required (CODEOWNERS doesn't apply to code owners)
- **All PRs**: MUST pass CI checks and resolve all conversations

**Why maintainers don't need approval:**
PRs from maintainers exist for archaeology (historical record) and to benefit from automated CI checks, NOT for review gates. CODEOWNERS requirements automatically don't apply when the PR author IS the code owner.

**Branch protection settings:**
- Require code owner reviews: ✅ Enabled
- Minimum approving reviews: 0 (CODEOWNERS provides the requirement)
- Dismiss stale reviews: ✅ Enabled
- Require CI checks: ✅ Enabled (`build-and-test`)
- Required linear history: ✅ Enabled
- Required conversation resolution: ✅ Enabled

### Workflow: Starting New Work

**For Maintainers:**
1. **Create or verify GitHub issue exists** (MANDATORY - no issue, no work)
2. **Assign issue to yourself** on GitHub
3. **Move to "In Progress"** on project board (if using columns)
4. **Create branch**: `git checkout -b fix/issue-description` or `feat/issue-description`
5. **Follow TDD**: Write tests first, then implementation
6. **Commit with issue reference**: `git commit -m "fix: description (#22)"`
7. **Push branch**: `git push origin fix/issue-description`
8. **Create Pull Request** - MANDATORY for all changes

**For External Contributors:**
1. **Fork the repository** if you haven't already
2. **Sync your fork** with upstream: `git fetch upstream && git merge upstream/main`
3. **Pick an issue** (look for `good-first-issue` or `help-wanted` labels)
4. **Comment on the issue** to let maintainers know you're working on it
5. **Create branch in your fork**: `git checkout -b fix/issue-description` or `feat/issue-description`
6. **Follow TDD**: Write tests first, then implementation
7. **Commit with issue reference**: `git commit -m "fix: description (#22)"`
8. **Push to your fork**: `git push origin fix/issue-description`
9. **Create Pull Request** from your fork to main repository

### Workflow: Completing Work

**For Maintainers:**
1. **Open PR** with `Fixes #22` in description - MANDATORY, no direct merges
2. **Fill out PR template** completely
3. **Wait for CI checks** to pass
4. **Merge PR** - No approval required (CODEOWNERS doesn't apply to code owners)
5. **Issue auto-closes** via "Fixes #22" keyword
6. **Issue moves to "Done"** on project board automatically
7. **Milestone progress updates** automatically

**Note**: Maintainer PRs don't require approval because CODEOWNERS requirements don't apply to the code owners themselves. PRs exist for archaeology/documentation purposes and to benefit from CI checks.

**For External Contributors:**
1. **Push to your fork**: `git push origin feature-branch`
2. **Open PR from your fork** to main repository with `Fixes #22` in description
3. **Fill out PR template** completely
4. **Wait for review** from maintainers
5. **Address feedback** if requested
6. **PR will be merged** by maintainers once approved
7. **Issue auto-closes** and moves to "Done" on project board

### Workflow: Weekly Status Update (Friday)

```bash
# 1. Review what was completed this week
gh issue list --milestone "v0.1.0 Documentation" --state closed --search "closed:>=$(date -v-7d +%Y-%m-%d)"

# 2. Check milestone progress
gh api repos/mikelane/dioxide/milestones/9 | jq '{open: .open_issues, closed: .closed_issues}'

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

- **ROADMAP.md**: Long-term vision aligned with MLP (updated Nov 2025)
- **docs/MLP_VISION.md**: Canonical design specification (THE north star)
- **docs/DOCUMENT_AUDIT.md**: Documentation alignment tracking
- **DX_EVALUATION.md**: PM assessment of current vs MLP state

**Historical documents** (deleted during MLP realignment):
- ~~docs/0.0.1-ALPHA_SCOPE.md~~ - Deleted (pre-MLP scope)
- ~~docs/RELEASE_CHECKLIST_0.0.1-alpha.md~~ - Deleted (pre-MLP checklist)

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

## Current Status: MLP Complete (v0.1.0-beta.2)

**✅ v0.1.0-beta.2 RELEASED** (Nov 23, 2025): MLP Complete! All must-have features implemented.

### Recent Milestones

**v0.0.1-alpha (Released Nov 6, 2025)** ✅
- First public release to Test PyPI
- Basic component decorator
- `Container().scan()` auto-discovery
- 100% test coverage
- Full CI/CD automation

**v0.0.2-alpha (COMPLETE Nov 16, 2025)** ✅
- Hexagonal architecture API implemented
- `@adapter.for_(Port, profile=Profile.PRODUCTION)` decorator
- `@service` decorator for core domain logic
- `Profile` enum (PRODUCTION, TEST, DEVELOPMENT, STAGING, CI, ALL)
- Port-based resolution (`container.resolve(Port)`)
- Global singleton container: `from dioxide import container`
- Migration guide (MIGRATION.md)
- Complete documentation alignment

**v0.0.4-alpha (COMPLETE Nov 22, 2025)** ✅
- `@lifecycle` decorator for opt-in lifecycle management
- Container lifecycle runtime (`async with container`, `start()`, `stop()`)
- Dependency-ordered initialization (Kahn's algorithm)
- Circular dependency detection at scan time
- Package scanning implementation

**v0.1.0-beta (RELEASED Nov 23, 2025)** ✅
- Performance benchmarking (all targets exceeded)
- FastAPI integration example
- Comprehensive testing guide (fakes > mocks philosophy)
- MLP Complete - API frozen, production-ready

**v0.1.0-beta.2 (RELEASED Nov 23, 2025)** ✅
- Release process improvements
- Test PyPI staging validation
- Wheel structure validation
- Documentation updates

See [ROADMAP.md](ROADMAP.md) and [docs/MLP_VISION.md](docs/MLP_VISION.md) for details.

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
   - Python versions: 3.11, 3.12, 3.13, 3.14

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

### Release Process Improvements (Phase 1 - Issue #137)

The release process includes robust validation and staging to prevent failures:

#### 1. Pre-flight Version Validation

Before building any wheels, the workflow validates that `Cargo.toml` version matches the git tag:

```bash
# Validate version synchronization locally
./scripts/validate_version.sh
```

This prevents wasting 90+ minutes building the wrong version. If there's a mismatch, the workflow fails immediately with clear instructions on how to fix it.

#### 2. Wheel Structure Validation

After building all wheels, the workflow validates ZIP structure and metadata:

```bash
# Validate wheels locally
./scripts/validate_wheels.py
```

This catches:
- ZIP corruption
- Trailing data after End of Central Directory (EOCD)
- Invalid wheel metadata

Prevents PyPI upload failures due to structural issues.

#### 3. Test PyPI Staging

All releases upload to Test PyPI BEFORE production PyPI:

1. Wheels uploaded to test.pypi.org
2. Upload validated (no PyPI errors)
3. Only after Test PyPI succeeds, upload to production PyPI

This prevents:
- Consuming production version numbers due to upload failures
- Discovering issues after production upload
- Requiring manual version bumps to retry

**Test PyPI Configuration**: Requires separate OIDC Trusted Publishing setup at test.pypi.org

**Benefits of this approach**:
- Failures caught in staging, not production
- No wasted version numbers on PyPI
- Same validation as production, but reversible
- Industry best practice for Python packaging

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
Check pre-commit configuration includes coverage checks:
```yaml
args: [tests/, --cov=dioxide, --cov-fail-under=95, --cov-branch, -q]
```

## Working with Claude Code

When working on this project, follow these requirements in order:

1. **Consult MLP Vision** - Check `docs/MLP_VISION.md` before making design decisions
2. **Ensure issue exists** - ALL work must have an associated GitHub issue (see Issue Tracking Requirements) - NO EXCEPTIONS
3. **Create feature branch** - Never work directly on main
4. **Always follow TDD** - Write tests before implementation
5. **Test through Python API** - Don't write Rust unit tests
6. **Check coverage** - Run coverage before committing
7. **Use Describe*/it_* pattern** - Follow BDD test structure
8. **Keep tests simple** - No logic in tests
9. **Update documentation** - ALL code changes MUST include documentation updates (see Documentation Requirements)
10. **Clean commits** - No attribution or co-authored lines, always reference issue number
11. **Update issue** - Keep the GitHub issue updated as you work
12. **Create Pull Request** - ALL changes MUST go through PR process - NO EXCEPTIONS
13. **Close properly** - Use "Fixes #N" in PR description to auto-close issue

**CRITICAL**:
- Step 2 (Issue exists) is MANDATORY - no issue means no work
- Step 4 (TDD) and 9 (Documentation) are NOT optional - code without tests or documentation is incomplete
- Step 12 (Pull Request) is ENFORCED by branch protection - direct pushes to main are blocked

## Reference Documentation

- **docs/MLP_VISION.md**: 🌟 **CANONICAL DESIGN DOCUMENT** - The north star for all architectural and API decisions
- **README.md**: Project overview and quick start
- **COVERAGE.md**: Detailed coverage documentation
- **STATUS.md**: Current sprint status and progress
- **TESTING_GUIDE.md**: Testing philosophy and patterns (fakes > mocks)
- **pyproject.toml**: Python configuration
- **Cargo.toml**: Rust configuration
- **.pre-commit-config.yaml**: Quality checks configuration
- This project uses **uv**. Use the uv commands to run pytest and other python cli tools. Avoid `uv pip` commands and use the built-in uv commands instead.
- Do not use `uv pip` commands. Use `uv add`, `uv remove`, and `uv sync` to deal with dependencies. Use groups and/or extras where appropriate.
