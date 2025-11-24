"""Lifecycle management decorator for dioxide components.

The @lifecycle decorator enables opt-in lifecycle management for services and
adapters that need initialization and cleanup. It provides guaranteed startup
and shutdown ordering based on dependency relationships, making it ideal for
managing resources like database connections, caches, message queues, and other
infrastructure components.

In hexagonal architecture, lifecycle management is essential at the seams (adapters)
where your application connects to external systems. The @lifecycle decorator ensures
these connections are established before your application starts processing requests
and gracefully shut down when the application stops.

Key Features:
    - **Dependency-ordered initialization**: Components initialized in dependency order
    - **Reverse-order disposal**: Cleanup happens in reverse dependency order
    - **Async context manager**: Use ``async with container:`` for automatic lifecycle
    - **Type-safe validation**: Validates initialize() and dispose() methods at decoration time
    - **Rollback on failure**: If initialization fails, already-initialized components are cleaned up
    - **Works with @service and @adapter**: Composable with other dioxide decorators

The lifecycle flow follows this pattern:

1. Container.start() or async with container:
   - Build dependency graph of all @lifecycle components
   - Sort topologically (dependencies before dependents)
   - Call initialize() on each component in order
   - If any initialize() fails, rollback by disposing already-initialized components

2. Application runs normally with all resources ready

3. Container.stop() or async context exit:
   - Call dispose() on all components in reverse order
   - Continue cleanup even if individual dispose() calls fail
   - Log disposal errors but don't raise (best-effort cleanup)

Basic Example:
    Database adapter with lifecycle management::

        from dioxide import adapter, Profile, lifecycle
        from sqlalchemy.ext.asyncio import create_async_engine

        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            def __init__(self, config: AppConfig):
                self.config = config
                self.engine = None

            async def initialize(self) -> None:
                \"\"\"Called automatically when container starts.\"\"\"
                self.engine = create_async_engine(self.config.database_url)
                # Test connection
                async with self.engine.connect() as conn:
                    await conn.execute("SELECT 1")
                print(f"Connected to {self.config.database_url}")

            async def dispose(self) -> None:
                \"\"\"Called automatically when container stops.\"\"\"
                if self.engine:
                    await self.engine.dispose()
                    print("Database connection closed")

            async def query(self, sql: str) -> list[dict]:
                async with self.engine.connect() as conn:
                    result = await conn.execute(sql)
                    return result.fetchall()

Advanced Example:
    Multiple lifecycle components with dependencies::

        from dioxide import adapter, service, lifecycle, Profile


        # Cache depends on nothing - initialized first
        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisCache:
            async def initialize(self) -> None:
                self.redis = await aioredis.create_redis_pool('redis://localhost')
                print('Redis connected')

            async def dispose(self) -> None:
                self.redis.close()
                await self.redis.wait_closed()
                print('Redis disconnected')


        # Database depends on nothing - initialized first (parallel with cache)
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                self.engine = create_async_engine('postgresql://...')
                print('Database connected')

            async def dispose(self) -> None:
                await self.engine.dispose()
                print('Database disconnected')


        # Service depends on cache and database - initialized last
        @service
        @lifecycle
        class UserService:
            def __init__(self, cache: CachePort, db: DatabasePort):
                self.cache = cache
                self.db = db

            async def initialize(self) -> None:
                # Warm up cache
                users = await self.db.query('SELECT * FROM users')
                for user in users:
                    await self.cache.set(f'user:{user.id}', user)
                print('UserService cache warmed')

            async def dispose(self) -> None:
                # Flush pending operations
                print('UserService cleanup complete')


        # Initialization order: RedisCache, PostgresAdapter, UserService
        # Disposal order: UserService, PostgresAdapter, RedisCache

Container Usage:
    Manual lifecycle control::

        from dioxide import Container, Profile

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        # Start all @lifecycle components
        await container.start()

        # Use services (all resources are initialized)
        user_service = container.resolve(UserService)
        users = await user_service.find_all()

        # Stop all @lifecycle components (reverse order)
        await container.stop()

    Async context manager (recommended)::

        from dioxide import Container, Profile

        async with Container() as container:
            container.scan(profile=Profile.PRODUCTION)
            # All @lifecycle components initialized here

            user_service = container.resolve(UserService)
            users = await user_service.find_all()

        # All @lifecycle components disposed here (even if exception raised)

Testing with Lifecycle:
    Use fast fakes that don't need real resources::

        from dioxide import adapter, Profile, lifecycle


        @adapter.for_(DatabasePort, profile=Profile.TEST)
        @lifecycle
        class FakeDatabaseAdapter:
            async def initialize(self) -> None:
                self.records = {}
                print('Fake database ready (no real connection)')

            async def dispose(self) -> None:
                self.records.clear()
                print('Fake database cleared')

            async def query(self, sql: str) -> list[dict]:
                # Fast in-memory queries
                return list(self.records.values())


        # Test container - uses fake adapters, no real infrastructure needed
        async with Container() as container:
            container.scan(profile=Profile.TEST)
            # Fast initialization - no network calls

            service = container.resolve(UserService)
            await service.create_user('alice@example.com')

        # Fast cleanup - no network calls

Error Handling:
    Initialization failure with automatic rollback::

        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                self.engine = create_async_engine('postgresql://...')
                # If connection fails, raises exception
                async with self.engine.connect() as conn:
                    await conn.execute('SELECT 1')


        async with Container() as container:
            try:
                container.scan(profile=Profile.PRODUCTION)
                # If database connection fails during start():
                # - initialize() raises exception
                # - Container automatically calls dispose() on already-initialized components
                # - Exception propagates to caller
            except Exception as e:
                print(f'Startup failed: {e}')
                # All initialized components have been cleaned up

Best Practices:
    - **Keep initialize() fast**: Avoid expensive operations, defer to first use if possible
    - **Make dispose() idempotent**: Safe to call multiple times, check if resources exist
    - **Don't raise in dispose()**: Log errors but continue cleanup (best-effort)
    - **Use for adapters, not services**: Services rarely need lifecycle (they're stateless logic)
    - **Test with fakes**: Use fast fake adapters in tests, no lifecycle overhead
    - **Connection pooling**: Initialize connection pools in initialize(), dispose in dispose()
    - **Graceful degradation**: Handle initialization failures gracefully

Common Patterns:
    Database connection pool::

        @lifecycle
        class DatabaseAdapter:
            async def initialize(self) -> None:
                self.pool = await asyncpg.create_pool(...)

            async def dispose(self) -> None:
                if self.pool:
                    await self.pool.close()

    Message queue consumer::

        @lifecycle
        class MessageQueueAdapter:
            async def initialize(self) -> None:
                self.consumer = await create_consumer(...)
                await self.consumer.start()

            async def dispose(self) -> None:
                if self.consumer:
                    await self.consumer.stop()

    HTTP session::

        @lifecycle
        class HttpClientAdapter:
            async def initialize(self) -> None:
                self.session = aiohttp.ClientSession()

            async def dispose(self) -> None:
                if self.session:
                    await self.session.close()

See Also:
    - :class:`dioxide.container.Container.start` - Initialize lifecycle components
    - :class:`dioxide.container.Container.stop` - Dispose lifecycle components
    - :class:`dioxide.adapter.adapter` - For marking boundary implementations
    - :class:`dioxide.services.service` - For core domain logic
    - :class:`dioxide.exceptions.CircularDependencyError` - Raised on circular dependencies
"""

import inspect
from typing import TypeVar

T = TypeVar('T', bound=type)


def lifecycle(cls: T) -> T:
    """Mark a class for lifecycle management with initialization and cleanup.

    The @lifecycle decorator marks a service or adapter as requiring lifecycle
    management, which means it needs to be initialized before use and disposed
    of when the application shuts down. This is essential for managing resources
    like database connections, caches, message queues, and other infrastructure
    components that require setup and teardown.

    The decorator performs compile-time validation to ensure the decorated class
    implements the required async methods. This provides early error detection
    (at import time) rather than runtime failures.

    Required Methods:
        The decorated class MUST implement both of these async methods:

        - ``async def initialize(self) -> None``:
            Called once when the container starts (via ``container.start()`` or
            ``async with container:``). Use this to establish connections, load
            resources, warm caches, etc. This method is called in dependency order
            (dependencies are initialized before their dependents).

        - ``async def dispose(self) -> None``:
            Called once when the container stops (via ``container.stop()`` or when
            exiting the ``async with`` block). Use this to close connections, flush
            buffers, release resources, etc. This method is called in reverse
            dependency order (dependents are disposed before their dependencies).
            Should be idempotent and not raise exceptions.

    Decorator Composition:
        @lifecycle works with both @service and @adapter.for_() decorators.
        Apply @lifecycle as the innermost decorator (closest to the class):

        - ``@service`` + ``@lifecycle`` - For stateful core logic (rare)
        - ``@adapter.for_()`` + ``@lifecycle`` - For infrastructure adapters (common)

    Args:
        cls: The class to mark for lifecycle management. Must implement both
            ``initialize()`` and ``dispose()`` methods as async coroutines.

    Returns:
        The decorated class with ``_dioxide_lifecycle = True`` attribute set.
        The class can be used normally and will be discovered by the container.

    Raises:
        TypeError: If the class does not implement ``initialize()`` method.
        TypeError: If ``initialize()`` is not an async coroutine function.
        TypeError: If the class does not implement ``dispose()`` method.
        TypeError: If ``dispose()`` is not an async coroutine function.

    Examples:
        Service with lifecycle (stateful core logic)::

            from dioxide import service, lifecycle


            @service
            @lifecycle
            class CacheWarmer:
                def __init__(self, db: DatabasePort):
                    self.db = db
                    self.cache = {}

                async def initialize(self) -> None:
                    # Load all users into memory cache
                    users = await self.db.query('SELECT * FROM users')
                    for user in users:
                        self.cache[user.id] = user
                    print(f'Cache warmed with {len(users)} users')

                async def dispose(self) -> None:
                    # Flush any pending writes
                    self.cache.clear()
                    print('Cache cleared')

        Adapter with lifecycle (infrastructure connection)::

            from dioxide import adapter, Profile, lifecycle


            @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
            @lifecycle
            class PostgresAdapter:
                def __init__(self, config: AppConfig):
                    self.config = config
                    self.engine = None

                async def initialize(self) -> None:
                    # Establish database connection pool
                    self.engine = create_async_engine(self.config.database_url, pool_size=10, max_overflow=20)
                    # Verify connection
                    async with self.engine.connect() as conn:
                        await conn.execute('SELECT 1')
                    print('Database connection established')

                async def dispose(self) -> None:
                    # Close all connections in pool
                    if self.engine:
                        await self.engine.dispose()
                        self.engine = None
                    print('Database connection closed')

                async def query(self, sql: str) -> list[dict]:
                    async with self.engine.connect() as conn:
                        result = await conn.execute(sql)
                        return [dict(row) for row in result]

        Multiple lifecycle components with dependencies::

            # Database adapter (no dependencies) - initialized first
            @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
            @lifecycle
            class PostgresAdapter:
                async def initialize(self) -> None:
                    self.engine = create_async_engine(...)

                async def dispose(self) -> None:
                    await self.engine.dispose()


            # Service depends on database - initialized after database
            @service
            @lifecycle
            class UserRepository:
                def __init__(self, db: DatabasePort):
                    self.db = db
                    self.initialized = False

                async def initialize(self) -> None:
                    # Database is already initialized at this point
                    # Run migrations or setup
                    await self.db.query('CREATE TABLE IF NOT EXISTS users ...')
                    self.initialized = True

                async def dispose(self) -> None:
                    self.initialized = False


            # Container handles dependency order automatically:
            # 1. PostgresAdapter.initialize()
            # 2. UserRepository.initialize()
            # ... application runs ...
            # 1. UserRepository.dispose()
            # 2. PostgresAdapter.dispose()

        Validation errors at decoration time::

            @service
            @lifecycle
            class BrokenService:
                # Missing initialize() and dispose() methods
                pass


            # Raises TypeError: BrokenService must implement initialize() method


            @service
            @lifecycle
            class SyncService:
                def initialize(self) -> None:  # Not async!
                    pass

                async def dispose(self) -> None:
                    pass


            # Raises TypeError: SyncService.initialize() must be async

    Best Practices:
        - **Keep initialize() fast**: Avoid expensive operations, connection checks only
        - **Make dispose() idempotent**: Safe to call multiple times (check if resource exists)
        - **Don't raise in dispose()**: Log errors but continue cleanup (best-effort)
        - **Use for adapters**: Infrastructure components at the seams (databases, queues, etc.)
        - **Rare for services**: Core domain logic is usually stateless (no lifecycle needed)
        - **Apply as innermost decorator**: ``@adapter.for_() @lifecycle class ...``

    See Also:
        - :class:`dioxide.container.Container.start` - Initialize all lifecycle components
        - :class:`dioxide.container.Container.stop` - Dispose all lifecycle components
        - :class:`dioxide.adapter.adapter` - For marking infrastructure adapters
        - :class:`dioxide.services.service` - For marking core domain services
    """
    # Validate that initialize() method exists
    if not hasattr(cls, 'initialize'):
        msg = f'{cls.__name__} must implement initialize() method'
        raise TypeError(msg)

    # Validate that initialize() is async
    init_method = cls.initialize
    if not inspect.iscoroutinefunction(init_method):
        msg = f'{cls.__name__}.initialize() must be async'
        raise TypeError(msg)

    # Validate that dispose() method exists
    if not hasattr(cls, 'dispose'):
        msg = f'{cls.__name__} must implement dispose() method'
        raise TypeError(msg)

    # Validate that dispose() is async
    dispose_method = cls.dispose  # type: ignore[attr-defined]
    if not inspect.iscoroutinefunction(dispose_method):
        msg = f'{cls.__name__}.dispose() must be async'
        raise TypeError(msg)

    cls._dioxide_lifecycle = True  # type: ignore[attr-defined]
    return cls
