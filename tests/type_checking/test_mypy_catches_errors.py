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

            # Should catch attr-defined errors
            assert 'has no attribute' in output or 'attr-defined' in output, (
                f'mypy should catch attribute errors\nOutput: {output}'
            )

            # Should catch arg-type errors
            assert 'Argument' in output or 'arg-type' in output, (
                f'mypy should catch argument type errors\nOutput: {output}'
            )

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
