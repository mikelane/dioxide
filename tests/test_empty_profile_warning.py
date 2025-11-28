"""Tests for empty profile warning in container.scan() (Issue #87).

When a profile matches zero components during container.scan(), a warning
should be logged to help users identify typos or misconfiguration.
"""

from __future__ import annotations

import logging
from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
)


class DescribeContainerScanEmptyProfileWarning:
    """Tests for warning when profile matches zero components."""

    def it_warns_when_profile_matches_no_components(self, caplog: pytest.LogCaptureFixture) -> None:
        """Logs warning when profile matches zero components."""
        container = Container()

        with caplog.at_level(logging.WARNING):
            container.scan(profile='nonexistent_profile')

        assert 'matched zero components' in caplog.text
        assert 'nonexistent_profile' in caplog.text

    def it_warns_when_profile_enum_matches_no_components(self, caplog: pytest.LogCaptureFixture) -> None:
        """Logs warning when Profile enum matches zero components."""
        container = Container()

        with caplog.at_level(logging.WARNING):
            container.scan(profile=Profile.STAGING)

        assert 'matched zero components' in caplog.text
        assert 'staging' in caplog.text.lower()

    def it_does_not_warn_when_profile_matches_components(self, caplog: pytest.LogCaptureFixture) -> None:
        """Does not log warning when profile matches at least one component."""

        class SomePort(Protocol):
            def do_something(self) -> None: ...

        @adapter.for_(SomePort, profile=Profile.TEST)
        class TestAdapter:
            def do_something(self) -> None:
                pass

        container = Container()

        with caplog.at_level(logging.WARNING):
            container.scan(profile=Profile.TEST)

        assert 'matched zero components' not in caplog.text

    def it_does_not_warn_when_no_profile_specified(self, caplog: pytest.LogCaptureFixture) -> None:
        """Does not log warning when scanning without profile filter."""
        container = Container()

        with caplog.at_level(logging.WARNING):
            container.scan()

        assert 'matched zero components' not in caplog.text

    def it_suggests_checking_decorator_usage(self, caplog: pytest.LogCaptureFixture) -> None:
        """Warning message suggests checking @adapter.for_() decorators."""
        container = Container()

        with caplog.at_level(logging.WARNING):
            container.scan(profile='nonexistent')

        assert '@adapter.for_()' in caplog.text or 'decorator' in caplog.text.lower()
