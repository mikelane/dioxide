"""Tests for documentation version configuration."""

from __future__ import annotations

import sys
from pathlib import Path

import dioxide


class DescribeDocumentationVersioning:
    """Tests for version configuration in Sphinx documentation."""

    def it_extracts_version_from_package(self) -> None:
        """Version is extracted from dioxide.__version__."""
        version = dioxide.__version__
        assert isinstance(version, str)
        assert len(version.split('.')) >= 2  # At least X.Y

    def it_extracts_short_version_correctly(self) -> None:
        """Short version (X.Y) is extracted from full version."""
        full_version = '0.1.0-beta.2'
        short_version = '.'.join(full_version.split('.')[:2])
        assert short_version == '0.1'

    def it_handles_versions_without_prerelease(self) -> None:
        """Short version works for stable releases."""
        full_version = '1.2.3'
        short_version = '.'.join(full_version.split('.')[:2])
        assert short_version == '1.2'

    def it_can_import_sphinx_conf_module(self) -> None:
        """Sphinx conf.py can be imported without errors."""
        # Add docs directory to path temporarily
        docs_path = Path(__file__).parent.parent / 'docs'
        sys.path.insert(0, str(docs_path.parent))

        try:
            # Import the conf module
            import docs.conf as conf

            # Verify version variables are set
            assert hasattr(conf, 'version')
            assert hasattr(conf, 'release')
            assert hasattr(conf, 'project')

            # Verify version format
            assert isinstance(conf.version, str)
            assert isinstance(conf.release, str)
            assert conf.project == 'dioxide'

            # Short version should be X.Y format
            version_parts = conf.version.split('.')
            assert len(version_parts) == 2, f'Expected X.Y format, got {conf.version}'

        finally:
            # Clean up path
            sys.path.pop(0)

    def it_synchronizes_version_with_package(self) -> None:
        """Sphinx conf version matches package version."""
        # Add docs directory to path temporarily
        docs_path = Path(__file__).parent.parent / 'docs'
        sys.path.insert(0, str(docs_path.parent))

        try:
            import docs.conf as conf

            package_version = dioxide.__version__
            expected_short = '.'.join(package_version.split('.')[:2])

            assert conf.version == expected_short
            assert conf.release == package_version

        finally:
            sys.path.pop(0)
