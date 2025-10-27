"""
Edge case tests for RustContainer behavior.

These tests verify the Rust container implementation handles:
- Singleton caching
- Recursive resolution
- Mixed lifecycles
- Deep dependency chains
- Circular dependencies
"""

import pytest

from dioxide._dioxide_core import Container as RustContainer


class DescribeRustContainerSingletonCaching:
    """Tests for singleton factory caching behavior."""

    def it_calls_singleton_factory_only_once(self) -> None:
        """Singleton factory is called exactly once across multiple resolutions."""
        container = RustContainer()
        call_count = {'count': 0}

        class Service:
            pass

        def factory() -> Service:
            call_count['count'] += 1
            return Service()

        container.register_singleton_factory(Service, factory)

        # Resolve multiple times
        first = container.resolve(Service)
        second = container.resolve(Service)
        third = container.resolve(Service)

        # Factory should only be called once
        assert call_count['count'] == 1
        # All resolutions should return the same instance
        assert first is second is third

    def it_calls_transient_factory_every_time(self) -> None:
        """Class provider creates new instance on every resolution."""
        container = RustContainer()
        call_count = {'count': 0}

        class Service:
            def __init__(self) -> None:
                call_count['count'] += 1
                self.instance_num = call_count['count']

        container.register_class(Service, Service)

        # Resolve multiple times
        first = container.resolve(Service)
        second = container.resolve(Service)
        third = container.resolve(Service)

        # Class should be instantiated three times
        assert call_count['count'] == 3
        # Each resolution should return a different instance
        assert first.instance_num == 1
        assert second.instance_num == 2
        assert third.instance_num == 3
        assert first is not second is not third


class DescribeRustContainerRecursiveResolution:
    """Tests for factories that resolve dependencies."""

    def it_resolves_dependencies_from_within_factory(self) -> None:
        """Factories can resolve their dependencies using the container."""
        container = RustContainer()

        class Config:
            def __init__(self) -> None:
                self.host = 'localhost'

        class Database:
            def __init__(self, config: Config) -> None:
                self.config = config

        # Register config as instance
        container.register_instance(Config, Config())

        # Register factory that resolves the dependency
        def database_factory() -> Database:
            config = container.resolve(Config)
            return Database(config)

        container.register_singleton_factory(Database, database_factory)

        result = container.resolve(Database)
        assert isinstance(result, Database)
        assert result.config.host == 'localhost'


class DescribeRustContainerMixedLifecycles:
    """Tests for mixing singleton and transient dependencies."""

    def it_allows_singleton_to_depend_on_transient(self) -> None:
        """Singleton factory can resolve a transient dependency."""
        container = RustContainer()
        transient_calls = {'count': 0}

        class TransientService:
            def __init__(self) -> None:
                transient_calls['count'] += 1
                self.num = transient_calls['count']

        class SingletonService:
            def __init__(self, transient: TransientService) -> None:
                self.transient = transient

        # Register transient as class (new instance each time)
        container.register_class(TransientService, TransientService)

        # Register singleton factory that resolves transient
        def singleton_factory() -> SingletonService:
            transient = container.resolve(TransientService)
            return SingletonService(transient)

        container.register_singleton_factory(SingletonService, singleton_factory)

        # First resolution - singleton factory called, resolves transient
        first = container.resolve(SingletonService)
        # Second resolution - singleton cached, transient NOT resolved again
        second = container.resolve(SingletonService)

        # Singleton factory only called once
        assert first is second
        # Transient only called once (during singleton creation)
        assert transient_calls['count'] == 1
        assert first.transient.num == 1

    def it_allows_transient_to_depend_on_singleton(self) -> None:
        """Transient can resolve a singleton dependency."""
        container = RustContainer()
        singleton_calls = {'count': 0}

        class SingletonService:
            def __init__(self) -> None:
                singleton_calls['count'] += 1
                self.num = singleton_calls['count']

        class TransientService:
            def __init__(self, singleton: SingletonService) -> None:
                self.singleton = singleton

        # Register singleton as factory
        def singleton_factory() -> SingletonService:
            return SingletonService()

        container.register_singleton_factory(SingletonService, singleton_factory)

        # Register transient as class that resolves singleton
        # Since we can't inject in __init__ directly, use a factory
        def transient_factory() -> TransientService:
            singleton = container.resolve(SingletonService)
            return TransientService(singleton)

        container.register_transient_factory(TransientService, transient_factory)

        # Multiple resolutions - transient called each time
        first = container.resolve(TransientService)
        second = container.resolve(TransientService)
        third = container.resolve(TransientService)

        # Singleton factory only called once
        assert singleton_calls['count'] == 1
        # Each transient gets the same singleton
        assert first.singleton is second.singleton is third.singleton
        assert first.singleton.num == 1


class DescribeRustContainerDeepDependencyChains:
    """Tests for deep chains of dependencies."""

    def it_resolves_deep_dependency_chains(self) -> None:
        """Dependencies resolve correctly multiple levels deep."""
        container = RustContainer()

        class Config:
            def __init__(self) -> None:
                self.value = 'base-config'

        class ServiceD:
            def __init__(self, config: Config) -> None:
                self.config = config

        class ServiceC:
            def __init__(self, d: ServiceD) -> None:
                self.d = d

        class ServiceB:
            def __init__(self, c: ServiceC) -> None:
                self.c = c

        class ServiceA:
            def __init__(self, b: ServiceB) -> None:
                self.b = b

        # Chain: ServiceA -> ServiceB -> ServiceC -> ServiceD -> Config
        container.register_instance(Config, Config())

        def factory_d() -> ServiceD:
            config = container.resolve(Config)
            return ServiceD(config)

        def factory_c() -> ServiceC:
            d = container.resolve(ServiceD)
            return ServiceC(d)

        def factory_b() -> ServiceB:
            c = container.resolve(ServiceC)
            return ServiceB(c)

        def factory_a() -> ServiceA:
            b = container.resolve(ServiceB)
            return ServiceA(b)

        container.register_singleton_factory(ServiceD, factory_d)
        container.register_singleton_factory(ServiceC, factory_c)
        container.register_singleton_factory(ServiceB, factory_b)
        container.register_singleton_factory(ServiceA, factory_a)

        result = container.resolve(ServiceA)
        assert isinstance(result, ServiceA)
        assert isinstance(result.b, ServiceB)
        assert isinstance(result.b.c, ServiceC)
        assert isinstance(result.b.c.d, ServiceD)
        assert result.b.c.d.config.value == 'base-config'

    def it_caches_singletons_in_deep_chains(self) -> None:
        """Singletons are properly cached even in deep dependency chains."""
        container = RustContainer()
        singleton_calls = {'count': 0}

        class Config:
            def __init__(self) -> None:
                self.value = 'base'

        class SingletonService:
            def __init__(self, config: Config) -> None:
                singleton_calls['count'] += 1
                self.config = config
                self.num = singleton_calls['count']

        class TransientService:
            def __init__(self, singleton: SingletonService) -> None:
                self.singleton = singleton

        container.register_instance(Config, Config())

        def singleton_factory() -> SingletonService:
            config = container.resolve(Config)
            return SingletonService(config)

        def transient_factory() -> TransientService:
            singleton = container.resolve(SingletonService)
            return TransientService(singleton)

        container.register_singleton_factory(SingletonService, singleton_factory)
        container.register_transient_factory(TransientService, transient_factory)

        # Resolve transient multiple times
        first = container.resolve(TransientService)
        second = container.resolve(TransientService)
        third = container.resolve(TransientService)

        # Singleton only created once
        assert singleton_calls['count'] == 1
        # All transients get same singleton
        assert first.singleton is second.singleton is third.singleton
        assert first.singleton.num == 1


class DescribeRustContainerCircularDependencies:
    """Tests for circular dependency detection."""

    @pytest.mark.skip(reason='Circular dependency detection not yet implemented in Rust container')
    def it_detects_direct_circular_dependencies(self) -> None:
        """Detects when service A depends on service B which depends on A."""
        container = RustContainer()

        class ServiceA:
            pass

        class ServiceB:
            pass

        def factory_a() -> ServiceA:
            container.resolve(ServiceB)
            return ServiceA()

        def factory_b() -> ServiceB:
            container.resolve(ServiceA)
            return ServiceB()

        container.register_singleton_factory(ServiceA, factory_a)
        container.register_singleton_factory(ServiceB, factory_b)

        # Should raise an error about circular dependency
        with pytest.raises(Exception) as exc_info:
            container.resolve(ServiceA)

        # Error message should mention circular or recursion
        error_msg = str(exc_info.value).lower()
        assert 'circular' in error_msg or 'recursion' in error_msg or 'cycle' in error_msg

    @pytest.mark.skip(reason='Circular dependency detection not yet implemented in Rust container')
    def it_detects_indirect_circular_dependencies(self) -> None:
        """Detects circular dependencies through multiple services (A -> B -> C -> A)."""
        container = RustContainer()

        class ServiceA:
            pass

        class ServiceB:
            pass

        class ServiceC:
            pass

        def factory_a() -> ServiceA:
            container.resolve(ServiceB)
            return ServiceA()

        def factory_b() -> ServiceB:
            container.resolve(ServiceC)
            return ServiceB()

        def factory_c() -> ServiceC:
            container.resolve(ServiceA)
            return ServiceC()

        container.register_singleton_factory(ServiceA, factory_a)
        container.register_singleton_factory(ServiceB, factory_b)
        container.register_singleton_factory(ServiceC, factory_c)

        # Should raise an error about circular dependency
        with pytest.raises(Exception) as exc_info:
            container.resolve(ServiceA)

        error_msg = str(exc_info.value).lower()
        assert 'circular' in error_msg or 'recursion' in error_msg or 'cycle' in error_msg

    @pytest.mark.skip(reason='Circular dependency detection not yet implemented in Rust container')
    def it_detects_self_dependency(self) -> None:
        """Detects when a service tries to resolve itself."""
        container = RustContainer()

        class ServiceA:
            pass

        def factory_a() -> ServiceA:
            container.resolve(ServiceA)
            return ServiceA()

        container.register_singleton_factory(ServiceA, factory_a)

        # Should raise an error about circular dependency
        with pytest.raises(Exception) as exc_info:
            container.resolve(ServiceA)

        error_msg = str(exc_info.value).lower()
        assert 'circular' in error_msg or 'recursion' in error_msg or 'cycle' in error_msg
