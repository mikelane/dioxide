"""Tests for Container lifecycle management (start/stop/async context manager)."""

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeContainerStart:
    """Tests for container.start() method."""

    @pytest.mark.asyncio
    async def it_initializes_lifecycle_components(self) -> None:
        """Calls initialize() on all @lifecycle components."""
        initialized = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                initialized.append('Database.initialize')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        assert 'Database.initialize' in initialized

    @pytest.mark.asyncio
    async def it_skips_non_lifecycle_components(self) -> None:
        """Does not call initialize() on components without @lifecycle."""
        initialized = []

        @service
        class RegularService:
            def __init__(self) -> None:
                pass

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                initialized.append('Database.initialize')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        # Only lifecycle components are initialized
        assert len(initialized) == 1
        assert 'Database.initialize' in initialized

    @pytest.mark.asyncio
    async def it_initializes_components_in_dependency_order(self) -> None:
        """Initializes dependencies before their dependents."""
        initialized = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                initialized.append('Database')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db

            async def initialize(self) -> None:
                initialized.append('Cache')

            async def dispose(self) -> None:
                pass

        @service
        @lifecycle
        class Application:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache

            async def initialize(self) -> None:
                initialized.append('Application')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        await container.start()

        # Database has no dependencies, so it goes first
        # Cache depends on Database, so it goes second
        # Application depends on both, so it goes last
        assert initialized == ['Database', 'Cache', 'Application']

    @pytest.mark.asyncio
    async def it_works_with_adapters(self) -> None:
        """Initializes @lifecycle adapters."""
        initialized = []

        class CachePort(Protocol):
            async def get(self, key: str) -> str | None: ...

        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisAdapter:
            async def initialize(self) -> None:
                initialized.append('RedisAdapter.initialize')

            async def dispose(self) -> None:
                pass

            async def get(self, key: str) -> str | None:
                return None

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        await container.start()

        assert 'RedisAdapter.initialize' in initialized

    @pytest.mark.asyncio
    async def it_rolls_back_on_initialization_failure(self) -> None:
        """Disposes already-initialized components if initialization fails."""
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
                raise RuntimeError('Cache initialization failed')

            async def dispose(self) -> None:
                disposed.append('Cache')

        container = Container()
        container.scan()

        # start() should fail and rollback
        with pytest.raises(RuntimeError, match='Cache initialization failed'):
            await container.start()

        # Database was initialized, so it should be disposed
        assert 'Database' in initialized
        assert 'Database' in disposed
        # Cache failed to initialize, so dispose should NOT be called
        assert 'Cache' not in disposed


class DescribeContainerStop:
    """Tests for container.stop() method."""

    @pytest.mark.asyncio
    async def it_disposes_lifecycle_components(self) -> None:
        """Calls dispose() on all @lifecycle components."""
        disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database.dispose')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        assert 'Database.dispose' in disposed

    @pytest.mark.asyncio
    async def it_skips_non_lifecycle_components(self) -> None:
        """Does not call dispose() on components without @lifecycle."""
        disposed = []

        @service
        class RegularService:
            def __init__(self) -> None:
                pass

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database.dispose')

        container = Container()
        container.scan()

        await container.start()
        await container.stop()

        # Only lifecycle components are disposed
        assert len(disposed) == 1
        assert 'Database.dispose' in disposed

    @pytest.mark.asyncio
    async def it_disposes_components_in_reverse_dependency_order(self) -> None:
        """Disposes dependents before their dependencies."""
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

        await container.start()
        await container.stop()

        # Application depends on both, so it goes first
        # Cache depends on Database, so it goes second
        # Database has no dependencies, so it goes last
        assert disposed == ['Application', 'Cache', 'Database']

    @pytest.mark.asyncio
    async def it_continues_disposal_on_error(self) -> None:
        """Continues disposing other components even if one fails."""
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
                raise RuntimeError('Cache disposal failed')

        container = Container()
        container.scan()

        await container.start()

        # stop() should not raise, but continue disposing other components
        await container.stop()

        # Both components should be disposed despite Cache error
        assert 'Cache' in disposed
        assert 'Database' in disposed


class DescribeContainerAsyncContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def it_calls_start_on_enter(self) -> None:
        """Calls start() when entering the context."""
        initialized = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                initialized.append('Database.initialize')

            async def dispose(self) -> None:
                pass

        container = Container()
        container.scan()

        async with container:
            assert 'Database.initialize' in initialized

    @pytest.mark.asyncio
    async def it_calls_stop_on_exit(self) -> None:
        """Calls stop() when exiting the context."""
        disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database.dispose')

        container = Container()
        container.scan()

        async with container:
            pass

        assert 'Database.dispose' in disposed

    @pytest.mark.asyncio
    async def it_disposes_on_exception(self) -> None:
        """Calls stop() even when exception occurs in the context."""
        disposed = []

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                pass

            async def dispose(self) -> None:
                disposed.append('Database.dispose')

        container = Container()
        container.scan()

        with pytest.raises(RuntimeError, match='User error'):
            async with container:
                raise RuntimeError('User error')

        # dispose() should still be called
        assert 'Database.dispose' in disposed

    @pytest.mark.asyncio
    async def it_enables_full_lifecycle_pattern(self) -> None:
        """Demonstrates full lifecycle pattern with async context manager."""
        events = []

        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.TEST)
        @lifecycle
        class FakeEmailAdapter:
            async def initialize(self) -> None:
                events.append('email.initialize')

            async def dispose(self) -> None:
                events.append('email.dispose')

            async def send(self, to: str, subject: str, body: str) -> None:
                events.append(f'email.send:{to}')

        @service
        @lifecycle
        class Database:
            async def initialize(self) -> None:
                events.append('db.initialize')

            async def dispose(self) -> None:
                events.append('db.dispose')

        @service
        class UserService:
            def __init__(self, db: Database, email_port: EmailPort) -> None:
                self.db = db
                self.email = email_port

            async def register_user(self, email_addr: str) -> None:
                await self.email.send(email_addr, 'Welcome', 'Hello!')

        container = Container()
        container.scan(profile=Profile.TEST)

        async with container:
            # Components are initialized (in dependency order)
            assert 'db.initialize' in events
            assert 'email.initialize' in events

            # Use the service
            user_service = container.resolve(UserService)
            await user_service.register_user('alice@example.com')
            assert 'email.send:alice@example.com' in events

        # Components are disposed (in reverse dependency order)
        assert 'db.dispose' in events
        assert 'email.dispose' in events
        # Dispose happens after initialize
        assert events.index('db.dispose') > events.index('db.initialize')
        assert events.index('email.dispose') > events.index('email.initialize')
