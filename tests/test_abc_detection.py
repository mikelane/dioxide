"""Tests for ABC detection in container."""

from abc import (
    ABC,
    abstractmethod,
)

from dioxide import (
    Container,
    adapter,
    component,
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
        @component
        class RegularService:
            def do_something(self) -> str:
                return 'done'

        # Act: Scan container
        container = Container()
        container.scan()

        # Assert: Can resolve regular component
        service = container.resolve(RegularService)
        assert service.do_something() == 'done'
