"""Integration tests for lifecycle disposal bug (#135).

This test file demonstrates the bug where Container.stop() only disposes
some lifecycle components instead of all of them when there are multiple
dependent components.

Root Cause: _build_lifecycle_dependency_order() is called twice (start and stop),
and the second call during stop() fails to find all instances.
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


class DescribeLifecycleDisposalBug:
    """Integration tests demonstrating the disposal bug with dependent components."""

    @pytest.mark.asyncio
    async def it_disposes_all_components_with_three_plus_dependencies(self) -> None:
        """Disposes all components when there are 3+ dependent lifecycle components.

        This is the core bug scenario from issue #135. When Container.stop() is called,
        it should dispose all components that were initialized during start(), but
        currently only disposes Database while skipping Cache and Application.
        """
        disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database')

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Cache')

        @service
        @lifecycle
        class Application:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Application')

        container = Container()
        container.scan()

        # All 3 components should initialize
        await container.start()

        # All 3 components should dispose (this is the bug)
        await container.stop()

        # EXPECTED: All 3 disposed in reverse order
        # ACTUAL (before fix): Only ['Database']
        assert disposed == ['Application', 'Cache', 'Database'], (
            f'Expected all components disposed in reverse order, '
            f'but got {disposed}. This indicates stop() is not '
            f'disposing all initialized components.'
        )

    @pytest.mark.asyncio
    async def it_disposes_all_adapters_and_services_mixed(self) -> None:
        """Disposes all components when mixing adapters and services with dependencies."""
        disposed = []

        # Port definition
        class DatabasePort(Protocol):
            async def query(self, sql: str) -> list[dict[str, str]]: ...

        # Adapter as dependency
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('PostgresAdapter')

            async def query(self, sql: str) -> list[dict[str, str]]:
                return []

        # Service depending on adapter
        @service
        @lifecycle
        class Cache:
            def __init__(self, db: DatabasePort) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Cache')

        # Service depending on both
        @service
        @lifecycle
        class Application:
            def __init__(self, db: DatabasePort, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Application')

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        await container.start()
        await container.stop()

        # All components should be disposed
        assert 'PostgresAdapter' in disposed, 'PostgresAdapter should be disposed'
        assert 'Cache' in disposed, 'Cache should be disposed'
        assert 'Application' in disposed, 'Application should be disposed'

        # Verify reverse dependency order
        assert disposed.index('Application') < disposed.index('Cache'), 'Application should be disposed before Cache'
        assert disposed.index('Cache') < disposed.index('PostgresAdapter'), (
            'Cache should be disposed before PostgresAdapter'
        )

    @pytest.mark.asyncio
    async def it_disposes_all_components_with_multiple_dependency_chains(self) -> None:
        """Disposes all components when there are multiple independent dependency chains."""
        disposed = []

        # Chain 1: Database -> Cache -> CacheService
        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database')

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Cache')

        @service
        @lifecycle
        class CacheService:
            def __init__(self, cache: Cache) -> None:
                self.cache = cache

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('CacheService')

        # Chain 2: EmailService (independent)
        @service
        @lifecycle
        class EmailService:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('EmailService')

        # Chain 3: Logger -> MetricsService (independent of chain 1)
        @service
        @lifecycle
        class Logger:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Logger')

        @service
        @lifecycle
        class MetricsService:
            def __init__(self, logger: Logger) -> None:
                self.logger = logger

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('MetricsService')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        # All 6 components should be disposed
        expected_components = {'Database', 'Cache', 'CacheService', 'EmailService', 'Logger', 'MetricsService'}
        disposed_set = set(disposed)

        assert disposed_set == expected_components, (
            f'All components should be disposed. Expected {expected_components}, got {disposed_set}'
        )

        # Verify dependency order within each chain
        if 'Cache' in disposed and 'Database' in disposed:
            assert disposed.index('Cache') < disposed.index('Database'), 'Cache should be disposed before Database'
        if 'CacheService' in disposed and 'Cache' in disposed:
            assert disposed.index('CacheService') < disposed.index('Cache'), (
                'CacheService should be disposed before Cache'
            )
        if 'MetricsService' in disposed and 'Logger' in disposed:
            assert disposed.index('MetricsService') < disposed.index('Logger'), (
                'MetricsService should be disposed before Logger'
            )

    @pytest.mark.asyncio
    async def it_disposes_during_exception_in_application_runtime(self) -> None:
        """Disposes all components when exception occurs during application runtime.

        This tests the async context manager scenario where an exception happens
        in the middle of application execution. All initialized components should
        still be disposed properly.
        """
        initialized = []
        disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                initialized.append('Database')

            async def dispose(self) -> None:
                disposed.append('Database')

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                initialized.append('Cache')

            async def dispose(self) -> None:
                disposed.append('Cache')

        @service
        @lifecycle
        class Application:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                initialized.append('Application')

            async def dispose(self) -> None:
                disposed.append('Application')

        container = Container()
        container.scan()

        # Use async context manager and raise exception during application runtime
        with pytest.raises(RuntimeError, match='Application error'):
            async with container:
                # All components initialized
                assert set(initialized) == {'Database', 'Cache', 'Application'}
                # Simulate application error
                raise RuntimeError('Application error')

        # All components should still be disposed despite exception
        assert set(disposed) == {'Database', 'Cache', 'Application'}, (
            f'All components should be disposed on exception. '
            f'Expected {{Database, Cache, Application}}, got {set(disposed)}'
        )

    @pytest.mark.asyncio
    async def it_handles_async_context_manager_with_complex_dependencies(self) -> None:
        """Disposes all components correctly with async context manager and complex deps.

        Tests the full lifecycle pattern with:
        - Multiple adapters with dependencies
        - Services depending on adapters
        - Complex dependency graph
        - Async context manager (which calls start() and stop())
        """
        events = []

        # Port definitions
        class DatabasePort(Protocol):
            async def query(self, sql: str) -> list[dict[str, str]]: ...

        class CachePort(Protocol):
            async def get(self, key: str) -> str | None: ...
            async def set(self, key: str, value: str) -> None: ...

        # Adapter 1: Database (no dependencies)
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                events.append('PostgresAdapter.initialize')

            async def dispose(self) -> None:
                events.append('PostgresAdapter.dispose')

            async def query(self, sql: str) -> list[dict[str, str]]:
                return []

        # Adapter 2: Cache depends on Database
        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisCacheAdapter:
            def __init__(self, db: DatabasePort) -> None:
                self.db = db

            async def initialize(self) -> None:
                events.append('RedisCacheAdapter.initialize')

            async def dispose(self) -> None:
                events.append('RedisCacheAdapter.dispose')

            async def get(self, key: str) -> str | None:
                return None

            async def set(self, key: str, value: str) -> None:
                pass

        # Service depends on both adapters
        @service
        @lifecycle
        class UserService:
            def __init__(self, db: DatabasePort, cache: CachePort) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                events.append('UserService.initialize')

            async def dispose(self) -> None:
                events.append('UserService.dispose')

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        async with container:
            # Verify all components initialized
            initialized = [e for e in events if e.endswith('.initialize')]
            assert len(initialized) == 3, f'All 3 components should initialize, got {initialized}'

        # Verify all components disposed
        disposed = [e for e in events if e.endswith('.dispose')]
        assert len(disposed) == 3, f'All 3 components should be disposed, got {disposed}. Full events: {events}'

        # Verify disposal order (reverse of initialization)
        assert events.index('UserService.dispose') > events.index('UserService.initialize')
        assert events.index('RedisCacheAdapter.dispose') > events.index('RedisCacheAdapter.initialize')
        assert events.index('PostgresAdapter.dispose') > events.index('PostgresAdapter.initialize')

        # UserService should dispose before its dependencies
        assert events.index('UserService.dispose') < events.index('RedisCacheAdapter.dispose')
        assert events.index('UserService.dispose') < events.index('PostgresAdapter.dispose')

    @pytest.mark.asyncio
    async def it_disposes_all_components_after_multiple_start_stop_cycles(self) -> None:
        """Disposes all components correctly across multiple start/stop cycles.

        This tests that the container can be reused and that stop() correctly
        disposes all components each time.
        """
        disposed_cycle1 = []
        disposed_cycle2 = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed_cycle1.append('Database')
                disposed_cycle2.append('Database')

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed_cycle1.append('Cache')
                disposed_cycle2.append('Cache')

        @service
        @lifecycle
        class Application:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed_cycle1.append('Application')
                disposed_cycle2.append('Application')

        container = Container()
        container.scan()

        # Cycle 1
        await container.start()
        disposed_cycle1.clear()  # Reset to track only this cycle's disposals
        await container.stop()

        assert set(disposed_cycle1) == {'Database', 'Cache', 'Application'}, (
            f'Cycle 1: All components should be disposed. Got {set(disposed_cycle1)}'
        )

        # Cycle 2
        await container.start()
        disposed_cycle2.clear()  # Reset to track only this cycle's disposals
        await container.stop()

        assert set(disposed_cycle2) == {'Database', 'Cache', 'Application'}, (
            f'Cycle 2: All components should be disposed. Got {set(disposed_cycle2)}'
        )
