"""Smoke test for installed dioxide package."""


def test_import() -> None:
    """Test that dioxide can be imported."""
    import dioxide

    assert dioxide is not None


def test_core_functionality() -> None:
    """Test basic DI functionality works."""
    from dioxide import Container, component

    @component
    class Service:
        pass

    @component
    class Consumer:
        def __init__(self, service: Service) -> None:
            self.service = service

    container = Container()
    container.scan()
    consumer = container.resolve(Consumer)

    assert consumer is not None
    assert isinstance(consumer.service, Service)


def test_singleton_scope() -> None:
    """Test singleton scope works correctly."""
    from dioxide import Container, Scope, component

    @component(scope=Scope.SINGLETON)
    class SingletonService:
        pass

    container = Container()
    container.scan()

    instance1 = container.resolve(SingletonService)
    instance2 = container.resolve(SingletonService)

    assert instance1 is instance2


def test_factory_scope() -> None:
    """Test factory scope works correctly."""
    from dioxide import Container, Scope, component

    @component(scope=Scope.FACTORY)
    class FactoryService:
        pass

    container = Container()
    container.scan()

    instance1 = container.resolve(FactoryService)
    instance2 = container.resolve(FactoryService)

    assert instance1 is not instance2


if __name__ == '__main__':
    test_import()
    test_core_functionality()
    test_singleton_scope()
    test_factory_scope()
    print('All smoke tests passed')
