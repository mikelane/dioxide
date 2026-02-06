"""Tests for scan statistics reporting (#384)."""

import pytest

from dioxide import (
    Container,
    Profile,
)
from dioxide.scan_stats import ScanStats


class DescribeScanStats:
    """Scan statistics reporting from container.scan()."""

    def it_returns_none_when_stats_not_requested(self) -> None:
        container = Container()
        result = container.scan()
        assert result is None

    def it_returns_scan_stats_when_stats_requested(self) -> None:
        container = Container()
        result = container.scan(stats=True)
        assert isinstance(result, ScanStats)

    def it_counts_services_registered(self) -> None:
        container = Container()
        result = container.scan(
            package='tests.fixtures.scan_stats_pkg',
            profile=Profile.PRODUCTION,
            stats=True,
        )
        assert result is not None
        assert result.services_registered == 3

    def it_counts_adapters_registered(self) -> None:
        container = Container()
        result = container.scan(
            package='tests.fixtures.scan_stats_pkg',
            profile=Profile.PRODUCTION,
            stats=True,
        )
        assert result is not None
        assert result.adapters_registered == 2

    def it_includes_duration_in_milliseconds(self) -> None:
        container = Container()
        result = container.scan(
            package='tests.fixtures.scan_stats_pkg',
            profile=Profile.PRODUCTION,
            stats=True,
        )
        assert result is not None
        assert result.duration_ms >= 0.0

    def it_counts_modules_imported(self) -> None:
        container = Container()
        result = container.scan(
            package='tests.fixtures.scan_stats_pkg',
            profile=Profile.PRODUCTION,
            stats=True,
        )
        assert result is not None
        assert result.modules_imported == 3

    def it_is_frozen_dataclass(self) -> None:
        container = Container()
        result = container.scan(stats=True)
        assert result is not None
        with pytest.raises(AttributeError):
            result.services_registered = 99  # type: ignore[misc]


class DescribeScanStatsBackwardCompatibility:
    """Existing scan() callers that ignore the return value still work."""

    def it_works_without_stats_parameter(self) -> None:
        container = Container()
        container.scan(package='tests.fixtures.scan_stats_pkg', profile=Profile.PRODUCTION)

        from tests.fixtures.scan_stats_pkg.services import AlphaService

        alpha = container.resolve(AlphaService)
        assert alpha.run() == 'alpha'

    def it_works_with_stats_false(self) -> None:
        container = Container()
        result = container.scan(
            package='tests.fixtures.scan_stats_pkg',
            profile=Profile.PRODUCTION,
            stats=False,
        )
        assert result is None
