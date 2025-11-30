"""Tests for container.reset() method.

The reset() method clears the singleton cache while preserving
provider registrations. This enables test isolation without re-scanning.
"""

from __future__ import annotations

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class DescribeContainerReset:
    """Tests for container.reset() method."""

    def it_clears_singleton_cache(self) -> None:
        """After reset, resolve returns new instance."""
        # Arrange
        container = Container()
        call_count = 0

        @service
        class CountingService:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

        container.scan()
        first_instance = container.resolve(CountingService)
        assert call_count == 1

        # Verify singleton behavior (same instance)
        second_instance = container.resolve(CountingService)
        assert second_instance is first_instance
        assert call_count == 1  # Factory not called again

        # Act
        container.reset()

        # Assert - new instance after reset
        third_instance = container.resolve(CountingService)
        assert third_instance is not first_instance
        assert call_count == 2  # Factory called again

    def it_preserves_provider_registrations(self) -> None:
        """After reset, can still resolve without re-scanning."""
        # Arrange
        container = Container()

        @service
        class MyService:
            pass

        container.scan()
        container.resolve(MyService)  # Ensure it works

        # Act
        container.reset()

        # Assert - should still be able to resolve without re-scanning
        instance = container.resolve(MyService)
        assert instance is not None
        assert isinstance(instance, MyService)

    def it_clears_lifecycle_instances_cache(self) -> None:
        """After reset, lifecycle cache is cleared.

        Note: This test directly manipulates the internal _lifecycle_instances
        attribute to verify cache clearing without requiring async lifecycle
        setup/teardown. This is intentional for test simplicity.
        """
        # Arrange
        container = Container()
        container._lifecycle_instances = ['fake_instance']  # Simulate cached lifecycle

        # Act
        container.reset()

        # Assert
        assert container._lifecycle_instances is None

    def it_works_with_adapters(self) -> None:
        """Reset clears adapter singleton cache too."""
        # Arrange
        container = Container()
        call_count = 0

        class EmailPort(Protocol):
            def send(self) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

            def send(self) -> None:
                pass

        container.scan(profile=Profile.TEST)
        first_adapter = container.resolve(EmailPort)
        assert call_count == 1

        # Verify singleton behavior
        second_adapter = container.resolve(EmailPort)
        assert second_adapter is first_adapter
        assert call_count == 1

        # Act
        container.reset()

        # Assert - new instance after reset
        third_adapter = container.resolve(EmailPort)
        assert third_adapter is not first_adapter
        assert call_count == 2

    def it_enables_test_isolation_pattern(self) -> None:
        """Demonstrates the pytest fixture pattern from MLP_VISION.md."""
        # This test demonstrates the intended usage pattern:
        #
        # @pytest.fixture(autouse=True)
        # def setup_container():
        #     container.scan(profile=Profile.TEST)
        #     yield
        #     container.reset()  # Fresh instances for next test

        # Arrange
        container = Container()
        instance_ids: list[int] = []

        @service
        class StatefulService:
            def __init__(self) -> None:
                instance_ids.append(id(self))

        container.scan()

        # Simulate test 1
        container.resolve(StatefulService)
        assert len(instance_ids) == 1

        # Reset between tests
        container.reset()

        # Simulate test 2
        container.resolve(StatefulService)
        assert len(instance_ids) == 2
        assert instance_ids[0] != instance_ids[1]  # Different instances

    def it_handles_reset_on_empty_container(self) -> None:
        """Reset on empty container does not raise."""
        container = Container()
        # Should not raise
        container.reset()
        assert container.is_empty()

    def it_handles_multiple_sequential_resets(self) -> None:
        """Multiple resets work correctly."""

        @service
        class SequentialService:
            pass

        container = Container()
        container.scan()

        first = container.resolve(SequentialService)
        container.reset()
        second = container.resolve(SequentialService)
        container.reset()
        third = container.resolve(SequentialService)

        assert first is not second
        assert second is not third
        assert first is not third


class DescribeContainerResetWithManualRegistration:
    """Tests for reset with manual registration methods."""

    def it_clears_singleton_factory_cache(self) -> None:
        """Reset clears cache for register_singleton_factory."""
        # Arrange
        container = Container()
        call_count = 0

        class Config:
            def __init__(self) -> None:
                nonlocal call_count
                call_count += 1

        container.register_singleton_factory(Config, Config)
        first_config = container.resolve(Config)
        assert call_count == 1

        # Act
        container.reset()

        # Assert
        second_config = container.resolve(Config)
        assert second_config is not first_config
        assert call_count == 2

    def it_preserves_transient_factory_behavior(self) -> None:
        """Transient factories continue to work after reset."""
        # Arrange
        container = Container()

        class Request:
            pass

        container.register_transient_factory(Request, Request)

        # Get different instances before reset
        req1 = container.resolve(Request)
        req2 = container.resolve(Request)
        assert req1 is not req2

        # Act
        container.reset()

        # Assert - transient still works
        req3 = container.resolve(Request)
        req4 = container.resolve(Request)
        assert req3 is not req4

    def it_preserves_instance_registrations(self) -> None:
        """Instance registrations remain after reset."""
        # Arrange
        container = Container()

        class Config:
            def __init__(self, value: str) -> None:
                self.value = value

        original_config = Config('original')
        container.register_instance(Config, original_config)

        # Act
        container.reset()

        # Assert - instance registration should still work
        resolved_config = container.resolve(Config)
        assert resolved_config is original_config
        assert resolved_config.value == 'original'


class DescribeResetGlobalContainer:
    """Tests for reset_global_container() function.

    This function resets the global singleton container to an empty state,
    primarily intended for testing isolation scenarios.
    """

    def it_resets_global_container_to_empty_state(self) -> None:
        """reset_global_container() clears the global container."""
        from dioxide import (
            container,
            reset_global_container,
            service,
        )

        @service
        class TestService:
            pass

        # Setup: scan and resolve to populate container
        container.scan()
        container.resolve(TestService)
        assert not container.is_empty()

        # Act
        reset_global_container()

        # Assert - container should be empty (no registrations)
        assert container.is_empty()

    def it_allows_rescanning_after_reset(self) -> None:
        """After reset, container can be scanned and used again."""
        from dioxide import (
            container,
            reset_global_container,
            service,
        )

        @service
        class RescannableService:
            pass

        container.scan()
        first_instance = container.resolve(RescannableService)

        # Act
        reset_global_container()
        container.scan()

        # Assert - can resolve after rescanning
        second_instance = container.resolve(RescannableService)
        assert second_instance is not first_instance

    def it_is_exported_from_main_package(self) -> None:
        """reset_global_container is importable from dioxide."""
        from dioxide import reset_global_container

        assert callable(reset_global_container)

    def it_clears_active_profile(self) -> None:
        """After reset, active profile is cleared."""
        from dioxide import (
            Profile,
            container,
            reset_global_container,
        )

        container.scan(profile=Profile.TEST)
        assert container._active_profile == 'test'

        # Act
        reset_global_container()

        # Assert
        assert container._active_profile is None

    def it_clears_lifecycle_cache(self) -> None:
        """After reset, lifecycle cache is cleared."""
        from dioxide import (
            container,
            reset_global_container,
        )

        # Simulate cached lifecycle instances
        container._lifecycle_instances = ['fake_instance']

        # Act
        reset_global_container()

        # Assert
        assert container._lifecycle_instances is None

    def it_does_not_raise_on_empty_container(self) -> None:
        """reset_global_container() works on an empty container."""
        from dioxide import (
            container,
            reset_global_container,
        )

        # Ensure container is empty
        reset_global_container()
        assert container.is_empty()

        # Act - should not raise even if already empty
        reset_global_container()

        # Assert
        assert container.is_empty()
