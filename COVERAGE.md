# Code Coverage

This document explains how code coverage works for dioxide and how to run coverage reports.

## Architecture

dioxide is a hybrid Python/Rust project:
- **Python code** (`python/dioxide/`) - Public API that users interact with
- **Rust code** (`rust/src/`) - Private implementation for performance-critical operations

## Coverage Tools

### Python Coverage (pytest-cov)

Measures coverage of the Python code. This is the **primary coverage metric** since the Python API is the public interface.

**Run Python coverage:**
```bash
pytest tests/ --cov=dioxide --cov-report=term-missing --cov-report=html
```

**View HTML report:**
```bash
open htmlcov/index.html
```

**Coverage requirements:**
- **Overall coverage**: ≥ 90%
- **Branch coverage**: ≥ 95%

### Rust Coverage (LLVM-based)

Measuring Rust coverage from Python FFI tests is complex due to build tooling:
1. The Rust code is compiled as a Python extension (.so file)
2. maturin copies/renames the binary during installation
3. LLVM coverage requires matching the exact binary to profraw files

**Current approach:**
- The Python integration tests (`tests/test_rust_container_edge_cases.py`) exercise the Rust implementation through the Python API
- Since the Rust code is private implementation, testing it through the public Python API is the correct approach
- The test failures proving the singleton cache bug demonstrate that the tests ARE exercising the Rust code paths

**For Rust coverage (advanced):**

This requires building with instrumentation and matching binaries to profile data. Due to PyO3 FFI complexity, this is primarily useful for development debugging rather than CI/CD.

```bash
# Install prerequisites
rustup component add llvm-tools-preview
cargo install cargo-llvm-cov

# Set environment and build with instrumentation
export LLVM_PROFILE_FILE='target/dioxide-%p-%12m.profraw'
export RUSTFLAGS='-C instrument-coverage'
maturin develop --release

# Run tests (generates .profraw files)
pytest tests/

# Note: Generating reports from FFI .profraw files requires matching
# the exact binary build, which is complex with maturin's build process.
```

## Running Coverage Before Commit

**Always run coverage before committing:**

```bash
# Run all tests with coverage
pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch

# Verify branch coverage meets requirements
# The report should show >= 95% branch coverage
```

**Look for:**
- `Cover` column shows overall line coverage
- `Branch` column shows branch coverage (decision points)
- Missing lines in the rightmost column indicate untested code paths

## Coverage in CI/CD

Coverage is automatically checked in the pre-commit hooks:
- Tests must pass
- Coverage thresholds must be met

## Understanding Branch Coverage

Branch coverage measures whether all decision paths are tested:

```python
# This requires 2 tests to achieve 100% branch coverage:
# Test 1: when condition is True
# Test 2: when condition is False
if condition:
    do_something()
else:
    do_something_else()
```

**Why branch coverage matters:**
- Line coverage can be 100% but miss edge cases
- Branch coverage ensures all code paths (if/else, try/except, match cases) are tested
- 95% branch coverage means we test 95% of all decision paths

## Interpreting Coverage Reports

**Green (100%)**: Fully tested
**Yellow (80-99%)**: Mostly tested, some paths missing
**Red (<80%)**: Insufficient testing

**Missing coverage is acceptable when:**
- Code is unreachable (defensive programming)
- Code is deprecated but maintained for backward compatibility
- Error handling for truly exceptional cases

**Missing coverage is NOT acceptable when:**
- Business logic is untested
- Error paths are untested
- Edge cases are untested
