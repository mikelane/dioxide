"""Tests verifying deprecated APIs have been removed.

This module tests that the old @component, @component.factory, @component.implements,
and @profile decorators have been completely removed as of v0.1.0-beta.
Users should use @service and @adapter.for_() instead.
"""

import pytest


class DescribeDeprecatedAPIRemoval:
    """Tests that deprecated APIs are no longer importable."""

    def it_raises_import_error_for_component(self) -> None:
        """@component decorator is no longer available."""
        with pytest.raises(ImportError, match=r'cannot import name.*component'):
            from dioxide import component  # noqa: F401

    def it_raises_import_error_for_profile(self) -> None:
        """@profile decorator is no longer available."""
        with pytest.raises(ImportError, match=r'cannot import name.*profile'):
            from dioxide import profile  # noqa: F401

    def it_does_not_export_component_in_all(self) -> None:
        """__all__ no longer includes 'component'."""
        from dioxide import __all__

        assert 'component' not in __all__
        assert 'profile' not in __all__

    def it_does_not_export_profile_in_all(self) -> None:
        """__all__ no longer includes 'profile'."""
        from dioxide import __all__

        assert 'profile' not in __all__


class DescribeDeprecatedModules:
    """Tests that deprecated modules have been removed."""

    def it_raises_import_error_for_decorators_module(self) -> None:
        """dioxide.decorators module is no longer available."""
        with pytest.raises(ImportError, match=r'No module named.*decorators'):
            import dioxide.decorators  # type: ignore[import-not-found]  # noqa: F401

    def it_raises_import_error_for_profile_module(self) -> None:
        """dioxide.profile module is no longer available."""
        with pytest.raises(ImportError, match=r'No module named.*profile'):
            import dioxide.profile  # type: ignore[import-not-found]  # noqa: F401


class DescribeReplacementAPIs:
    """Tests that replacement APIs are available."""

    def it_exports_service(self) -> None:
        """@service is available as replacement for @component."""
        from dioxide import service

        assert service is not None
        assert callable(service)

    def it_exports_adapter(self) -> None:
        """@adapter.for_() is available as replacement for @component.implements."""
        from dioxide import adapter

        assert adapter is not None
        assert hasattr(adapter, 'for_')
        assert callable(adapter.for_)

    def it_exports_profile_enum(self) -> None:
        """Profile enum is available for profile parameter."""
        from dioxide import Profile

        assert Profile is not None
        assert hasattr(Profile, 'PRODUCTION')
        assert hasattr(Profile, 'TEST')
        assert hasattr(Profile, 'DEVELOPMENT')
