"""Smoke test for installed dioxide package."""

import dioxide
from dioxide import (
    Container,
    service,
)


def test_import() -> None:
    """Test that dioxide can be imported."""
    assert dioxide is not None


def test_core_functionality() -> None:
    """Test basic DI functionality works."""

    @service
    class Service:
        pass

    @service
    class Consumer:
        def __init__(self, service: Service) -> None:
            self.service = service

    container = Container()
    container.scan()
    consumer = container.resolve(Consumer)

    assert consumer is not None
    assert isinstance(consumer.service, Service)


def test_singleton_scope() -> None:
    """Test singleton scope works correctly (services are always singletons)."""

    @service
    class SingletonService:
        pass

    container = Container()
    container.scan()

    instance1 = container.resolve(SingletonService)
    instance2 = container.resolve(SingletonService)

    assert instance1 is instance2


if __name__ == '__main__':
    test_import()
    test_core_functionality()
    test_singleton_scope()
    print('All smoke tests passed')
