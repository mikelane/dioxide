"""Unit tests for lifecycle instance caching behavior (#135).

These tests verify that the Container correctly caches lifecycle instances
during start() and reuses them during stop() instead of rebuilding the list.
"""

from typing import Any

import pytest

from dioxide import (
    Container,
    lifecycle,
    service,
)


class DescribeLifecycleInstanceCaching:
    """Unit tests for _lifecycle_instances caching."""

    @pytest.mark.asyncio
    async def it_caches_lifecycle_instances_during_start(self) -> None:
        """Caches the lifecycle instances list during start()."""

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # Before start, cache should be None
        assert container._lifecycle_instances is None

        await container.start()

        # After start, cache should be populated
        assert container._lifecycle_instances is not None
        if container._lifecycle_instances:  # type: ignore[unreachable]
            assert len(container._lifecycle_instances) == 1
            assert isinstance(container._lifecycle_instances[0], Database)

    @pytest.mark.asyncio
    async def it_clears_cache_on_stop(self) -> None:
        """Clears the lifecycle instances cache after stop()."""

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()
        assert container._lifecycle_instances is not None

        await container.stop()

        # After stop, cache should be cleared
        assert container._lifecycle_instances is None

    @pytest.mark.asyncio
    async def it_handles_stop_without_prior_start(self) -> None:
        """Handles stop() when start() was never called (cache is None)."""

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # Call stop without calling start first
        # Should not raise, should be a no-op
        await container.stop()

        # Cache should still be None
        assert container._lifecycle_instances is None

    @pytest.mark.asyncio
    async def it_clears_cache_on_initialization_failure(self) -> None:
        """Clears the cache when initialization fails during start()."""

        @service
        @lifecycle
        class GoodService:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class FailingService:
            def __init__(self, good: GoodService) -> None:
                self.good = good

            async def initialize(self) -> None:
                raise RuntimeError('Initialization failed')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # start() should fail
        with pytest.raises(RuntimeError, match='Initialization failed'):
            await container.start()

        # Cache should be cleared after rollback
        assert container._lifecycle_instances is None

    @pytest.mark.asyncio
    async def it_rebuilds_cache_on_subsequent_start_after_failure(self) -> None:
        """Rebuilds the cache when start() is called again after a failure."""
        call_count = {'initialize': 0}

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                call_count['initialize'] += 1
                # Fail on first call, succeed on second
                if call_count['initialize'] == 1:
                    raise RuntimeError('First attempt failed')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # First start() should fail
        with pytest.raises(RuntimeError, match='First attempt failed'):
            await container.start()

        assert container._lifecycle_instances is None

        # Second start() should succeed
        await container.start()

        # Cache should be populated
        assert container._lifecycle_instances is not None
        if container._lifecycle_instances:  # type: ignore[unreachable]
            assert len(container._lifecycle_instances) == 1

    @pytest.mark.asyncio
    async def it_uses_same_instances_for_start_and_stop(self) -> None:
        """Uses the exact same instances during start() and stop().

        This is the core fix for #135 - stop() should dispose exactly
        what start() initialized, not rebuild the list.
        """
        instances_initialized = []
        instances_disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                instances_initialized.append(self)

            async def dispose(self) -> None:
                instances_disposed.append(self)

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        # Should be the exact same instance (singleton)
        assert len(instances_initialized) == 1
        assert len(instances_disposed) == 1
        assert instances_initialized[0] is instances_disposed[0]

    @pytest.mark.asyncio
    async def it_handles_multiple_start_stop_cycles(self) -> None:
        """Handles multiple start/stop cycles correctly.

        Each cycle should initialize/dispose, and the cache should be
        managed correctly across cycles.
        """

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # Cycle 1
        await container.start()
        cycle1_instances = container._lifecycle_instances
        assert cycle1_instances is not None
        await container.stop()
        stopped_state_1 = container._lifecycle_instances
        assert stopped_state_1 is None

        # Cycle 2 - start() rebuilds _lifecycle_instances
        await container.start()
        cycle2_instances = container._lifecycle_instances
        assert cycle2_instances is not None
        await container.stop()
        stopped_state_2 = container._lifecycle_instances
        assert stopped_state_2 is None

        # Instances should be the same (singletons)
        assert cycle1_instances[0] is cycle2_instances[0]

    @pytest.mark.asyncio
    async def it_caches_complex_dependency_graph(self) -> None:
        """Caches the correct dependency order for complex graphs."""

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class Application:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        # Cache should contain all 3 instances in dependency order
        assert container._lifecycle_instances is not None
        assert len(container._lifecycle_instances) == 3

        # Verify dependency order (Database, Cache, Application)
        db_instance = container._lifecycle_instances[0]
        cache_instance = container._lifecycle_instances[1]
        app_instance = container._lifecycle_instances[2]

        assert isinstance(db_instance, Database)
        assert isinstance(cache_instance, Cache)
        assert isinstance(app_instance, Application)

        # Verify they are the resolved instances
        assert cache_instance.db is db_instance
        assert app_instance.db is db_instance
        assert app_instance.cache is cache_instance

    @pytest.mark.asyncio
    async def it_prevents_redundant_dependency_graph_rebuilds(self) -> None:
        """Prevents rebuilding dependency graph during stop().

        This is an efficiency test - stop() should use the cached list
        instead of calling _build_lifecycle_dependency_order() again.
        """
        build_count = {'count': 0}

        # Monkey-patch to track calls
        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        # Wrap _build_lifecycle_dependency_order to count calls
        original_build = container._build_lifecycle_dependency_order

        def counting_build() -> list[Any]:
            build_count['count'] += 1
            return original_build()

        container._build_lifecycle_dependency_order = counting_build  # type: ignore[method-assign]

        await container.start()
        # Should call once during start
        assert build_count['count'] == 1

        await container.stop()
        # Should NOT call again during stop (uses cache)
        assert build_count['count'] == 1, 'stop() should not rebuild dependency graph, should use cache'
