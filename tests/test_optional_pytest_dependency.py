"""Tests for optional pytest dependency in dioxide.

This module verifies that dioxide can be imported without pytest installed.
The fresh_container context manager and core functionality should work
without pytest; only the pytest fixtures require pytest.

Issue: https://github.com/mikelane/dioxide/issues/362
"""

from __future__ import annotations

import subprocess
import sys
import textwrap


class DescribeDioxideImportWithoutPytest:
    """Tests for importing dioxide when pytest is not installed."""

    def it_imports_dioxide_without_pytest(self) -> None:
        """Core dioxide package imports successfully without pytest."""
        # We run a subprocess with a script that blocks pytest imports
        # and then tries to import dioxide.
        # The subprocess uses the same Python interpreter (sys.executable)
        # which has dioxide installed, so no cwd is needed.
        script = textwrap.dedent("""
            import sys
            from importlib.abc import MetaPathFinder

            # Block pytest from being imported
            class PytestBlocker(MetaPathFinder):
                def find_spec(self, fullname, path, target=None):
                    if fullname == 'pytest' or fullname.startswith('pytest.') or fullname.startswith('_pytest'):
                        raise ImportError(f'pytest is blocked for testing: {fullname}')
                    return None

            # Remove pytest if already imported
            for key in list(sys.modules.keys()):
                if key == 'pytest' or key.startswith('pytest.') or key.startswith('_pytest'):
                    del sys.modules[key]

            # Install the blocker
            sys.meta_path.insert(0, PytestBlocker())

            # Now try to import dioxide - this should work
            import dioxide

            # Verify core functionality is available
            assert hasattr(dioxide, 'Container')
            assert hasattr(dioxide, 'adapter')
            assert hasattr(dioxide, 'service')
            assert hasattr(dioxide, 'Profile')
            assert hasattr(dioxide, 'fresh_container')

            print("SUCCESS: dioxide imported without pytest")
        """)

        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f'Failed to import dioxide without pytest.\nstdout: {result.stdout}\nstderr: {result.stderr}'
        )
        assert 'SUCCESS' in result.stdout

    def it_imports_fresh_container_without_pytest(self) -> None:
        """fresh_container can be imported from dioxide.testing without pytest."""
        script = textwrap.dedent("""
            import sys
            from importlib.abc import MetaPathFinder

            # Block pytest from being imported
            class PytestBlocker(MetaPathFinder):
                def find_spec(self, fullname, path, target=None):
                    if fullname == 'pytest' or fullname.startswith('pytest.') or fullname.startswith('_pytest'):
                        raise ImportError(f'pytest is blocked for testing: {fullname}')
                    return None

            # Remove pytest if already imported
            for key in list(sys.modules.keys()):
                if key == 'pytest' or key.startswith('pytest.') or key.startswith('_pytest'):
                    del sys.modules[key]

            # Install the blocker
            sys.meta_path.insert(0, PytestBlocker())

            # Now try to import fresh_container - this should work
            from dioxide.testing import fresh_container

            # Verify it's a callable
            assert callable(fresh_container)

            print("SUCCESS: fresh_container imported without pytest")
        """)

        result = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f'Failed to import fresh_container without pytest.\nstdout: {result.stdout}\nstderr: {result.stderr}'
        )
        assert 'SUCCESS' in result.stdout

    def it_provides_pytest_fixtures_when_pytest_is_available(self) -> None:
        """Pytest fixtures work when pytest IS installed."""
        # This test runs in the normal pytest environment where pytest is available
        from dioxide.testing import (
            dioxide_container,
            dioxide_container_session,
            fresh_container_fixture,
        )

        # All fixtures should be available
        assert callable(dioxide_container)
        assert callable(fresh_container_fixture)
        assert callable(dioxide_container_session)
