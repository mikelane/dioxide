"""Tests for error guidance when decorators are misused.

Issue #399: Add error guidance for decorator misuse.
These tests verify that common decorator mistakes produce helpful,
actionable error messages guiding users toward correct usage.
"""

from __future__ import annotations

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeAdapterWithoutForCall:
    """Tests for using @adapter directly without .for_()."""

    def it_raises_type_error_when_used_as_class_decorator(self) -> None:
        with pytest.raises(TypeError, match=r'@adapter\.for_'):

            @adapter  # type: ignore[arg-type]
            class MyAdapter:
                pass

    def it_includes_the_class_name_in_the_error(self) -> None:
        with pytest.raises(TypeError, match='SendGridAdapter'):

            @adapter  # type: ignore[arg-type]
            class SendGridAdapter:
                pass

    def it_suggests_correct_usage_with_code_example(self) -> None:
        with pytest.raises(TypeError, match=r'@adapter\.for_\(YourPort'):

            @adapter  # type: ignore[arg-type]
            class MyAdapter:
                pass

    def it_raises_type_error_when_called_with_non_class(self) -> None:
        with pytest.raises(TypeError, match=r'@adapter cannot be used directly'):
            adapter(42)  # type: ignore[arg-type]

    def it_raises_type_error_when_called_with_string(self) -> None:
        with pytest.raises(TypeError, match=r'@adapter cannot be used directly'):
            adapter('not a class')  # type: ignore[arg-type]


class DescribeStackedServiceAndAdapter:
    """Tests for stacking @service and @adapter on the same class."""

    def it_raises_type_error_when_adapter_applied_to_service(self) -> None:
        class EmailPort(Protocol):
            def send(self) -> None: ...

        with pytest.raises(TypeError, match='both @service and @adapter'):

            @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            @service
            class SendGridAdapter:
                def send(self) -> None:
                    pass

    def it_raises_type_error_when_service_applied_to_adapter(self) -> None:
        class EmailPort(Protocol):
            def send(self) -> None: ...

        with pytest.raises(TypeError, match='both @service and @adapter'):

            @service
            @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            class SendGridAdapter:
                def send(self) -> None:
                    pass


class DescribeLifecycleWithoutRegistration:
    """Tests for using @lifecycle without @adapter or @service."""

    def it_warns_when_lifecycle_class_not_discovered_during_scan(self) -> None:
        @lifecycle
        class OrphanComponent:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        with pytest.warns(UserWarning, match='OrphanComponent.*@lifecycle.*not registered'):
            container.scan(profile=Profile.TEST)

    def it_suggests_adding_service_or_adapter_in_warning(self) -> None:
        @lifecycle
        class OrphanComponent:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        with pytest.warns(UserWarning, match='@service.*@adapter'):
            container.scan(profile=Profile.TEST)


class DescribeServiceUsedAsAdapter:
    """Tests for @service on a class that implements a port."""

    def it_suggests_adapter_when_service_implements_port(self) -> None:
        class EmailPort(Protocol):
            def send(self, to: str) -> None: ...

        @service
        class SendGridService:
            def send(self, to: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        with pytest.raises(Exception, match=r'SendGridService.*@adapter\.for_'):
            container.resolve(EmailPort)


class DescribeAdapterForWithWrongTypes:
    """Tests for providing wrong argument types to @adapter.for_()."""

    def it_raises_type_error_when_port_is_a_string(self) -> None:
        with pytest.raises(TypeError, match=r'port.*must be a class'):

            @adapter.for_('EmailPort')  # type: ignore[arg-type]
            class MyAdapter:
                pass

    def it_raises_type_error_when_port_is_an_integer(self) -> None:
        with pytest.raises(TypeError, match=r'port.*must be a class'):

            @adapter.for_(42)  # type: ignore[arg-type]
            class MyAdapter:
                pass

    def it_raises_type_error_when_port_is_none(self) -> None:
        with pytest.raises(TypeError, match=r'port.*must be a class'):

            @adapter.for_(None)  # type: ignore[arg-type]
            class MyAdapter:
                pass


class DescribeServiceWithWrongArguments:
    """Tests for providing wrong arguments to @service."""

    def it_raises_type_error_when_called_with_positional_non_class(self) -> None:
        with pytest.raises(TypeError, match=r'@service.*class'):
            service('not a class')  # type: ignore[call-overload]
