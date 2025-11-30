"""Tests for ScopedContainer API with create_scope() context manager.

This module tests the scoped container functionality introduced in issue #181,
which provides explicit scope lifecycle management through an async context
manager pattern.

The ScopedContainer enables request-scoped dependency injection that works
across all contexts (web, CLI, background tasks, tests) with a universal API.
"""

import uuid
from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    Scope,
    ScopedContainer,
    adapter,
    lifecycle,
    service,
)
from dioxide.exceptions import (
    CaptiveDependencyError,
    ScopeError,
)


class DescribeScopedContainerCreation:
    """Tests for container.create_scope() async context manager."""

    @pytest.mark.asyncio
    async def it_returns_scoped_container_from_create_scope(self) -> None:
        """create_scope() returns a ScopedContainer instance."""
        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            assert isinstance(scope, ScopedContainer)

    @pytest.mark.asyncio
    async def it_provides_unique_scope_id_for_each_scope(self) -> None:
        """Each scope has a unique identifier."""

        container = Container()
        container.scan()

        scope_ids: list[str] = []

        async with container.create_scope() as scope1:
            scope_ids.append(scope1.scope_id)

        async with container.create_scope() as scope2:
            scope_ids.append(scope2.scope_id)

        async with container.create_scope() as scope3:
            scope_ids.append(scope3.scope_id)

        # All scope IDs should be unique
        assert len(scope_ids) == len(set(scope_ids))

    @pytest.mark.asyncio
    async def it_raises_error_for_nested_scopes_in_v0_3(self) -> None:
        """Nested scopes raise error (v0.3.0 restriction)."""
        container = Container()
        container.scan()

        async with container.create_scope() as outer_scope:
            # Trying to create nested scope should raise ScopeError
            with pytest.raises(ScopeError, match='Nested scopes are not supported'):
                async with outer_scope.create_scope():
                    pass


class DescribeScopedContainerResolution:
    """Tests for ScopedContainer.resolve() behavior."""

    @pytest.mark.asyncio
    async def it_resolves_singleton_from_parent_container(self) -> None:
        """SINGLETON scope returns shared instance from parent container."""

        @service
        class SingletonService:
            pass

        container = Container()
        container.scan()

        # Resolve from parent container first
        parent_instance = container.resolve(SingletonService)

        async with container.create_scope() as scope:
            # Resolve from scoped container
            scoped_instance = scope.resolve(SingletonService)

            # Should be same instance as parent (singleton shared)
            assert scoped_instance is parent_instance

    @pytest.mark.asyncio
    async def it_caches_request_scoped_instances_within_scope(self) -> None:
        """REQUEST scope returns same instance within a single scope."""

        @service(scope=Scope.REQUEST)
        class RequestScopedService:
            def __init__(self) -> None:
                self.id = str(uuid.uuid4())

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            # Multiple resolutions within same scope
            instance1 = scope.resolve(RequestScopedService)
            instance2 = scope.resolve(RequestScopedService)
            instance3 = scope.resolve(RequestScopedService)

            # All should be same instance (cached within scope)
            assert instance1 is instance2
            assert instance2 is instance3

    @pytest.mark.asyncio
    async def it_creates_fresh_request_instances_per_scope(self) -> None:
        """REQUEST scope creates fresh instances for each new scope."""

        @service(scope=Scope.REQUEST)
        class RequestScopedService:
            def __init__(self) -> None:
                self.id = str(uuid.uuid4())

        container = Container()
        container.scan()

        instances: list[object] = []

        async with container.create_scope() as scope1:
            instances.append(scope1.resolve(RequestScopedService))

        async with container.create_scope() as scope2:
            instances.append(scope2.resolve(RequestScopedService))

        async with container.create_scope() as scope3:
            instances.append(scope3.resolve(RequestScopedService))

        # Each scope should have a different instance
        assert len(instances) == 3
        assert instances[0] is not instances[1]
        assert instances[1] is not instances[2]
        assert instances[0] is not instances[2]

    @pytest.mark.asyncio
    async def it_creates_new_factory_instance_each_resolution(self) -> None:
        """FACTORY scope creates new instance on each resolve(), even in scope."""

        @service(scope=Scope.FACTORY)
        class FactoryService:
            def __init__(self) -> None:
                self.id = str(uuid.uuid4())

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            # Multiple resolutions
            instance1 = scope.resolve(FactoryService)
            instance2 = scope.resolve(FactoryService)
            instance3 = scope.resolve(FactoryService)

            # Each should be different (factory creates new each time)
            assert instance1 is not instance2
            assert instance2 is not instance3
            assert instance1 is not instance3

    @pytest.mark.asyncio
    async def it_supports_bracket_syntax_for_resolution(self) -> None:
        """ScopedContainer[Type] works like scope.resolve(Type)."""

        @service
        class MyService:
            pass

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            # Bracket syntax
            via_bracket = scope[MyService]
            via_resolve = scope.resolve(MyService)

            # Same instance (singleton)
            assert via_bracket is via_resolve


class DescribeRequestScopeOutsideScope:
    """Tests for REQUEST scope resolution outside of a scope context."""

    @pytest.mark.asyncio
    async def it_raises_scope_error_when_resolving_request_outside_scope(self) -> None:
        """Resolving REQUEST component outside scope raises ScopeError."""

        @service(scope=Scope.REQUEST)
        class RequestScopedService:
            pass

        container = Container()
        container.scan()

        # Trying to resolve REQUEST-scoped component from parent container
        with pytest.raises(ScopeError, match=r'REQUEST-scoped.*require.*scope'):
            container.resolve(RequestScopedService)

    @pytest.mark.asyncio
    async def it_provides_helpful_error_message_for_request_outside_scope(self) -> None:
        """Error message explains how to fix REQUEST outside scope."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            pass

        container = Container()
        container.scan()

        with pytest.raises(ScopeError) as exc_info:
            container.resolve(RequestContext)

        error_message = str(exc_info.value)
        # Error should mention:
        # 1. The component that failed
        assert 'RequestContext' in error_message
        # 2. That it's REQUEST scoped
        assert 'REQUEST' in error_message
        # 3. How to fix (create_scope)
        assert 'create_scope' in error_message


class DescribeCaptiveDependency:
    """Tests for captive dependency detection (SINGLETON depends on REQUEST)."""

    @pytest.mark.asyncio
    async def it_raises_error_when_singleton_depends_on_request(self) -> None:
        """CaptiveDependencyError when SINGLETON depends on REQUEST."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            pass

        @service  # Default SINGLETON
        class SingletonService:
            def __init__(self, ctx: RequestContext) -> None:
                self.ctx = ctx

        container = Container()

        # Error should be raised at scan time (fail fast)
        with pytest.raises(CaptiveDependencyError, match=r'(?i)captive dependency'):
            container.scan()

    @pytest.mark.asyncio
    async def it_provides_helpful_captive_dependency_message(self) -> None:
        """Error message explains the captive dependency problem."""

        @service(scope=Scope.REQUEST)
        class RequestData:
            pass

        @service  # SINGLETON
        class GlobalService:
            def __init__(self, data: RequestData) -> None:
                self.data = data

        container = Container()

        with pytest.raises(CaptiveDependencyError) as exc_info:
            container.scan()

        error_message = str(exc_info.value)
        # Should mention both components
        assert 'GlobalService' in error_message
        assert 'RequestData' in error_message
        # Should explain the problem
        assert 'SINGLETON' in error_message
        assert 'REQUEST' in error_message

    @pytest.mark.asyncio
    async def it_allows_request_to_depend_on_singleton(self) -> None:
        """REQUEST depending on SINGLETON is valid (no captive)."""

        @service  # SINGLETON
        class Config:
            pass

        @service(scope=Scope.REQUEST)
        class RequestHandler:
            def __init__(self, config: Config) -> None:
                self.config = config

        container = Container()
        container.scan()  # Should not raise

        async with container.create_scope() as scope:
            handler = scope.resolve(RequestHandler)
            config = container.resolve(Config)

            # Handler's config should be the singleton
            assert handler.config is config

    @pytest.mark.asyncio
    async def it_allows_request_to_depend_on_request(self) -> None:
        """REQUEST depending on REQUEST is valid."""

        @service(scope=Scope.REQUEST)
        class RequestContext:
            pass

        @service(scope=Scope.REQUEST)
        class RequestHandler:
            def __init__(self, ctx: RequestContext) -> None:
                self.ctx = ctx

        container = Container()
        container.scan()  # Should not raise

        async with container.create_scope() as scope:
            handler = scope.resolve(RequestHandler)
            ctx = scope.resolve(RequestContext)

            # Both should be same instance (cached in scope)
            assert handler.ctx is ctx


class DescribeScopedLifecycle:
    """Tests for lifecycle management within scopes."""

    @pytest.mark.asyncio
    async def it_disposes_request_scoped_lifecycle_components_on_exit(self) -> None:
        """@lifecycle components with REQUEST scope get dispose() called on scope exit."""
        disposed: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class RequestDatabase:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('RequestDatabase')

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            db = scope.resolve(RequestDatabase)
            assert db is not None
            assert 'RequestDatabase' not in disposed

        # After scope exits, dispose should have been called
        assert 'RequestDatabase' in disposed

    @pytest.mark.asyncio
    async def it_disposes_multiple_scoped_components_in_reverse_order(self) -> None:
        """Multiple scoped components disposed in reverse dependency order."""
        disposal_order: list[str] = []

        @service(scope=Scope.REQUEST)
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposal_order.append('Database')

        @service(scope=Scope.REQUEST)
        @lifecycle
        class Repository:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposal_order.append('Repository')

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            # Resolve the dependent to trigger both
            repo = scope.resolve(Repository)
            assert repo is not None

        # Disposal order: Repository (dependent) first, then Database
        assert disposal_order == ['Repository', 'Database']

    @pytest.mark.asyncio
    async def it_does_not_dispose_singleton_components_on_scope_exit(self) -> None:
        """SINGLETON components are NOT disposed when scope exits."""
        disposed: list[str] = []

        @service  # SINGLETON
        @lifecycle
        class GlobalDatabase:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('GlobalDatabase')

        container = Container()
        container.scan()

        # Start container to initialize singleton
        await container.start()

        async with container.create_scope() as scope:
            db = scope.resolve(GlobalDatabase)
            assert db is not None

        # Singleton should NOT be disposed when scope exits
        assert 'GlobalDatabase' not in disposed

        # Only disposed when container stops
        await container.stop()
        assert 'GlobalDatabase' in disposed


class DescribeAdapterWithRequestScope:
    """Tests for adapters with REQUEST scope."""

    @pytest.mark.asyncio
    async def it_supports_request_scoped_adapters(self) -> None:
        """Adapters can be registered with REQUEST scope."""

        class DbConnectionPort(Protocol):
            def query(self, sql: str) -> str: ...

        @adapter.for_(DbConnectionPort, profile=Profile.TEST, scope=Scope.REQUEST)
        class FakeDbConnection:
            def __init__(self) -> None:
                self.connection_id = str(uuid.uuid4())

            def query(self, sql: str) -> str:
                return f'Result from {self.connection_id}'

        container = Container()
        container.scan(profile=Profile.TEST)

        connections: list[str] = []

        async with container.create_scope() as scope1:
            conn1 = scope1.resolve(DbConnectionPort)
            conn2 = scope1.resolve(DbConnectionPort)
            # Same connection within scope
            assert conn1 is conn2
            connections.append(conn1.connection_id)

        async with container.create_scope() as scope2:
            conn3 = scope2.resolve(DbConnectionPort)
            connections.append(conn3.connection_id)

        # Different connections between scopes
        assert len(set(connections)) == 2


class DescribeScopeWithDependencyInjection:
    """Tests for dependency injection within scopes."""

    @pytest.mark.asyncio
    async def it_injects_request_scoped_dependencies_correctly(self) -> None:
        """Services get correct request-scoped dependencies injected."""

        @service(scope=Scope.REQUEST)
        class RequestId:
            def __init__(self) -> None:
                self.value = str(uuid.uuid4())

        @service(scope=Scope.REQUEST)
        class RequestLogger:
            def __init__(self, request_id: RequestId) -> None:
                self.request_id = request_id

        @service(scope=Scope.REQUEST)
        class RequestHandler:
            def __init__(self, logger: RequestLogger, request_id: RequestId) -> None:
                self.logger = logger
                self.request_id = request_id

        container = Container()
        container.scan()

        async with container.create_scope() as scope:
            handler = scope.resolve(RequestHandler)
            logger = scope.resolve(RequestLogger)
            request_id = scope.resolve(RequestId)

            # All should reference the same RequestId instance
            assert handler.request_id is request_id
            assert handler.logger.request_id is request_id
            assert logger.request_id is request_id

    @pytest.mark.asyncio
    async def it_mixes_singleton_and_request_dependencies(self) -> None:
        """Services can have both SINGLETON and REQUEST dependencies."""

        @service  # SINGLETON
        class AppConfig:
            def __init__(self) -> None:
                self.app_name = 'TestApp'

        @service(scope=Scope.REQUEST)
        class RequestContext:
            def __init__(self) -> None:
                self.request_id = str(uuid.uuid4())

        @service(scope=Scope.REQUEST)
        class RequestHandler:
            def __init__(self, config: AppConfig, ctx: RequestContext) -> None:
                self.config = config
                self.ctx = ctx

        container = Container()
        container.scan()

        # Get singleton before any scope
        app_config = container.resolve(AppConfig)

        request_ids: list[str] = []

        async with container.create_scope() as scope1:
            handler1 = scope1.resolve(RequestHandler)
            # Handler gets same singleton config
            assert handler1.config is app_config
            request_ids.append(handler1.ctx.request_id)

        async with container.create_scope() as scope2:
            handler2 = scope2.resolve(RequestHandler)
            # Handler still gets same singleton config
            assert handler2.config is app_config
            request_ids.append(handler2.ctx.request_id)

        # Different request contexts per scope
        assert request_ids[0] != request_ids[1]
