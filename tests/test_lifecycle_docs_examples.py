"""Tests verifying code examples from docs/guides/lifecycle-async-patterns.md.

Each test corresponds to a pattern or scenario described in the guide,
ensuring the documented behavior is accurate.
"""

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeLifecycleDocExamples:
    """Verify code patterns documented in the lifecycle async patterns guide."""

    @pytest.mark.asyncio
    async def it_initializes_via_async_context_manager(self) -> None:
        """Pattern 1: async with Container() initializes and disposes lifecycle components."""
        initialized = False
        disposed = False

        @service
        @lifecycle
        class Resource:
            async def initialize(self) -> None:
                nonlocal initialized
                initialized = True

            async def dispose(self) -> None:
                nonlocal disposed
                disposed = True

        container = Container()
        container.scan()

        async with container:
            assert initialized
            assert not disposed
            container.resolve(Resource)

        assert disposed

    @pytest.mark.asyncio
    async def it_initializes_via_manual_start_stop(self) -> None:
        """Pattern 2: manual start()/stop() controls lifecycle explicitly."""
        call_log: list[str] = []

        @service
        @lifecycle
        class ManualResource:
            async def initialize(self) -> None:
                call_log.append('initialized')

            async def dispose(self) -> None:
                call_log.append('disposed')

        container = Container()
        container.scan()

        assert call_log == []
        await container.start()
        assert call_log == ['initialized']

        container.resolve(ManualResource)
        await container.stop()

        assert call_log == ['initialized', 'disposed']

    @pytest.mark.asyncio
    async def it_returns_uninitialized_instance_when_resolved_before_start(self) -> None:
        """FAQ: resolve() before start() returns an instance without running initialize()."""

        @service
        @lifecycle
        class EarlyResolveDb:
            def __init__(self) -> None:
                self.engine: str | None = None

            async def initialize(self) -> None:
                self.engine = 'connected'

            async def dispose(self) -> None:
                self.engine = None

        container = Container()
        container.scan()

        instance = container.resolve(EarlyResolveDb)
        assert instance.engine is None

        await container.start()
        assert instance.engine == 'connected'

        await container.stop()

    @pytest.mark.asyncio
    async def it_rolls_back_initialized_components_on_failure(self) -> None:
        """Error handling: if initialize() fails, already-initialized components are disposed."""
        first_disposed = False

        @service
        @lifecycle
        class FirstOk:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal first_disposed
                first_disposed = True

        @service
        @lifecycle
        class SecondFails:
            def __init__(self, dep: FirstOk) -> None:
                self.dep = dep

            async def initialize(self) -> None:
                raise ConnectionError('cannot connect')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        with pytest.raises(ConnectionError, match='cannot connect'):
            await container.start()

        assert first_disposed

    @pytest.mark.asyncio
    async def it_continues_disposing_when_one_dispose_fails(self) -> None:
        """Error handling: dispose() failure does not prevent other components from disposing."""
        good_disposed = False

        @service
        @lifecycle
        class GoodComponent:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                nonlocal good_disposed
                good_disposed = True

        @service
        @lifecycle
        class BadDispose:
            def __init__(self, dep: GoodComponent) -> None:
                self.dep = dep

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                raise RuntimeError('dispose failed')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert good_disposed

    @pytest.mark.asyncio
    async def it_initializes_in_dependency_order(self) -> None:
        """Lifecycle ordering: dependencies are initialized before their dependents."""
        init_order: list[str] = []

        @service
        @lifecycle
        class DbLayer:
            async def initialize(self) -> None:
                init_order.append('db')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class CacheLayer:
            def __init__(self, db: DbLayer) -> None:
                self.db = db

            async def initialize(self) -> None:
                init_order.append('cache')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class AppLayer:
            def __init__(self, db: DbLayer, cache: CacheLayer) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                init_order.append('app')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()
        await container.start()

        assert init_order.index('db') < init_order.index('cache')
        assert init_order.index('cache') < init_order.index('app')

        await container.stop()

    @pytest.mark.asyncio
    async def it_disposes_in_reverse_dependency_order(self) -> None:
        """Lifecycle ordering: dependents are disposed before their dependencies."""
        dispose_order: list[str] = []

        @service
        @lifecycle
        class BaseResource:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                dispose_order.append('base')

        @service
        @lifecycle
        class DependentResource:
            def __init__(self, base: BaseResource) -> None:
                self.base = base

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                dispose_order.append('dependent')

        container = Container()
        container.scan()
        await container.start()
        await container.stop()

        assert dispose_order == ['dependent', 'base']

    @pytest.mark.asyncio
    async def it_works_with_adapter_lifecycle_and_test_fake_without(self) -> None:
        """FAQ: production adapters use @lifecycle, test fakes do not."""

        class StoragePort(Protocol):
            async def read(self, key: str) -> str | None: ...

        @adapter.for_(StoragePort, profile=Profile.PRODUCTION)
        @lifecycle
        class ProductionStorage:
            def __init__(self) -> None:
                self.connected = False

            async def initialize(self) -> None:
                self.connected = True

            async def dispose(self) -> None:
                self.connected = False

            async def read(self, key: str) -> str | None:
                return None

        @adapter.for_(StoragePort, profile=Profile.TEST)
        class FakeStorage:
            def __init__(self) -> None:
                self.data: dict[str, str] = {}

            async def read(self, key: str) -> str | None:
                return self.data.get(key)

            def seed(self, key: str, value: str) -> None:
                self.data[key] = value

        # Production path uses lifecycle
        async with Container(profile=Profile.PRODUCTION) as prod_container:
            storage = prod_container.resolve(StoragePort)
            assert storage.connected

        # Test path skips lifecycle entirely
        test_container = Container(profile=Profile.TEST)
        fake = test_container.resolve(StoragePort)
        fake.seed('key1', 'value1')
        result = await fake.read('key1')
        assert result == 'value1'

    def it_rejects_sync_initialize(self) -> None:
        """FAQ: @lifecycle rejects synchronous initialize() at decoration time."""
        with pytest.raises(TypeError, match='must be async'):

            @service
            @lifecycle  # type: ignore[arg-type]
            class SyncInit:
                def initialize(self) -> None:
                    pass

                async def dispose(self) -> None:
                    pass

    def it_rejects_missing_dispose(self) -> None:
        """FAQ: @lifecycle rejects missing dispose() at decoration time."""
        with pytest.raises(TypeError, match=r'must implement.*dispose'):

            @service
            @lifecycle  # type: ignore[arg-type]
            class NoDispose:
                async def initialize(self) -> None:
                    pass

    @pytest.mark.asyncio
    async def it_supports_idempotent_dispose(self) -> None:
        """Best practice: dispose() can be called safely after stop() clears state."""
        dispose_count = 0

        @service
        @lifecycle
        class IdempotentResource:
            def __init__(self) -> None:
                self.pool: str | None = None

            async def initialize(self) -> None:
                self.pool = 'active'

            async def dispose(self) -> None:
                nonlocal dispose_count
                if self.pool:
                    self.pool = None
                    dispose_count += 1

        container = Container()
        container.scan()

        await container.start()
        await container.stop()
        assert dispose_count == 1

        # Second cycle re-initializes and disposes again
        await container.start()
        await container.stop()
        assert dispose_count == 2
