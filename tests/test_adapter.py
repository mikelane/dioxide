"""Tests for @adapter decorator for hexagonal architecture.

The @adapter decorator enables marking concrete implementations for
Protocol/ABC ports with explicit profile associations, supporting
hexagonal/ports-and-adapters architecture patterns.
"""

from typing import Protocol

from dioxide import (
    Scope,
    adapter,
)


class EmailPort(Protocol):
    """Test protocol for email functionality."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class DescribeAdapterDecorator:
    """Tests for @adapter.for() decorator functionality."""

    def it_requires_port_and_profile_parameters(self) -> None:
        """@adapter.for() requires port and profile parameters."""

        @adapter.for_(EmailPort, profile='production')
        class TestAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert TestAdapter is not None

    def it_registers_with_port_and_profile(self) -> None:
        """@adapter.for() registers implementation for port + profile."""

        @adapter.for_(EmailPort, profile='production')
        class ProductionAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Verify registration metadata
        assert hasattr(ProductionAdapter, '__dioxide_port__')
        assert ProductionAdapter.__dioxide_port__ is EmailPort
        assert hasattr(ProductionAdapter, '__dioxide_profiles__')
        assert 'production' in ProductionAdapter.__dioxide_profiles__

    def it_accepts_string_profile(self) -> None:
        """@adapter.for() accepts string profiles for custom environments."""

        @adapter.for_(EmailPort, profile='staging')
        class StagingAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert hasattr(StagingAdapter, '__dioxide_profiles__')
        assert 'staging' in StagingAdapter.__dioxide_profiles__

    def it_supports_multiple_profiles_list(self) -> None:
        """@adapter.for() accepts list of profiles."""

        @adapter.for_(EmailPort, profile=['test', 'development'])
        class MultiProfileAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert hasattr(MultiProfileAdapter, '__dioxide_profiles__')
        assert 'test' in MultiProfileAdapter.__dioxide_profiles__
        assert 'development' in MultiProfileAdapter.__dioxide_profiles__

    def it_defaults_to_all_profiles_when_profile_omitted(self) -> None:
        """@adapter.for() defaults to '*' (all profiles) when profile is omitted."""

        @adapter.for_(EmailPort)
        class DefaultProfileAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert hasattr(DefaultProfileAdapter, '__dioxide_profiles__')
        assert '*' in DefaultProfileAdapter.__dioxide_profiles__

    def it_defaults_to_singleton_scope(self) -> None:
        """@adapter.for() uses SINGLETON scope by default."""

        @adapter.for_(EmailPort, profile='production')
        class SingletonAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert hasattr(SingletonAdapter, '__dioxide_scope__')
        assert SingletonAdapter.__dioxide_scope__ == Scope.SINGLETON

    def it_normalizes_profiles_to_lowercase(self) -> None:
        """@adapter.for() normalizes profile names to lowercase."""

        @adapter.for_(EmailPort, profile='PRODUCTION')
        class UppercaseAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        assert 'production' in UppercaseAdapter.__dioxide_profiles__
        assert 'PRODUCTION' not in UppercaseAdapter.__dioxide_profiles__

    def it_deduplicates_profile_list(self) -> None:
        """@adapter.for() deduplicates repeated profiles."""

        @adapter.for_(EmailPort, profile=['test', 'TEST', 'test'])
        class DuplicateAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Should only have one 'test' after normalization
        assert 'test' in DuplicateAdapter.__dioxide_profiles__
        assert len(DuplicateAdapter.__dioxide_profiles__) == 1
