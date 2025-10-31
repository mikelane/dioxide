# Type Checking Tests

This directory contains **negative type tests** - files with intentionally wrong code that should **FAIL mypy**.

## Purpose

These tests verify that mypy properly catches type errors when using dioxide's APIs.

## How to Run

```bash
# Run mypy on the type checking tests
# These should FAIL mypy (that's expected!)
mypy tests/type_checking/invalid_*.py --no-error-summary

# To verify they fail, check exit code:
# Exit code 0 = all passed (BAD - means mypy isn't catching errors!)
# Exit code 1 = found errors (GOOD - mypy is working!)
```

## Test Files

- `invalid_resolve_usage.py` - Wrong method calls, attributes, argument types
- More files to be added as type safety features expand

## Note

The `# type: ignore` comments are added to prevent these test files from breaking
CI when mypy runs on the entire codebase. We verify type checking in a separate
test runner that explicitly checks these files SHOULD fail.
