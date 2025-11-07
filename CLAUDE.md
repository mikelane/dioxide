# CLAUDE.md

This file provides guidance to Claude Code when working on the dioxide codebase.

## Project Overview

**dioxide** is a fast, Rust-backed declarative dependency injection framework for Python that combines:
- **Declarative Python API** - Simple `@component` decorators and type hints
- **Rust-backed performance** - Fast container operations via PyO3
- **Type safety** - Full support for mypy and type checkers
- **Clean architecture** - Encourages loose coupling and testability

**Note**: The package was recently renamed from `rivet_di` to `dioxide`. All references in code, tests, and documentation have been updated to use `dioxide`.

**⚠️ API IN TRANSITION**: dioxide is currently undergoing MLP API realignment (v0.0.2-alpha). The current codebase uses v0.0.1-alpha syntax, but documentation has been updated to show target MLP syntax. Expect breaking changes as we implement the MLP Vision.

## MLP Vision: The North Star

**CRITICAL**: Before making ANY architectural, API, or design decisions, consult **`docs/MLP_VISION.md`**.

The MLP Vision document is the **canonical design reference** for Dioxide. It defines:

- **The North Star**: Make the Dependency Inversion Principle feel inevitable
- **Guiding Principles**: 7 core principles that guide ALL decisions (type-safe, explicit, fails fast, etc.)
- **Core API Design**: `@component`, `@profile`, container, lifecycle protocols
- **Profile System**: Hybrid approach (common + custom profiles via `__getattr__`)
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
from dioxide import component, profile
from typing import Protocol

# Singleton component (default) - shared across app
@component
class UserService:
    pass

# Factory component - new instance each time
@component.factory
class RequestHandler:
    pass

# Protocol implementation with profile
class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass  # Real implementation
```

**Implementation**: `python/dioxide/decorators.py` (MLP realignment in progress)

**How it works**:
1. `@component` - Registers as SINGLETON (default scope)
2. `@component.factory` - Registers as FACTORY scope (new instance each call)
3. `@component.implements(Protocol)` - Registers concrete implementation for protocol
4. `@profile` - Associates component with environment profile (production, test, dev)
5. `container.scan()` discovers all registered classes by profile

### Container (Global Singleton Pattern)

MLP uses a global singleton container for simplicity and ergonomics:

```python
from dioxide import container, component, profile

# Scan and activate a profile
container.scan("app", profile="production")  # or "test", "development"

# Resolve with automatic dependency injection
controller = container.resolve(UserController)  # Dependencies auto-injected

# Alternative syntax (optional)
controller = container[UserController]
```

**Features**:
- **Global singleton**: No manual container instantiation (`from dioxide import container`)
- **Profile selection**: Scan with `profile` parameter to activate environment-specific implementations
- **Auto-discovery**: Finds all `@component` decorated classes in package
- **Type-safe resolution**: `container.resolve(Type)` with full mypy support
- **Dependency injection**: Inspects `__init__` type hints and auto-injects dependencies

**Implementation**: `python/dioxide/container.py` (MLP realignment in progress)

**Important details**:
- SINGLETON components shared across entire app lifecycle
- FACTORY components create new instance for each resolution
- Profile system enables clean swapping of implementations (e.g., DB → in-memory for tests)

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

## Current Status: MLP API Realignment (v0.0.2-alpha)

**⚠️ IMPORTANT**: dioxide is currently undergoing MLP API realignment. The v0.0.1-alpha API is being replaced with the MLP Vision API.

### Recent Milestones

**v0.0.1-alpha (Released Nov 6, 2025)** ✅
- First public release to Test PyPI
- Basic `@component` decorator with `@component(scope=...)` syntax
- `Container().scan()` auto-discovery
- 100% test coverage
- Full CI/CD automation

**v0.0.2-alpha (In Progress - MLP Realignment)** 🔄
- Breaking API changes to align with MLP Vision
- New syntax: `@component.factory`, `@component.implements(Protocol)`
- Profile system: `@profile.production`, `@profile("test", "development")`
- Global singleton container: `from dioxide import container`
- Updated `container.scan("package", profile="...")`

**Timeline to MLP Complete**:
- **Nov 2025**: v0.0.2-alpha (API realignment) ← **WE ARE HERE**
- **Dec 2025**: v0.0.3-alpha (lifecycle management), v0.0.4-alpha (polish)
- **Mid-Dec 2025**: v0.1.0-beta (MLP complete, API freeze)

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

When working on this project, follow these requirements in order:

1. **Consult MLP Vision** - Check `docs/MLP_VISION.md` before making design decisions
2. **Ensure issue exists** - ALL work must have an associated GitHub issue (see Issue Tracking Requirements)
3. **Always follow TDD** - Write tests before implementation
4. **Test through Python API** - Don't write Rust unit tests
5. **Check coverage** - Run coverage before committing
6. **Use Describe*/it_* pattern** - Follow BDD test structure
7. **Keep tests simple** - No logic in tests
8. **Update documentation** - ALL code changes MUST include documentation updates (see Documentation Requirements)
9. **Clean commits** - No attribution or co-authored lines, always reference issue number
10. **Update issue** - Keep the GitHub issue updated as you work
11. **Close properly** - Use "Fixes #N" in PR description to auto-close issue

**CRITICAL**: Steps 3 (TDD) and 8 (Documentation) are NOT optional. Code without tests or documentation is incomplete and will not be merged.

## Reference Documentation

- **docs/MLP_VISION.md**: 🌟 **CANONICAL DESIGN DOCUMENT** - The north star for all architectural and API decisions
- **README.md**: Project overview and quick start
- **COVERAGE.md**: Detailed coverage documentation
- **STATUS.md**: Current sprint status and progress
- **pyproject.toml**: Python configuration
- **Cargo.toml**: Rust configuration
- **.pre-commit-config.yaml**: Quality checks configuration
- this project uses uv. Use the uv commands to run pytest and other python cli tools. Avoid `uv pip` commands and use the built-in uv commands instead.
