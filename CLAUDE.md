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
