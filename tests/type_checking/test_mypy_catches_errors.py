"""
Test runner that verifies mypy catches type errors in invalid test files.

This is a runtime test that runs mypy programmatically and verifies it
catches the intentional type errors in our negative test files.
"""

import subprocess
import sys
from pathlib import Path


class DescribeMypyErrorDetection:
    """Tests that mypy catches intentional type errors."""

    def it_catches_invalid_resolve_usage(self) -> None:
        """mypy detects type errors in invalid_resolve_usage.py."""
        test_file = Path(__file__).parent / 'invalid_resolve_usage.py'
        assert test_file.exists(), f'Test file not found: {test_file}'

        # Remove type: ignore comments temporarily to test mypy
        content = test_file.read_text()
        content_without_ignores = content.replace('# type: ignore[attr-defined]', '')
        content_without_ignores = content_without_ignores.replace('# type: ignore[arg-type]', '')

        # Create temporary file without ignores
        temp_file = test_file.parent / 'temp_invalid_test.py'
        temp_file.write_text(content_without_ignores)

        try:
            # Run mypy on the file
            result = subprocess.run(
                [sys.executable, '-m', 'mypy', str(temp_file), '--no-error-summary'],
                capture_output=True,
                text=True,
            )

            # mypy should find errors (exit code 1)
            assert result.returncode == 1, (
                f'mypy should detect errors but exit code was {result.returncode}\n'
                f'stdout: {result.stdout}\n'
                f'stderr: {result.stderr}'
            )

            # Verify specific errors are caught
            output = result.stdout + result.stderr

            # Should catch arg-type errors (attr-defined is globally disabled for test files)
            assert 'Argument' in output or 'arg-type' in output, (
                f'mypy should catch argument type errors\nOutput: {output}'
            )

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def it_catches_missing_initialize_method(self) -> None:
        """mypy detects missing initialize() in @lifecycle class."""
        test_file = Path(__file__).parent / 'invalid_lifecycle_missing_initialize.py'
        assert test_file.exists(), f'Test file not found: {test_file}'

        # Remove type: ignore comments temporarily to test mypy
        content = test_file.read_text()
        content_without_ignores = content.replace('# type: ignore[arg-type]', '')

        # Create temporary file without ignores
        temp_file = test_file.parent / 'temp_missing_init.py'
        temp_file.write_text(content_without_ignores)

        try:
            # Run mypy on the file
            result = subprocess.run(
                [sys.executable, '-m', 'mypy', str(temp_file), '--no-error-summary'],
                capture_output=True,
                text=True,
            )

            # mypy should find errors (exit code 1)
            assert result.returncode == 1, (
                f'mypy should detect missing initialize() but exit code was {result.returncode}\n'
                f'stdout: {result.stdout}\n'
                f'stderr: {result.stderr}'
            )

            # Verify specific errors are caught
            output = result.stdout + result.stderr

            # Should catch that initialize() is missing
            assert 'arg-type' in output or 'initialize' in output.lower(), (
                f'mypy should catch missing initialize() method\nOutput: {output}'
            )

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def it_catches_missing_dispose_method(self) -> None:
        """mypy detects missing dispose() in @lifecycle class."""
        test_file = Path(__file__).parent / 'invalid_lifecycle_missing_dispose.py'
        assert test_file.exists(), f'Test file not found: {test_file}'

        # Remove type: ignore comments temporarily to test mypy
        content = test_file.read_text()
        content_without_ignores = content.replace('# type: ignore[arg-type]', '')

        # Create temporary file without ignores
        temp_file = test_file.parent / 'temp_missing_dispose.py'
        temp_file.write_text(content_without_ignores)

        try:
            # Run mypy on the file
            result = subprocess.run(
                [sys.executable, '-m', 'mypy', str(temp_file), '--no-error-summary'],
                capture_output=True,
                text=True,
            )

            # mypy should find errors (exit code 1)
            assert result.returncode == 1, (
                f'mypy should detect missing dispose() but exit code was {result.returncode}\n'
                f'stdout: {result.stdout}\n'
                f'stderr: {result.stderr}'
            )

            # Verify specific errors are caught
            output = result.stdout + result.stderr

            # Should catch that dispose() is missing
            assert 'arg-type' in output or 'dispose' in output.lower(), (
                f'mypy should catch missing dispose() method\nOutput: {output}'
            )

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def it_catches_sync_methods_instead_of_async(self) -> None:
        """mypy detects sync methods when async is required."""
        test_file = Path(__file__).parent / 'invalid_lifecycle_sync_methods.py'
        assert test_file.exists(), f'Test file not found: {test_file}'

        # Remove type: ignore comments temporarily to test mypy
        content = test_file.read_text()
        content_without_ignores = content.replace('# type: ignore[arg-type]', '')
        content_without_ignores = content_without_ignores.replace('# type: ignore[override]', '')

        # Create temporary file without ignores
        temp_file = test_file.parent / 'temp_sync_methods.py'
        temp_file.write_text(content_without_ignores)

        try:
            # Run mypy on the file
            result = subprocess.run(
                [sys.executable, '-m', 'mypy', str(temp_file), '--no-error-summary'],
                capture_output=True,
                text=True,
            )

            # mypy should find errors (exit code 1)
            assert result.returncode == 1, (
                f'mypy should detect sync methods but exit code was {result.returncode}\n'
                f'stdout: {result.stdout}\n'
                f'stderr: {result.stderr}'
            )

            # Verify specific errors are caught
            output = result.stdout + result.stderr

            # Should catch type mismatch (sync vs async)
            assert 'arg-type' in output or 'incompatible' in output.lower(), (
                f'mypy should catch sync vs async mismatch\nOutput: {output}'
            )

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
