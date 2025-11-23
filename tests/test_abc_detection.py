"""Tests for ABC detection in container."""

from abc import (
    ABC,
    abstractmethod,
)

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


class DescribeABCDetection:
    """Tests for ABC (Abstract Base Class) detection."""

    def it_detects_abc_classes_as_ports(self) -> None:
        """Detects ABC classes as ports for adapter resolution."""

        # Arrange: Define an ABC port
        class EmailPort(ABC):
            @abstractmethod
            def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Define an adapter
        @adapter.for_(EmailPort)
        class FakeEmailAdapter:
            def send(self, to: str, subject: str, body: str) -> None:
                pass

        # Act: Scan container
        container = Container()
        container.scan()

        # Assert: Can resolve port to adapter
        email = container.resolve(EmailPort)
        assert isinstance(email, FakeEmailAdapter)

    def it_handles_non_protocol_non_abc_classes(self) -> None:
        """Handles regular classes that are not Protocols or ABCs."""

        # Arrange: Regular component
        @service
        class RegularService:
            def do_something(self) -> str:
                return 'done'

        # Act: Scan container
        container = Container()
        container.scan()

        # Assert: Can resolve regular component
        regular_service = container.resolve(RegularService)
        assert regular_service.do_something() == 'done'

    def it_handles_abc_with_profile_filtering(self) -> None:
        """Handles ABC ports with profile-based adapter selection."""

        # Arrange: ABC port with profile-specific adapters
        class StoragePort(ABC):
            @abstractmethod
            def save(self, data: str) -> None:
                pass

        @adapter.for_(StoragePort, profile=Profile.PRODUCTION)
        class ProductionStorage:
            def save(self, data: str) -> None:
                pass

        @adapter.for_(StoragePort, profile=Profile.TEST)
        class FakeStorage:
            def save(self, data: str) -> None:
                pass

        # Act: Scan with test profile
        container = Container()
        container.scan(profile=Profile.TEST)

        # Assert: Test adapter is selected
        storage = container.resolve(StoragePort)
        assert isinstance(storage, FakeStorage)
