"""Tests for async lifecycle support in dioxide.

These tests verify that container.start() and container.stop() properly await
async initialize() and dispose() methods. This is critical for real-world usage
where adapters need async setup (database pools, HTTP sessions, message queues).

Key scenarios tested:
1. Async initialize() is properly awaited
2. Async dispose() is properly awaited
3. Initialize order respects dependencies (dependencies first)
4. Dispose order respects dependencies (reverse: dependents first)
5. Rollback on initialize failure disposes already-initialized components
6. Dispose errors logged but don't prevent other disposals
7. Async context manager (async with container:) handles lifecycle
"""

from __future__ import annotations

import asyncio
from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeAsyncLifecycleInitialize:
    """Tests for async initialize() behavior."""

    @pytest.mark.asyncio
    async def it_awaits_async_initialize_method(self) -> None:
        """Verifies that container.start() awaits async initialize() methods."""
        initialized = False
        awaited_sleep = False

        @service
        @lifecycle
        class AsyncDatabase:
            async def initialize(self) -> None:
                nonlocal initialized, awaited_sleep
                # This would fail if not properly awaited
                await asyncio.sleep(0.001)
                awaited_sleep = True
                initialized = True

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        assert initialized, 'initialize() was not called'
        assert awaited_sleep, 'async sleep was not properly awaited'

    @pytest.mark.asyncio
    async def it_awaits_initialize_with_async_io_operations(self) -> None:
        """Verifies async I/O in initialize() is properly awaited."""
        connection_established = False

        @service
        @lifecycle
        class AsyncConnectionPool:
            async def initialize(self) -> None:
                nonlocal connection_established
                # Simulate async connection establishment
                await asyncio.sleep(0.001)
                connection_established = True

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        assert connection_established, 'Async connection was not established'


class DescribeAsyncLifecycleDispose:
    """Tests for async dispose() behavior."""

    @pytest.mark.asyncio
    async def it_awaits_async_dispose_method(self) -> None:
        """Verifies that container.stop() awaits async dispose() methods."""
        disposed = False
        awaited_sleep = False

        @service
        @lifecycle
        class AsyncDatabase:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal disposed, awaited_sleep
                # This would fail if not properly awaited
                await asyncio.sleep(0.001)
                awaited_sleep = True
                disposed = True

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert disposed, 'dispose() was not called'
        assert awaited_sleep, 'async sleep was not properly awaited'

    @pytest.mark.asyncio
    async def it_awaits_dispose_with_async_cleanup(self) -> None:
        """Verifies async cleanup in dispose() is properly awaited."""
        connection_closed = False

        @service
        @lifecycle
        class AsyncConnectionPool:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal connection_closed
                # Simulate async connection cleanup
                await asyncio.sleep(0.001)
                connection_closed = True

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert connection_closed, 'Async connection was not closed'


class DescribeAsyncLifecycleDependencyOrder:
    """Tests for lifecycle ordering based on dependencies."""

    @pytest.mark.asyncio
    async def it_awaits_initialize_in_dependency_order(self) -> None:
        """Dependencies are initialized before their dependents."""
        init_order: list[str] = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                await asyncio.sleep(0.001)  # Simulate async work
                init_order.append('database')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class UserService:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                init_order.append('user_service')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        assert init_order == ['database', 'user_service']

    @pytest.mark.asyncio
    async def it_awaits_dispose_in_reverse_dependency_order(self) -> None:
        """Dependents are disposed before their dependencies."""
        dispose_order: list[str] = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)  # Simulate async cleanup
                dispose_order.append('database')

        @service
        @lifecycle
        class UserService:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                dispose_order.append('user_service')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert dispose_order == ['user_service', 'database']

    @pytest.mark.asyncio
    async def it_handles_complex_dependency_graph(self) -> None:
        """Correctly orders initialization for multi-level dependencies."""
        init_order: list[str] = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                init_order.append('database')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class Cache:
            async def initialize(self) -> None:
                init_order.append('cache')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class UserRepository:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                init_order.append('user_repository')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class UserService:
            def __init__(self, repo: UserRepository) -> None:
                self.repo = repo

            async def initialize(self) -> None:
                init_order.append('user_service')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        # Database and Cache have no dependencies, so they go first (order may vary)
        # UserRepository depends on both, so it goes after
        # UserService depends on UserRepository, so it goes last
        assert init_order.index('user_repository') > init_order.index('database')
        assert init_order.index('user_repository') > init_order.index('cache')
        assert init_order.index('user_service') > init_order.index('user_repository')


class DescribeAsyncLifecycleRollback:
    """Tests for rollback on initialization failure."""

    @pytest.mark.asyncio
    async def it_rolls_back_on_initialize_failure(self) -> None:
        """Already-initialized components are disposed on failure."""
        disposed: list[str] = []

        @service
        @lifecycle
        class ServiceA:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)  # Async dispose
                disposed.append('A')

        @service
        @lifecycle
        class ServiceB:
            def __init__(self, a: ServiceA) -> None:
                self.a = a

            async def initialize(self) -> None:
                raise RuntimeError('B failed!')

            async def dispose(self) -> None:
                disposed.append('B')

        container = Container()
        container.scan()

        with pytest.raises(RuntimeError, match='B failed'):
            await container.start()

        assert 'A' in disposed, 'A was initialized, so must be disposed'
        assert 'B' not in disposed, 'B never fully initialized'

    @pytest.mark.asyncio
    async def it_disposes_multiple_initialized_components_on_failure(self) -> None:
        """All initialized components are disposed on failure."""
        disposed: list[str] = []

        @service
        @lifecycle
        class ServiceA:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('A')

        @service
        @lifecycle
        class ServiceB:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('B')

        @service
        @lifecycle
        class ServiceC:
            def __init__(self, a: ServiceA, b: ServiceB) -> None:
                self.a = a
                self.b = b

            async def initialize(self) -> None:
                raise RuntimeError('C failed!')

            async def dispose(self) -> None:
                disposed.append('C')

        container = Container()
        container.scan()

        with pytest.raises(RuntimeError, match='C failed'):
            await container.start()

        # A and B were initialized (C depends on them), so they must be disposed
        assert 'A' in disposed
        assert 'B' in disposed
        assert 'C' not in disposed


class DescribeAsyncLifecycleDisposeErrors:
    """Tests for error handling during dispose."""

    @pytest.mark.asyncio
    async def it_continues_disposal_after_dispose_error(self) -> None:
        """All components are disposed even if one fails."""
        disposed: list[str] = []

        @service
        @lifecycle
        class BadDisposer:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('bad')
                raise RuntimeError('Dispose failed!')

        @service
        @lifecycle
        class GoodDisposer:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)  # Async dispose
                disposed.append('good')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()  # Should not raise

        assert 'bad' in disposed
        assert 'good' in disposed

    @pytest.mark.asyncio
    async def it_handles_async_dispose_errors(self) -> None:
        """Async errors in dispose() are handled without breaking other disposals."""
        disposed: list[str] = []

        @service
        @lifecycle
        class AsyncBadDisposer:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)
                disposed.append('async_bad')
                raise RuntimeError('Async dispose failed!')

        @service
        @lifecycle
        class AsyncGoodDisposer:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)
                disposed.append('async_good')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert 'async_bad' in disposed
        assert 'async_good' in disposed


class DescribeAsyncLifecycleContextManager:
    """Tests for async context manager handling of lifecycle."""

    @pytest.mark.asyncio
    async def it_awaits_initialize_on_context_enter(self) -> None:
        """async with container: awaits initialize()."""
        initialized = False

        @service
        @lifecycle
        class AsyncDatabase:
            async def initialize(self) -> None:
                nonlocal initialized
                await asyncio.sleep(0.001)
                initialized = True

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        async with container:
            assert initialized, 'initialize() not awaited on enter'

    @pytest.mark.asyncio
    async def it_awaits_dispose_on_context_exit(self) -> None:
        """async with container: awaits dispose() on exit."""
        disposed = False

        @service
        @lifecycle
        class AsyncDatabase:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal disposed
                await asyncio.sleep(0.001)
                disposed = True

        container = Container()
        container.scan()

        async with container:
            pass

        assert disposed, 'dispose() not awaited on exit'

    @pytest.mark.asyncio
    async def it_awaits_dispose_on_exception(self) -> None:
        """dispose() is awaited even when exception occurs in context."""
        disposed = False

        @service
        @lifecycle
        class AsyncDatabase:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal disposed
                await asyncio.sleep(0.001)
                disposed = True

        container = Container()
        container.scan()

        with pytest.raises(RuntimeError, match='User error'):
            async with container:
                raise RuntimeError('User error')

        assert disposed, 'dispose() not awaited after exception'


class DescribeAsyncLifecycleWithAdapters:
    """Tests for async lifecycle with adapter pattern."""

    @pytest.mark.asyncio
    async def it_awaits_adapter_initialize(self) -> None:
        """Async adapter initialize() is properly awaited."""
        initialized = False

        class DatabasePort(Protocol):
            async def query(self, sql: str) -> list[dict[str, str]]: ...

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        @lifecycle
        class AsyncDatabaseAdapter:
            async def initialize(self) -> None:
                nonlocal initialized
                await asyncio.sleep(0.001)
                initialized = True

            async def dispose(self) -> None:
                pass

            async def query(self, sql: str) -> list[dict[str, str]]:
                return []

        container = Container()
        container.scan(profile=Profile.TEST)

        await container.start()

        assert initialized

    @pytest.mark.asyncio
    async def it_awaits_adapter_dispose(self) -> None:
        """Async adapter dispose() is properly awaited."""
        disposed = False

        class DatabasePort(Protocol):
            async def query(self, sql: str) -> list[dict[str, str]]: ...

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        @lifecycle
        class AsyncDatabaseAdapter:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal disposed
                await asyncio.sleep(0.001)
                disposed = True

            async def query(self, sql: str) -> list[dict[str, str]]:
                return []

        container = Container()
        container.scan(profile=Profile.TEST)

        await container.start()
        await container.stop()

        assert disposed

    @pytest.mark.asyncio
    async def it_initializes_adapters_before_dependent_services(self) -> None:
        """Adapter is initialized before services that depend on it."""
        init_order: list[str] = []

        class CachePort(Protocol):
            async def get(self, key: str) -> str | None: ...

        @adapter.for_(CachePort, profile=Profile.TEST)
        @lifecycle
        class RedisAdapter:
            async def initialize(self) -> None:
                await asyncio.sleep(0.001)
                init_order.append('redis')

            async def dispose(self) -> None:
                pass

            async def get(self, key: str) -> str | None:
                return None

        @service
        @lifecycle
        class CacheService:
            def __init__(self, cache: CachePort) -> None:
                self.cache = cache

            async def initialize(self) -> None:
                init_order.append('cache_service')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        await container.start()

        assert init_order == ['redis', 'cache_service']


class DescribeAsyncLifecycleRealWorldPatterns:
    """Tests demonstrating real-world async lifecycle patterns."""

    @pytest.mark.asyncio
    async def it_handles_database_pool_pattern(self) -> None:
        """Simulates async database connection pool lifecycle."""
        pool_state = {'connections': 0, 'disposed': False}

        class DatabasePort(Protocol):
            async def execute(self, query: str) -> None: ...

        @adapter.for_(DatabasePort, profile=Profile.TEST)
        @lifecycle
        class AsyncDatabasePool:
            async def initialize(self) -> None:
                # Simulate async connection pool creation
                await asyncio.sleep(0.001)
                pool_state['connections'] = 5

            async def dispose(self) -> None:
                # Simulate async pool cleanup
                await asyncio.sleep(0.001)
                pool_state['connections'] = 0
                pool_state['disposed'] = True

            async def execute(self, query: str) -> None:
                pass

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            assert pool_state['connections'] == 5

        assert pool_state['connections'] == 0
        assert pool_state['disposed'] is True

    @pytest.mark.asyncio
    async def it_handles_http_client_session_pattern(self) -> None:
        """Simulates async HTTP client session lifecycle."""
        session_state = {'open': False}

        class HttpClientPort(Protocol):
            async def get(self, url: str) -> str: ...

        @adapter.for_(HttpClientPort, profile=Profile.TEST)
        @lifecycle
        class AsyncHttpClient:
            async def initialize(self) -> None:
                await asyncio.sleep(0.001)
                session_state['open'] = True

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)
                session_state['open'] = False

            async def get(self, url: str) -> str:
                return ''

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            assert session_state['open'] is True

        assert session_state['open'] is False

    @pytest.mark.asyncio
    async def it_handles_message_queue_consumer_pattern(self) -> None:
        """Simulates async message queue consumer lifecycle."""
        consumer_state = {'running': False, 'messages_received': 0}

        class MessageConsumerPort(Protocol):
            async def consume(self) -> None: ...

        @adapter.for_(MessageConsumerPort, profile=Profile.TEST)
        @lifecycle
        class AsyncMessageConsumer:
            async def initialize(self) -> None:
                await asyncio.sleep(0.001)
                consumer_state['running'] = True

            async def dispose(self) -> None:
                await asyncio.sleep(0.001)
                consumer_state['running'] = False

            async def consume(self) -> None:
                consumer_state['messages_received'] += 1

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            assert consumer_state['running'] is True
            consumer = container.resolve(MessageConsumerPort)
            await consumer.consume()
            assert consumer_state['messages_received'] == 1

        assert consumer_state['running'] is False
