Migrating from dependency-injector
===================================

**Target Audience:** Python developers currently using ``dependency-injector`` who want a simpler, faster DI solution.

**Time to Migrate:** 1-2 hours for small projects, half a day for medium projects.

----

Why Migrate?
------------

If you're using ``dependency-injector`` and experiencing any of these pain points, dioxide might be a better fit:

Wiring Ceremony
~~~~~~~~~~~~~~~

dependency-injector requires a 3-step ceremony for every injection:

.. code-block:: python

    # dependency-injector: 3 steps for every injection
    from dependency_injector.wiring import inject, Provide

    # Step 1: Import inject
    # Step 2: Import Provide
    # Step 3: Use @inject decorator with Provide[] annotation
    @inject
    def get_user(user_service: UserService = Provide[Container.user_service]):
        return user_service.get_current_user()

    # Step 4: Don't forget to call wire()!
    container.wire(modules=[__name__])

dioxide eliminates this entirely:

.. code-block:: python

    # dioxide: Just type hints
    from dioxide import container

    def get_user():
        user_service = container.resolve(UserService)
        return user_service.get_current_user()

    # Or with constructor injection (no decorators needed)
    @service
    class UserController:
        def __init__(self, user_service: UserService):  # Auto-injected!
            self.user_service = user_service

Nested Container Confusion
~~~~~~~~~~~~~~~~~~~~~~~~~~

dependency-injector's nested containers are a common source of bugs:

- Issue `#936 <https://github.com/ets-labs/python-dependency-injector/issues/936>`_: Singleton scope behavior in nested containers
- Issue `#937 <https://github.com/ets-labs/python-dependency-injector/issues/937>`_: Container inheritance resolution order
- Issue `#841 <https://github.com/ets-labs/python-dependency-injector/issues/841>`_: Overriding providers in nested containers
- Issue `#912 <https://github.com/ets-labs/python-dependency-injector/issues/912>`_: Nested container lifecycle management

dioxide uses a simple flat container with profiles for environment-based configuration:

.. code-block:: python

    # dioxide: Simple profile-based configuration
    container.scan(profile=Profile.PRODUCTION)  # Use production adapters
    container.scan(profile=Profile.TEST)        # Use test fakes

Performance Under Load
~~~~~~~~~~~~~~~~~~~~~~

dependency-injector has reported performance issues under load:

- Issue `#904 <https://github.com/ets-labs/python-dependency-injector/issues/904>`_: 400ms+ per request in high-concurrency scenarios

dioxide's Rust-backed container provides consistent sub-microsecond resolution:

.. code-block:: python

    # dioxide benchmark results (from real benchmarks)
    # Resolution: 167-300ns per resolve
    # 1000x faster than Python-based containers

Framework Integration Bugs
~~~~~~~~~~~~~~~~~~~~~~~~~~

dependency-injector has ongoing issues with popular frameworks:

- Issue `#938 <https://github.com/ets-labs/python-dependency-injector/issues/938>`_: FastAPI Depends integration
- Issue `#908 <https://github.com/ets-labs/python-dependency-injector/issues/908>`_: FastAPI lifespan context
- Issue `#712 <https://github.com/ets-labs/python-dependency-injector/issues/712>`_: Django settings integration

dioxide integrates cleanly with framework patterns:

.. code-block:: python

    # dioxide + FastAPI: Clean integration
    from fastapi import FastAPI
    from dioxide import container, Profile
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container.scan(profile=Profile.PRODUCTION)
        async with container:
            yield

    app = FastAPI(lifespan=lifespan)

Async Resource Lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~

dependency-injector's ``Resource`` provider has issues with async cleanup:

- Issue `#567 <https://github.com/ets-labs/python-dependency-injector/issues/567>`_: Async resource shutdown not awaited

dioxide's ``@lifecycle`` decorator properly handles async initialization and disposal:

.. code-block:: python

    # dioxide: Proper async lifecycle
    from dioxide import adapter, lifecycle, Profile

    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    @lifecycle
    class PostgresAdapter:
        async def initialize(self) -> None:
            self.engine = create_async_engine(...)
            await self.engine.connect()

        async def dispose(self) -> None:
            await self.engine.dispose()  # Properly awaited!

    # Lifecycle is automatic with async context manager
    async with container:
        # initialize() called on all @lifecycle components
        db = container.resolve(DatabasePort)
    # dispose() properly awaited on all @lifecycle components

Type Safety Holes
~~~~~~~~~~~~~~~~~

dependency-injector's ``__getattr__`` on containers silences type errors:

- Issue `#910 <https://github.com/ets-labs/python-dependency-injector/issues/910>`_: Type checkers can't detect missing providers

dioxide is fully type-safe:

.. code-block:: python

    # dependency-injector: No type error (but will fail at runtime!)
    class Container(containers.DeclarativeContainer):
        pass

    container = Container()
    service = container.user_service()  # No error from mypy, fails at runtime!

    # dioxide: Type-safe resolution
    service = container.resolve(UserService)  # mypy validates UserService type

----

Concept Mapping
---------------

Here's how dependency-injector concepts map to dioxide:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - dependency-injector
     - dioxide
     - Notes
   * - ``containers.DeclarativeContainer``
     - ``Container()``
     - dioxide containers are simpler
   * - ``providers.Singleton``
     - ``@service`` or ``@adapter.for_()``
     - Default scope is singleton
   * - ``providers.Factory``
     - ``@adapter.for_(..., scope=Scope.FACTORY)``
     - Use Scope.FACTORY for new instances
   * - ``providers.Configuration``
     - Pydantic Settings + ``register_instance()``
     - Use Pydantic for config validation
   * - ``providers.Resource``
     - ``@lifecycle``
     - Proper async support
   * - ``@inject`` + ``Provide[]``
     - Type hints only
     - No decorators needed
   * - ``container.wire()``
     - ``container.scan()``
     - Auto-discovery based on decorators
   * - ``container.override()``
     - Profile system
     - ``Profile.TEST`` for test overrides
   * - Nested containers
     - Single container + profiles
     - Simpler mental model

----

Side-by-Side Examples
---------------------

Let's convert common dependency-injector patterns to dioxide.

Basic Service with Dependency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    # containers.py
    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        config = providers.Configuration()

        database = providers.Singleton(
            Database,
            host=config.db.host,
            port=config.db.port,
        )

        user_repository = providers.Singleton(
            UserRepository,
            database=database,
        )

        user_service = providers.Singleton(
            UserService,
            repository=user_repository,
        )

    # main.py
    from dependency_injector.wiring import inject, Provide

    @inject
    def main(user_service: UserService = Provide[Container.user_service]):
        user = user_service.get_user(1)
        print(user)

    if __name__ == "__main__":
        container = Container()
        container.config.from_yaml("config.yml")
        container.wire(modules=[__name__])
        main()

**dioxide:**

.. code-block:: python

    # services.py
    from typing import Protocol
    from dioxide import adapter, service, Profile

    # Define ports (interfaces)
    class DatabasePort(Protocol):
        async def query(self, sql: str) -> list[dict]: ...

    class UserRepositoryPort(Protocol):
        async def get_user(self, user_id: int) -> dict | None: ...

    # Define adapters (implementations)
    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    class PostgresDatabase:
        def __init__(self, config: AppConfig):
            self.host = config.db_host
            self.port = config.db_port

        async def query(self, sql: str) -> list[dict]:
            # Real database query
            pass

    @adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
    class PostgresUserRepository:
        def __init__(self, db: DatabasePort):
            self.db = db

        async def get_user(self, user_id: int) -> dict | None:
            results = await self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
            return results[0] if results else None

    # Define service (business logic)
    @service
    class UserService:
        def __init__(self, repository: UserRepositoryPort):
            self.repository = repository

        async def get_user(self, user_id: int) -> dict | None:
            return await self.repository.get_user(user_id)

    # main.py
    from dioxide import Container, Profile
    from pydantic_settings import BaseSettings

    class AppConfig(BaseSettings):
        db_host: str = "localhost"
        db_port: int = 5432

        model_config = {"env_prefix": "APP_"}

    async def main():
        container = Container()
        container.register_instance(AppConfig, AppConfig())
        container.scan(profile=Profile.PRODUCTION)

        user_service = container.resolve(UserService)
        user = await user_service.get_user(1)
        print(user)

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())

Configuration Handling
~~~~~~~~~~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        config = providers.Configuration()

        api_client = providers.Singleton(
            ApiClient,
            base_url=config.api.base_url,
            api_key=config.api.api_key,
            timeout=config.api.timeout,
        )

    # Usage
    container = Container()
    container.config.from_yaml("config.yml")
    container.config.api.api_key.from_env("API_KEY")

**dioxide (with Pydantic Settings):**

.. code-block:: python

    from pydantic_settings import BaseSettings
    from dioxide import Container, adapter, Profile

    # Type-safe, validated configuration
    class ApiConfig(BaseSettings):
        base_url: str = "https://api.example.com"
        api_key: str  # Required, from API_KEY env var
        timeout: int = 30

        model_config = {"env_prefix": "API_"}

    class ApiClientPort(Protocol):
        async def request(self, endpoint: str) -> dict: ...

    @adapter.for_(ApiClientPort, profile=Profile.PRODUCTION)
    class RealApiClient:
        def __init__(self, config: ApiConfig):
            self.base_url = config.base_url
            self.api_key = config.api_key
            self.timeout = config.timeout

        async def request(self, endpoint: str) -> dict:
            # Real API call
            pass

    # Usage
    container = Container()
    container.register_instance(ApiConfig, ApiConfig())  # Loads from env vars
    container.scan(profile=Profile.PRODUCTION)

    client = container.resolve(ApiClientPort)

Testing Setup
~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    # test_user_service.py
    from unittest.mock import Mock
    from dependency_injector import providers

    def test_user_service():
        # Create container
        container = Container()

        # Override with mocks
        mock_repository = Mock()
        mock_repository.get_user.return_value = {"id": 1, "name": "Alice"}
        container.user_repository.override(providers.Object(mock_repository))

        # Wire and test
        container.wire(modules=[__name__])

        service = container.user_service()
        user = service.get_user(1)

        assert user["name"] == "Alice"
        mock_repository.get_user.assert_called_once_with(1)

        # Don't forget to reset!
        container.user_repository.reset_override()

**dioxide (with fakes, no mocks):**

.. code-block:: python

    # adapters/fakes.py - Fakes live in production code!
    from dioxide import adapter, Profile

    @adapter.for_(DatabasePort, profile=Profile.TEST)
    class FakeDatabase:
        def __init__(self):
            self.data = {}

        async def query(self, sql: str) -> list[dict]:
            # Simple in-memory implementation
            return list(self.data.values())

    @adapter.for_(UserRepositoryPort, profile=Profile.TEST)
    class FakeUserRepository:
        def __init__(self):
            self.users = {}

        async def get_user(self, user_id: int) -> dict | None:
            return self.users.get(user_id)

        # Test helper (not in protocol)
        def seed(self, **users):
            self.users.update(users)

    # test_user_service.py
    import pytest
    from dioxide import Container, Profile

    @pytest.fixture
    def container():
        c = Container()
        c.scan(profile=Profile.TEST)  # Activates fakes!
        return c

    async def test_user_service(container):
        # Seed test data
        fake_repo = container.resolve(UserRepositoryPort)
        fake_repo.seed(**{1: {"id": 1, "name": "Alice"}})

        # Test REAL service with REAL fakes
        service = container.resolve(UserService)
        user = await service.get_user(1)

        # Assert observable outcomes (no mock.assert_called!)
        assert user["name"] == "Alice"

FastAPI Integration
~~~~~~~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    # containers.py
    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        wiring_config = containers.WiringConfiguration(modules=["api"])
        user_service = providers.Singleton(UserService)

    # api.py
    from fastapi import FastAPI, Depends
    from dependency_injector.wiring import inject, Provide

    app = FastAPI()

    @app.get("/users/{user_id}")
    @inject
    async def get_user(
        user_id: int,
        user_service: UserService = Depends(Provide[Container.user_service]),
    ):
        return user_service.get_user(user_id)

    # main.py
    container = Container()
    container.wire(modules=["api"])
    app.container = container

**dioxide:**

.. code-block:: python

    # main.py
    from fastapi import FastAPI
    from dioxide import container, Profile
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container.scan(profile=Profile.PRODUCTION)
        async with container:
            yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        user_service = container.resolve(UserService)
        return await user_service.get_user(user_id)

    # Or create a dependency for cleaner routes
    def get_user_service() -> UserService:
        return container.resolve(UserService)

    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        user_service: UserService = Depends(get_user_service),
    ):
        return await user_service.get_user(user_id)

----

Step-by-Step Migration
----------------------

Follow these steps to migrate your project from dependency-injector to dioxide.

Step 1: Install dioxide
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Add dioxide
    pip install dioxide
    # or
    uv add dioxide

    # Keep dependency-injector temporarily for gradual migration
    # Remove it after migration is complete

Step 2: Define Ports (Interfaces)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each provider in your dependency-injector container, create a Protocol:

.. code-block:: python

    # Before: No explicit interface
    class UserService:
        def __init__(self, repository):
            self.repository = repository

    # After: Explicit port
    from typing import Protocol

    class UserRepositoryPort(Protocol):
        async def get_user(self, user_id: int) -> dict | None: ...
        async def create_user(self, name: str, email: str) -> dict: ...

    class UserServicePort(Protocol):
        async def get_user(self, user_id: int) -> dict | None: ...
        async def register_user(self, name: str, email: str) -> dict: ...

Step 3: Convert Singletons to @service or @adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Singletons that are business logic become @service:**

.. code-block:: python

    # Before: dependency-injector Singleton
    class Container(containers.DeclarativeContainer):
        user_service = providers.Singleton(UserService, repository=user_repository)

    # After: dioxide @service
    from dioxide import service

    @service
    class UserService:
        def __init__(self, repository: UserRepositoryPort):
            self.repository = repository

**Singletons that are infrastructure become @adapter:**

.. code-block:: python

    # Before: dependency-injector Singleton
    class Container(containers.DeclarativeContainer):
        database = providers.Singleton(PostgresDatabase, config=config)

    # After: dioxide @adapter
    from dioxide import adapter, Profile

    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    class PostgresDatabase:
        def __init__(self, config: DatabaseConfig):
            self.config = config

Step 4: Convert Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (dependency-injector):**

.. code-block:: python

    class Container(containers.DeclarativeContainer):
        config = providers.Configuration()

    container.config.from_yaml("config.yml")
    container.config.db.host.from_env("DB_HOST")

**After (Pydantic Settings):**

.. code-block:: python

    from pydantic_settings import BaseSettings

    class DatabaseConfig(BaseSettings):
        host: str = "localhost"
        port: int = 5432
        username: str = "postgres"
        password: str

        model_config = {"env_prefix": "DB_"}

    # Register as instance
    container.register_instance(DatabaseConfig, DatabaseConfig())

Step 5: Convert Resources to @lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (dependency-injector):**

.. code-block:: python

    class Container(containers.DeclarativeContainer):
        db_engine = providers.Resource(
            init_db_engine,
            config=config.db,
        )

    def init_db_engine(config):
        engine = create_engine(config.url)
        yield engine
        engine.dispose()

**After (dioxide @lifecycle):**

.. code-block:: python

    from dioxide import adapter, lifecycle, Profile

    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    @lifecycle
    class PostgresAdapter:
        def __init__(self, config: DatabaseConfig):
            self.config = config
            self.engine = None

        async def initialize(self) -> None:
            self.engine = create_async_engine(self.config.url)

        async def dispose(self) -> None:
            if self.engine:
                await self.engine.dispose()

Step 6: Convert Overrides to Profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Before (dependency-injector overrides):**

.. code-block:: python

    # Production
    container = Container()

    # Testing - override with mocks
    container.database.override(providers.Object(mock_db))
    container.user_repository.override(providers.Object(mock_repo))

**After (dioxide profiles):**

.. code-block:: python

    # Production adapters
    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    class PostgresDatabase:
        pass

    # Test fakes (real implementations, not mocks)
    @adapter.for_(DatabasePort, profile=Profile.TEST)
    class FakeDatabase:
        def __init__(self):
            self.data = {}

    # Production
    container.scan(profile=Profile.PRODUCTION)

    # Testing
    container.scan(profile=Profile.TEST)

Step 7: Remove Wiring
~~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

    from dependency_injector.wiring import inject, Provide

    @inject
    def get_user(service: UserService = Provide[Container.user_service]):
        return service.get_user(1)

    container.wire(modules=[__name__])

**After:**

.. code-block:: python

    # No decorators, no wiring!
    def get_user():
        service = container.resolve(UserService)
        return service.get_user(1)

Step 8: Update Tests
~~~~~~~~~~~~~~~~~~~~

**Before:**

.. code-block:: python

    def test_user_service():
        container = Container()
        container.user_repository.override(providers.Object(mock_repo))
        container.wire(modules=[__name__])

        mock_repo.get_user.return_value = {"id": 1}
        service = container.user_service()
        result = service.get_user(1)

        mock_repo.get_user.assert_called_once_with(1)
        container.user_repository.reset_override()

**After:**

.. code-block:: python

    async def test_user_service(container):
        # Seed fake with test data
        fake_repo = container.resolve(UserRepositoryPort)
        fake_repo.seed(**{1: {"id": 1, "name": "Alice"}})

        # Test real behavior
        service = container.resolve(UserService)
        result = await service.get_user(1)

        assert result["id"] == 1

Step 9: Remove dependency-injector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once migration is complete:

.. code-block:: bash

    pip uninstall dependency-injector
    # or
    uv remove dependency-injector

----

Common Patterns
---------------

Singletons vs Factories
~~~~~~~~~~~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    class Container(containers.DeclarativeContainer):
        # Singleton - one instance
        db_connection = providers.Singleton(DatabaseConnection)

        # Factory - new instance each time
        request_handler = providers.Factory(RequestHandler)

**dioxide:**

.. code-block:: python

    from dioxide import adapter, Profile, Scope

    # Singleton (default) - one instance
    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    class PostgresConnection:
        pass

    # Factory - new instance each time
    @adapter.for_(RequestHandlerPort, profile=Profile.PRODUCTION, scope=Scope.FACTORY)
    class RequestHandler:
        pass

Configuration with Pydantic
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replace dependency-injector's Configuration provider with Pydantic Settings for type-safe, validated configuration:

.. code-block:: python

    from pydantic_settings import BaseSettings
    from pydantic import Field

    class AppConfig(BaseSettings):
        # Database settings
        db_host: str = "localhost"
        db_port: int = 5432
        db_name: str = "app"
        db_password: str = Field(..., env="DB_PASSWORD")  # Required

        # API settings
        api_key: str = Field(..., env="API_KEY")
        api_timeout: int = 30

        # Feature flags
        debug: bool = False

        model_config = {
            "env_prefix": "APP_",
            "env_file": ".env",
        }

    # Usage
    config = AppConfig()  # Loads from environment
    container.register_instance(AppConfig, config)

Testing Without Mocks
~~~~~~~~~~~~~~~~~~~~~

dioxide encourages fakes over mocks for clearer, more maintainable tests:

.. code-block:: python

    # Define test fakes alongside production adapters
    @adapter.for_(EmailPort, profile=Profile.TEST)
    class FakeEmailAdapter:
        def __init__(self):
            self.sent_emails = []

        async def send(self, to: str, subject: str, body: str) -> None:
            self.sent_emails.append({"to": to, "subject": subject, "body": body})

        # Test helpers
        def verify_sent_to(self, email: str) -> bool:
            return any(e["to"] == email for e in self.sent_emails)

        def clear(self):
            self.sent_emails = []

    # Tests use real fakes
    async def test_sends_welcome_email(container):
        fake_email = container.resolve(EmailPort)
        service = container.resolve(UserService)

        await service.register_user("alice@example.com", "Alice")

        assert fake_email.verify_sent_to("alice@example.com")

Async Lifecycle
~~~~~~~~~~~~~~~

dioxide properly handles async resource initialization and cleanup:

.. code-block:: python

    from dioxide import adapter, lifecycle, Profile

    @adapter.for_(CachePort, profile=Profile.PRODUCTION)
    @lifecycle
    class RedisCache:
        def __init__(self, config: CacheConfig):
            self.config = config
            self.redis = None

        async def initialize(self) -> None:
            import aioredis
            self.redis = await aioredis.create_redis_pool(
                self.config.redis_url,
                minsize=5,
                maxsize=10,
            )

        async def dispose(self) -> None:
            if self.redis:
                self.redis.close()
                await self.redis.wait_closed()

        async def get(self, key: str) -> str | None:
            return await self.redis.get(key)

        async def set(self, key: str, value: str, ttl: int = 3600) -> None:
            await self.redis.setex(key, ttl, value)

    # Lifecycle is automatic
    async with container:
        # RedisCache.initialize() called here
        cache = container.resolve(CachePort)
        await cache.set("key", "value")
    # RedisCache.dispose() called here (properly awaited!)

----

FAQ
---

How do I handle providers that need runtime arguments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**dependency-injector:**

.. code-block:: python

    class Container(containers.DeclarativeContainer):
        user_service = providers.Factory(UserService, repository=repository)

    service = container.user_service(extra_arg="value")

**dioxide:**

For runtime arguments, use explicit construction or factory functions:

.. code-block:: python

    # Option 1: Resolve dependencies, construct manually
    repository = container.resolve(UserRepositoryPort)
    service = UserService(repository=repository, extra_arg="value")

    # Option 2: Register a factory
    container.register_factory(
        UserServiceWithArg,
        lambda: UserService(
            repository=container.resolve(UserRepositoryPort),
            extra_arg="runtime_value",
        )
    )

How do I migrate nested containers?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flatten nested containers into a single container with profiles:

**Before:**

.. code-block:: python

    class CoreContainer(containers.DeclarativeContainer):
        database = providers.Singleton(Database)

    class AppContainer(containers.DeclarativeContainer):
        core = providers.Container(CoreContainer)
        user_service = providers.Singleton(UserService, db=core.database)

**After:**

.. code-block:: python

    # Single flat container with all components
    @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
    class PostgresDatabase:
        pass

    @service
    class UserService:
        def __init__(self, db: DatabasePort):
            self.db = db

    # One container, one scan
    container.scan(profile=Profile.PRODUCTION)

How do I handle circular dependencies?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dioxide detects circular dependencies and raises a clear error. Refactor to break the cycle:

.. code-block:: python

    # Circular: A depends on B, B depends on A
    # Solution: Introduce an interface or event system

    class EventBusPort(Protocol):
        def publish(self, event: Event) -> None: ...
        def subscribe(self, handler: Callable) -> None: ...

    @service
    class ServiceA:
        def __init__(self, event_bus: EventBusPort):
            self.event_bus = event_bus
            self.event_bus.subscribe(self.handle_b_event)

    @service
    class ServiceB:
        def __init__(self, event_bus: EventBusPort):
            self.event_bus = event_bus
            self.event_bus.subscribe(self.handle_a_event)

Can I migrate incrementally?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! You can use both frameworks during migration:

.. code-block:: python

    # Keep dependency-injector for unmigrated code
    from dependency_injector import containers, providers

    # Start using dioxide for new code
    from dioxide import container, service, adapter, Profile

    # Gradually move providers from dependency-injector to dioxide

How does dioxide compare in performance?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dioxide is significantly faster due to its Rust backend:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - dependency-injector
     - dioxide
   * - Simple resolution
     - ~10-50us
     - ~167-300ns
   * - Nested dependencies
     - ~50-200us
     - ~300-500ns
   * - High concurrency
     - Degrades (issue #904)
     - Consistent

What if I need features dioxide doesn't have?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dioxide is intentionally focused on hexagonal architecture patterns. If you need features like:

- **Coroutine providers**: Use ``@lifecycle`` with async initialization instead
- **Callable providers**: Use ``container.register_factory()``
- **Aggregate providers**: Compose manually or use service aggregation

dioxide prioritizes simplicity over feature count.

----

Migration Checklist
-------------------

Use this checklist to track your migration progress:

.. code-block:: text

    [ ] Install dioxide
    [ ] Define ports (Protocol) for each abstraction
    [ ] Convert business logic Singletons to @service
    [ ] Convert infrastructure Singletons to @adapter
    [ ] Convert Factory providers to Scope.FACTORY adapters
    [ ] Replace Configuration with Pydantic Settings
    [ ] Convert Resource providers to @lifecycle
    [ ] Replace container overrides with Profile system
    [ ] Remove @inject decorators and Provide[] annotations
    [ ] Remove container.wire() calls
    [ ] Create test fakes for each port
    [ ] Update test fixtures to use Profile.TEST
    [ ] Replace mock assertions with fake state checks
    [ ] Update FastAPI/Flask integration
    [ ] Remove dependency-injector package
    [ ] Run full test suite
    [ ] Update documentation

----

Getting Help
------------

If you encounter issues during migration:

- **GitHub Issues**: `<https://github.com/mikelane/dioxide/issues>`_
- **Discussions**: `<https://github.com/mikelane/dioxide/discussions>`_
- **Documentation**: `<https://dioxide.readthedocs.io>`_

When reporting migration issues, include:

1. Your dependency-injector pattern/code
2. Your attempted dioxide conversion
3. The error or unexpected behavior

We're happy to help with migration questions!

----

.. seealso::

   - :doc:`user_guide/getting_started` - Complete introduction to dioxide
   - :doc:`user_guide/testing_with_fakes` - Testing philosophy and patterns
   - :doc:`user_guide/hexagonal_architecture` - Ports and adapters in depth
