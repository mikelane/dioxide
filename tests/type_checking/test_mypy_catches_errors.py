"""
Test runner that verifies mypy catches type errors in invalid code patterns.

These tests validate that our .pyi type stubs correctly guide mypy to catch
user errors. Tests use mypy's -c option to check inline code strings,
eliminating filesystem access for hermetic, parallel-safe execution.

These tests are marked as 'slow' because they invoke mypy as a subprocess.
"""

import subprocess
import sys

import pytest

# Code snippets that should fail mypy type checking
# These are inline versions of the files in tests/type_checking/invalid/

INVALID_RESOLVE_USAGE = """
from dioxide import Container


class UserService:
    def get_user(self, user_id: int) -> str:
        return f'User {user_id}'


def test_wrong_argument_types() -> None:
    container = Container()
    container.register_singleton(UserService, lambda: UserService())
    service = container.resolve(UserService)
    # This should fail mypy - get_user expects int, not str
    service.get_user('not an int')
"""

INVALID_LIFECYCLE_MISSING_INITIALIZE = """
from dioxide import lifecycle, service


@service
@lifecycle
class DatabaseMissingInitialize:
    def __init__(self) -> None:
        self.connected = False

    async def dispose(self) -> None:
        self.connected = False


db = DatabaseMissingInitialize()
"""

INVALID_LIFECYCLE_MISSING_DISPOSE = """
from dioxide import lifecycle, service


@service
@lifecycle
class DatabaseMissingDispose:
    def __init__(self) -> None:
        self.connected = False

    async def initialize(self) -> None:
        self.connected = True


db = DatabaseMissingDispose()
"""

INVALID_LIFECYCLE_SYNC_METHODS = """
from dioxide import lifecycle, service


@service
@lifecycle
class DatabaseWithSyncMethods:
    def __init__(self) -> None:
        self.connected = False

    def initialize(self) -> None:
        self.connected = True

    def dispose(self) -> None:
        self.connected = False


db = DatabaseWithSyncMethods()
"""


def _run_mypy_on_code(code: str) -> subprocess.CompletedProcess[str]:
    """Run mypy type checker on inline code string."""
    return subprocess.run(
        [sys.executable, '-m', 'mypy', '-c', code, '--no-error-summary'],
        capture_output=True,
        text=True,
    )


@pytest.mark.slow
class DescribeMypyErrorDetection:
    """Tests that mypy catches intentional type errors."""

    def it_catches_invalid_resolve_usage(self) -> None:
        """mypy detects type errors when using Container.resolve() incorrectly."""
        result = _run_mypy_on_code(INVALID_RESOLVE_USAGE)

        assert result.returncode == 1, (
            f'mypy should detect errors but exit code was {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )

        output = result.stdout + result.stderr
        assert 'Argument' in output or 'arg-type' in output, f'mypy should catch argument type errors\nOutput: {output}'

    def it_catches_missing_initialize_method(self) -> None:
        """mypy detects missing initialize() in @lifecycle class."""
        result = _run_mypy_on_code(INVALID_LIFECYCLE_MISSING_INITIALIZE)

        assert result.returncode == 1, (
            f'mypy should detect missing initialize() but exit code was {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )

        output = result.stdout + result.stderr
        assert 'arg-type' in output or 'initialize' in output.lower(), (
            f'mypy should catch missing initialize() method\nOutput: {output}'
        )

    def it_catches_missing_dispose_method(self) -> None:
        """mypy detects missing dispose() in @lifecycle class."""
        result = _run_mypy_on_code(INVALID_LIFECYCLE_MISSING_DISPOSE)

        assert result.returncode == 1, (
            f'mypy should detect missing dispose() but exit code was {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )

        output = result.stdout + result.stderr
        assert 'arg-type' in output or 'dispose' in output.lower(), (
            f'mypy should catch missing dispose() method\nOutput: {output}'
        )

    def it_catches_sync_methods_instead_of_async(self) -> None:
        """mypy detects sync methods when async is required."""
        result = _run_mypy_on_code(INVALID_LIFECYCLE_SYNC_METHODS)

        assert result.returncode == 1, (
            f'mypy should detect sync methods but exit code was {result.returncode}\n'
            f'stdout: {result.stdout}\n'
            f'stderr: {result.stderr}'
        )

        output = result.stdout + result.stderr
        # mypy reports 'type-var' error when class doesn't match protocol requirements
        assert 'arg-type' in output or 'incompatible' in output.lower() or 'type-var' in output.lower(), (
            f'mypy should catch sync vs async mismatch\nOutput: {output}'
        )
