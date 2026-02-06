"""Profile-based dependency injection container with lifecycle management.

The Container class is the heart of dioxide's dependency injection system,
providing profile-based component scanning, automatic dependency resolution,
and opt-in lifecycle management for services and adapters.

In hexagonal architecture, the container serves as the composition root where
you wire together services (core domain logic) and adapters (infrastructure
implementations). By using profiles, you can swap out infrastructure implementations
based on environment (production vs test vs development) without changing core logic.

Key Features:
    - **Profile-based scanning**: Activate different adapters per environment
    - **Automatic dependency injection**: Constructor parameters resolved via type hints
    - **Lifecycle management**: Optional initialize/dispose for infrastructure resources
    - **Type-safe resolution**: Full mypy support with IDE autocomplete
    - **Port-based resolution**: Resolve abstract ports, get active adapter
    - **Singleton caching**: Shared instances managed by high-performance Rust core
    - **Async context manager**: Automatic lifecycle with ``async with container:``

Architecture Overview:
    dioxide implements hexagonal architecture (ports and adapters pattern):

    - **Ports**: Abstract interfaces (Protocols/ABCs) defining contracts
    - **Adapters**: Concrete implementations of ports (infrastructure at the seams)
    - **Services**: Core domain logic depending on ports (not concrete adapters)
    - **Container**: Composition root that wires services to adapters based on profile

    The container ensures services remain decoupled from infrastructure by:
    1. Services declare dependencies on ports (abstractions)
    2. Adapters register as implementations for ports with profiles
    3. Container injects the active adapter when resolving the port
    4. Tests use fast fake adapters, production uses real infrastructure

Profile System:
    Profiles determine which adapter implementations are active:

    - **Profile.PRODUCTION**: Real infrastructure (SendGrid, PostgreSQL, Redis, etc.)
    - **Profile.TEST**: Fast fakes for testing (in-memory, no network calls)
    - **Profile.DEVELOPMENT**: Developer-friendly implementations (console, files, etc.)
    - **Profile.STAGING**: Staging environment configurations
    - **Profile.CI**: Continuous integration environment
    - **Profile.ALL** (``'*'``): Available in all profiles (universal adapters)

    Services are profile-agnostic (available in ALL profiles) while adapters are
    profile-specific. This enables swapping infrastructure without changing domain logic.

Basic Example:
    Automatic discovery with profile-based adapters::

        from typing import Protocol
        from dioxide import Container, adapter, service, Profile


        # Port (interface) - defines contract
        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...


        # Production adapter - real SendGrid
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                # Real SendGrid API calls
                async with httpx.AsyncClient() as client:
                    await client.post('https://api.sendgrid.com/v3/mail/send', ...)


        # Test adapter - fast fake
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def __init__(self):
                self.sent_emails = []

            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})


        # Service - depends on PORT, not concrete adapter
        @service
        class UserService:
            def __init__(self, email: EmailPort):
                self.email = email  # Container injects active adapter

            async def register(self, email_addr: str, name: str):
                # Core logic - doesn't know which adapter is active
                await self.email.send(email_addr, 'Welcome!', f'Hello {name}!')


        # Production container - uses SendGridAdapter
        prod_container = Container()
        prod_container.scan(profile=Profile.PRODUCTION)
        prod_service = prod_container.resolve(UserService)
        # prod_service.email is SendGridAdapter

        # Test container - uses FakeEmailAdapter
        test_container = Container()
        test_container.scan(profile=Profile.TEST)
        test_service = test_container.resolve(UserService)
        # test_service.email is FakeEmailAdapter

        # Tests run fast with fakes, production uses real infrastructure
        # Core domain logic (UserService) stays the same

Lifecycle Management Example:
    Initialize and dispose resources automatically::

        from dioxide import Container, adapter, lifecycle, Profile
        from sqlalchemy.ext.asyncio import create_async_engine


        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            def __init__(self, config: AppConfig):
                self.config = config
                self.engine = None

            async def initialize(self) -> None:
                # Called automatically when container starts
                self.engine = create_async_engine(self.config.database_url)
                print('Database connected')

            async def dispose(self) -> None:
                # Called automatically when container stops
                if self.engine:
                    await self.engine.dispose()
                print('Database disconnected')

            async def query(self, sql: str) -> list[dict]:
                async with self.engine.connect() as conn:
                    result = await conn.execute(sql)
                    return [dict(row) for row in result]


        # Manual lifecycle control
        container = Container()
        container.scan(profile=Profile.PRODUCTION)
        await container.start()  # Calls PostgresAdapter.initialize()
        db = container.resolve(DatabasePort)
        users = await db.query('SELECT * FROM users')
        await container.stop()  # Calls PostgresAdapter.dispose()

        # Async context manager (recommended)
        async with Container() as container:
            container.scan(profile=Profile.PRODUCTION)
            # PostgresAdapter.initialize() called here
            db = container.resolve(DatabasePort)
            users = await db.query('SELECT * FROM users')
        # PostgresAdapter.dispose() called here (even if exception raised)

Advanced Example:
    Multiple adapters with dependencies and lifecycle::

        from dioxide import Container, adapter, service, lifecycle, Profile


        # Cache adapter (no dependencies) - initialized first
        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisCache:
            async def initialize(self) -> None:
                self.redis = await aioredis.create_redis_pool('redis://localhost')

            async def dispose(self) -> None:
                self.redis.close()
                await self.redis.wait_closed()

            async def get(self, key: str) -> str | None:
                return await self.redis.get(key)

            async def set(self, key: str, value: str) -> None:
                await self.redis.set(key, value)


        # Database adapter (no dependencies) - initialized first
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        @lifecycle
        class PostgresAdapter:
            async def initialize(self) -> None:
                self.engine = create_async_engine('postgresql://...')

            async def dispose(self) -> None:
                await self.engine.dispose()

            async def query(self, sql: str) -> list[dict]:
                async with self.engine.connect() as conn:
                    result = await conn.execute(sql)
                    return [dict(row) for row in result]


        # Service depends on cache and database - initialized last
        @service
        @lifecycle
        class UserRepository:
            def __init__(self, cache: CachePort, db: DatabasePort):
                self.cache = cache
                self.db = db

            async def initialize(self) -> None:
                # Both adapters are already initialized
                # Warm cache with users from database
                users = await self.db.query('SELECT * FROM users')
                for user in users:
                    await self.cache.set(f'user:{user["id"]}', user['email'])

            async def dispose(self) -> None:
                # Flush any pending operations
                pass


        # Container manages initialization order automatically:
        # 1. RedisCache.initialize()
        # 2. PostgresAdapter.initialize()
        # 3. UserRepository.initialize() (after dependencies ready)
        # ... application runs ...
        # 1. UserRepository.dispose() (before dependencies)
        # 2. PostgresAdapter.dispose()
        # 3. RedisCache.dispose()

        async with Container() as container:
            container.scan(profile=Profile.PRODUCTION)
            repo = container.resolve(UserRepository)
            # All @lifecycle components initialized in dependency order
            user = await repo.find_by_email('alice@example.com')
        # All @lifecycle components disposed in reverse dependency order

Testing Example:
    Fast tests with fake adapters::

        import pytest
        from dioxide import Container, Profile


        @pytest.fixture
        async def container():
            async with Container() as c:
                c.scan(profile=Profile.TEST)
                # Fast fake adapters initialized (no real infrastructure)
                yield c
            # Cleanup happens automatically


        async def test_user_registration(container):
            # Arrange
            service = container.resolve(UserService)
            email = container.resolve(EmailPort)  # FakeEmailAdapter

            # Act
            await service.register('alice@example.com', 'Alice')

            # Assert - check observable outcomes using fake's state
            assert len(email.sent_emails) == 1
            assert email.sent_emails[0]['to'] == 'alice@example.com'
            assert 'Welcome' in email.sent_emails[0]['subject']


        # Tests run in milliseconds, no network calls, fully isolated

Global Container Instance:
    For simple scripts and CLI tools, use the global singleton container::

        from dioxide import container, Profile

        # Setup once at application startup
        container.scan(profile=Profile.PRODUCTION)

        # Resolve services anywhere in your app
        user_service = container.resolve(UserService)

        # With lifecycle
        async with container:
            # All @lifecycle components initialized
            await app.run()
        # All @lifecycle components disposed

    .. note::

        For testing, libraries, and larger applications, prefer **instance containers**
        (``Container()``) over the global container. Instance containers provide better
        isolation and are easier to test. See the user guide for details:
        :doc:`/docs/user_guide/container_patterns`

Manual Registration Example:
    Register components without decorators::

        from dioxide import Container


        class Config:
            def __init__(self, env: str):
                self.env = env


        container = Container()

        # Register pre-created instance
        config = Config('production')
        container.register_instance(Config, config)

        # Register singleton factory
        container.register_singleton(Logger, lambda: Logger(config))

        # Register transient factory (new instance each time)
        container.register_factory(RequestContext, lambda: RequestContext())

        # Resolve components
        config = container.resolve(Config)
        logger = container.resolve(Logger)

Security:
    Restrict which packages can be scanned to prevent code execution::

        # Only allow scanning within your application packages
        container = Container(allowed_packages=['myapp', 'tests'])
        container.scan(package='myapp.services')  # OK
        container.scan(package='os')  # Raises ValueError

Error Handling:
    Descriptive errors with troubleshooting hints::

        from dioxide.exceptions import AdapterNotFoundError, ServiceNotFoundError

        try:
            container.scan(profile=Profile.PRODUCTION)
            email = container.resolve(EmailPort)
        except AdapterNotFoundError as e:
            # Shows:
            # - Which port couldn't be resolved
            # - Active profile
            # - Available adapters for other profiles
            # - How to register an adapter for this profile
            print(e)

        try:
            service = container.resolve(UnregisteredService)
        except ServiceNotFoundError as e:
            # Shows:
            # - Which service couldn't be resolved
            # - Missing dependencies
            # - How to register the service
            print(e)

Best Practices:
    - **One container per application**: Create once at startup, reuse everywhere
    - **Use profiles**: Swap infrastructure, keep domain logic unchanged
    - **Global container for simplicity**: Import ``from dioxide import container``
    - **Separate containers for testing**: Isolated test containers per test
    - **Lifecycle for adapters**: Infrastructure resources need init/dispose
    - **Services rarely need lifecycle**: Core logic is usually stateless
    - **Async context manager**: ``async with container:`` handles lifecycle automatically

Thread Safety:
    The global ``container`` singleton (``from dioxide import container``) is thread-safe
    for most common usage patterns:

    **Why it's safe:**

    - **Module import guarantee**: Python's import system ensures modules are initialized
      exactly once, even when multiple threads import simultaneously. The GIL (Global
      Interpreter Lock) serializes module initialization, so ``container: Container = Container()``
      executes atomically.

    - **Singleton access**: Once initialized, accessing the global ``container`` variable
      is a simple attribute lookup, which is atomic under the GIL.

    - **Rust-backed resolution**: The underlying Rust container uses thread-safe data
      structures for provider registration and singleton caching.

    **Safe operations (no external synchronization needed):**

    - Importing: ``from dioxide import container``
    - Resolving singletons: ``container.resolve(MyService)``
    - Scanning at startup: ``container.scan(profile=Profile.PRODUCTION)``

    **Best practices for multi-threaded applications:**

    - Call ``container.scan()`` once during application startup, before spawning threads
    - Resolve services after scanning is complete
    - For per-thread isolation (e.g., request-scoped state), create separate Container
      instances or use ``container.create_scope()``

    **When to use separate containers:**

    - Multi-tenant applications requiring isolated dependency graphs
    - Testing scenarios requiring complete isolation
    - Per-request scoping in web frameworks (consider ``create_scope()`` first)

    Example (multi-threaded web application)::

        import threading
        from dioxide import container, Profile

        # Startup: scan once before threads start
        container.scan(profile=Profile.PRODUCTION)


        def handle_request():
            # Safe: resolving from already-scanned container
            service = container.resolve(UserService)
            return service.process()


        # Multiple threads can safely resolve from the same container
        threads = [threading.Thread(target=handle_request) for _ in range(10)]
        for t in threads:
            t.start()

See Also:
    - :class:`dioxide.adapter.adapter` - For marking infrastructure adapters
    - :class:`dioxide.services.service` - For marking core domain services
    - :class:`dioxide.lifecycle.lifecycle` - For initialization/cleanup
    - :class:`dioxide.profile_enum.Profile` - Standard profile enum values
    - :class:`dioxide.exceptions.AdapterNotFoundError` - Port resolution error
    - :class:`dioxide.exceptions.ServiceNotFoundError` - Service resolution error
"""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import time
from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    get_type_hints,
)

from dioxide._dioxide_core import Container as RustContainer
from dioxide.exceptions import (
    AdapterNotFoundError,
    CaptiveDependencyError,
    ScopeError,
    ServiceNotFoundError,
)
from dioxide.scan_stats import ScanStats
from dioxide.scope import Scope

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dioxide.profile_enum import Profile

T = TypeVar('T')


class Container:
    """Dependency injection container.

    The Container manages component registration and dependency resolution
    for your application. It supports both automatic discovery via the
    @component decorator and manual registration for fine-grained control.

    The container is backed by a high-performance Rust implementation that
    handles provider caching, singleton management, and type resolution.

    Features:
        - Type-safe dependency resolution with full IDE support
        - Automatic dependency injection based on type hints
        - SINGLETON and FACTORY lifecycle scopes
        - Thread-safe singleton caching (Rust-backed)
        - Automatic discovery via @component decorator
        - Manual registration for non-decorated classes

    Examples:
        Automatic discovery with @component:
            >>> from dioxide import Container, component
            >>>
            >>> @component
            ... class Database:
            ...     def query(self, sql):
            ...         return f'Executing: {sql}'
            >>>
            >>> @component
            ... class UserService:
            ...     def __init__(self, db: Database):
            ...         self.db = db
            >>>
            >>> container = Container()
            >>> container.scan()  # Auto-discover @component classes
            >>> service = container.resolve(UserService)
            >>> result = service.db.query('SELECT * FROM users')

        Manual registration:
            >>> from dioxide import Container
            >>>
            >>> class Config:
            ...     def __init__(self, env: str):
            ...         self.env = env
            >>>
            >>> container = Container()
            >>> container.register_singleton(Config, lambda: Config('production'))
            >>> config = container.resolve(Config)
            >>> assert config.env == 'production'

        Factory scope for per-request objects:
            >>> from dioxide import Container, component, Scope
            >>>
            >>> @component(scope=Scope.FACTORY)
            ... class RequestContext:
            ...     def __init__(self):
            ...         self.id = id(self)
            >>>
            >>> container = Container()
            >>> container.scan()
            >>> ctx1 = container.resolve(RequestContext)
            >>> ctx2 = container.resolve(RequestContext)
            >>> assert ctx1 is not ctx2  # Different instances

    Note:
        The container should be created once at application startup and
        reused throughout the application lifecycle. Each container maintains
        its own singleton cache and registration state.
    """

    def __init__(
        self,
        allowed_packages: list[str] | None = None,
        profile: Profile | str | None = None,
    ) -> None:
        """Initialize a new dependency injection container.

        Creates a new container with an empty registry. The container is
        ready to accept registrations via scan() for @component classes
        or via manual registration methods.

        If a profile is provided, the container automatically scans for
        components and adapters matching that profile during initialization.
        This enables the streamlined API pattern::

            async with Container(profile=Profile.PRODUCTION) as container:
                service = container.resolve(UserService)

        Instead of the more verbose::

            container = Container()
            container.scan(profile=Profile.PRODUCTION)
            async with container:
                service = container.resolve(UserService)

        Args:
            allowed_packages: Optional list of package prefixes allowed for scanning.
                If provided, only modules matching these prefixes can be imported.
                This prevents arbitrary code execution via package scanning.
                If None, no validation is performed (backward compatible).
                Example: ['myapp', 'tests.fixtures'] allows 'myapp.services'
                and 'tests.fixtures.mocks' but blocks 'os' or 'sys'.
            profile: Optional profile for auto-scanning. Accepts either a Profile
                enum value (Profile.PRODUCTION, Profile.TEST, etc.) or a string
                profile name. If provided, scan(profile=...) is called automatically
                during initialization. If None, no auto-scan is performed (default
                behavior for backward compatibility).

        Example:
            >>> from dioxide import Container
            >>> container = Container()
            >>> assert container.is_empty()

            Auto-scan with profile:
            >>> from dioxide import Container, Profile
            >>> container = Container(profile=Profile.PRODUCTION)
            >>> # Container is ready to resolve - no explicit scan() needed

            Security example:
            >>> # Only allow scanning within your application package
            >>> container = Container(allowed_packages=['myapp', 'tests'])
            >>> container.scan(package='myapp.services')  # OK
            >>> container.scan(package='os')  # Raises ValueError

            Combined example:
            >>> container = Container(allowed_packages=['myapp'], profile=Profile.PRODUCTION)
        """
        self._rust_core = RustContainer()
        self._active_profile: str | None = None  # Track active profile for error messages
        self._allowed_packages = allowed_packages  # Security: restrict scannable packages
        self._lifecycle_instances: list[Any] | None = None  # Cache lifecycle instances during start()
        self._multi_bindings: dict[type[Any], list[type[Any]]] = {}  # Port -> list of multi adapter classes

        # Auto-scan if profile is provided
        if profile is not None:
            self.scan(profile=profile)

    def register_instance(self, component_type: type[T], instance: T) -> None:
        """Register a pre-created instance for a given type.

        This method registers an already-instantiated object that will be
        returned whenever the type is resolved. Useful for registering
        configuration objects or external dependencies.

        Type safety is enforced at runtime: the instance must be an instance
        of component_type (or a subclass). For Protocol types, structural
        compatibility is checked.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            instance: The pre-created instance to return for this type. Must
                be an instance of component_type or a compatible type.

        Raises:
            TypeError: If the instance is not an instance of component_type.
            KeyError: If the type is already registered in this container.
                Each type can only be registered once.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class Config:
            ...     def __init__(self, debug: bool):
            ...         self.debug = debug
            >>>
            >>> container = Container()
            >>> config_instance = Config(debug=True)
            >>> container.register_instance(Config, config_instance)
            >>> resolved = container.resolve(Config)
            >>> assert resolved is config_instance
            >>> assert resolved.debug is True

        Type safety example:
            >>> container = Container()
            >>> container.register_instance(str, 42)  # Raises TypeError
            Traceback (most recent call last):
                ...
            TypeError: instance must be of type 'str', got 'int'
        """
        self._validate_instance_type(component_type, instance)
        self._rust_core.register_instance(component_type, instance)

    def _validate_instance_type(self, component_type: type[T], instance: T) -> None:
        """Validate that instance is compatible with component_type.

        Args:
            component_type: The expected type.
            instance: The instance to validate.

        Raises:
            TypeError: If instance is not compatible with component_type.
        """
        # Check for Protocol types
        if self._is_port(component_type):
            # For protocols, check structural compatibility
            if not self._implements_protocol(instance, component_type):
                instance_type_name = type(instance).__name__
                raise TypeError(f"instance must be of type '{component_type.__name__}', got '{instance_type_name}'")
        else:
            # For regular classes, use isinstance check
            if not isinstance(instance, component_type):
                instance_type_name = type(instance).__name__
                raise TypeError(f"instance must be of type '{component_type.__name__}', got '{instance_type_name}'")

    def _implements_protocol(self, instance: Any, protocol: type[Any]) -> bool:
        """Check if instance implements a Protocol.

        Args:
            instance: The instance to check.
            protocol: The Protocol type to check against.

        Returns:
            True if instance implements all methods defined by the protocol.
        """
        # Get all methods defined by the protocol (excluding dunder methods)
        protocol_methods = set()
        for name in dir(protocol):
            if name.startswith('_'):
                continue
            attr = getattr(protocol, name, None)
            if callable(attr):
                protocol_methods.add(name)

        # Check if instance has all required methods
        for method_name in protocol_methods:
            if not hasattr(instance, method_name):
                return False
            if not callable(getattr(instance, method_name)):
                return False

        return True

    def register_class(self, component_type: type[T], implementation: type[T]) -> None:
        """Register a class to instantiate for a given type.

        Registers a class that will be instantiated with no arguments when
        the type is resolved. The class's __init__ method will be called
        without parameters.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            implementation: The class to instantiate. Must have a no-argument
                __init__ method (or no __init__ at all).

        Raises:
            KeyError: If the type is already registered in this container.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class DatabaseConnection:
            ...     def __init__(self):
            ...         self.connected = True
            >>>
            >>> container = Container()
            >>> container.register_class(DatabaseConnection, DatabaseConnection)
            >>> db = container.resolve(DatabaseConnection)
            >>> assert db.connected is True

        Note:
            For classes requiring constructor arguments, use
            register_singleton_factory() or register_transient_factory()
            with a lambda that provides the arguments.
        """
        self._rust_core.register_class(component_type, implementation)

    def register_singleton_factory(self, component_type: type[T], factory: Callable[[], T]) -> None:
        """Register a singleton factory function for a given type.

        The factory will be called once when the type is first resolved,
        and the result will be cached. All subsequent resolve() calls for
        this type will return the same cached instance.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            factory: A callable that takes no arguments and returns an instance
                of component_type. Called exactly once, on first resolve().

        Raises:
            KeyError: If the type is already registered in this container.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class ExpensiveService:
            ...     def __init__(self, config_path: str):
            ...         self.config_path = config_path
            ...         self.initialized = True
            >>>
            >>> container = Container()
            >>> container.register_singleton_factory(ExpensiveService, lambda: ExpensiveService('/etc/config.yaml'))
            >>> service1 = container.resolve(ExpensiveService)
            >>> service2 = container.resolve(ExpensiveService)
            >>> assert service1 is service2  # Same instance

        Note:
            This is the recommended registration method for most services,
            as it provides lazy initialization and instance sharing.
        """
        self._rust_core.register_singleton_factory(component_type, factory)

    def register_transient_factory(self, component_type: type[T], factory: Callable[[], T]) -> None:
        """Register a transient factory function for a given type.

        The factory will be called every time the type is resolved, creating
        a new instance for each resolve() call. Use this for stateful objects
        that should not be shared.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            factory: A callable that takes no arguments and returns an instance
                of component_type. Called on every resolve() to create a fresh
                instance.

        Raises:
            KeyError: If the type is already registered in this container.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class RequestHandler:
            ...     _counter = 0
            ...
            ...     def __init__(self):
            ...         RequestHandler._counter += 1
            ...         self.request_id = RequestHandler._counter
            >>>
            >>> container = Container()
            >>> container.register_transient_factory(RequestHandler, lambda: RequestHandler())
            >>> handler1 = container.resolve(RequestHandler)
            >>> handler2 = container.resolve(RequestHandler)
            >>> assert handler1 is not handler2  # Different instances
            >>> assert handler1.request_id != handler2.request_id

        Note:
            Use this for objects with per-request or per-operation lifecycle.
            For shared services, use register_singleton_factory() instead.
        """
        self._rust_core.register_transient_factory(component_type, factory)

    def register_singleton(self, component_type: type[T], factory: Callable[[], T]) -> None:
        """Register a singleton provider manually.

        Convenience method that calls register_singleton_factory(). The factory
        will be called once when the type is first resolved, and the result
        will be cached for the lifetime of the container.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            factory: A callable that takes no arguments and returns an instance
                of component_type. Called exactly once, on first resolve().

        Raises:
            KeyError: If the type is already registered in this container.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class Config:
            ...     def __init__(self, db_url: str):
            ...         self.db_url = db_url
            >>>
            >>> container = Container()
            >>> container.register_singleton(Config, lambda: Config('postgresql://localhost'))
            >>> config = container.resolve(Config)
            >>> assert config.db_url == 'postgresql://localhost'

        Note:
            This is an alias for register_singleton_factory() provided for
            convenience and clarity.
        """
        self.register_singleton_factory(component_type, factory)

    def register_factory(self, component_type: type[T], factory: Callable[[], T]) -> None:
        """Register a transient (factory) provider manually.

        Convenience method that calls register_transient_factory(). The factory
        will be called every time the type is resolved, creating a new instance
        for each resolve() call.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            factory: A callable that takes no arguments and returns an instance
                of component_type. Called on every resolve() to create a fresh
                instance.

        Raises:
            KeyError: If the type is already registered in this container.

        Example:
            >>> from dioxide import Container
            >>>
            >>> class Transaction:
            ...     _id_counter = 0
            ...
            ...     def __init__(self):
            ...         Transaction._id_counter += 1
            ...         self.tx_id = Transaction._id_counter
            >>>
            >>> container = Container()
            >>> container.register_factory(Transaction, lambda: Transaction())
            >>> tx1 = container.resolve(Transaction)
            >>> tx2 = container.resolve(Transaction)
            >>> assert tx1.tx_id != tx2.tx_id  # Different instances

        Note:
            This is an alias for register_transient_factory() provided for
            convenience and clarity.
        """
        self.register_transient_factory(component_type, factory)

    def resolve(self, component_type: type[T]) -> T:
        """Resolve a component instance.

        Retrieves or creates an instance of the requested type based on its
        registration. For singletons, returns the cached instance (creating
        it on first call). For factories, creates a new instance every time.

        For multi-bindings, use ``list[Port]`` type hint to resolve all
        adapters registered with ``multi=True`` for that port.

        Args:
            component_type: The type to resolve. Must have been previously
                registered via scan() or manual registration methods.
                Can be a ``list[Port]`` type to resolve multi-bindings.

        Returns:
            An instance of the requested type. For SINGLETON scope, the same
            instance is returned on every call. For FACTORY scope, a new
            instance is created on each call. For ``list[Port]``, returns
            a list of all multi-binding adapters for that port.

        Raises:
            AdapterNotFoundError: If the type is a port (Protocol/ABC) and no
                adapter is registered for the current profile.
            ServiceNotFoundError: If the type is a service/component that cannot
                be resolved (not registered or has unresolvable dependencies).
            ScopeError: If trying to resolve a REQUEST-scoped component outside
                of a scope context. Use ``container.create_scope()`` to create
                a scope.

        Example:
            >>> from dioxide import Container, component
            >>>
            >>> @component
            ... class Logger:
            ...     def log(self, msg: str):
            ...         print(f'LOG: {msg}')
            >>>
            >>> @component
            ... class Application:
            ...     def __init__(self, logger: Logger):
            ...         self.logger = logger
            >>>
            >>> container = Container()
            >>> container.scan()
            >>> app = container.resolve(Application)
            >>> app.logger.log('Application started')

        Note:
            Type annotations in constructors enable automatic dependency
            injection. The container recursively resolves all dependencies.
        """
        # Check if this is a list[Port] type hint for multi-bindings
        multi_binding_result = self._resolve_multi_binding(component_type)
        if multi_binding_result is not None:
            return multi_binding_result  # type: ignore[return-value]

        # Check if this is a REQUEST-scoped component being resolved outside a scope
        scope = self._get_component_scope(component_type)
        if scope is not None:
            from dioxide.scope import Scope

            if scope == Scope.REQUEST:
                component_name = component_type.__name__
                raise ScopeError(f'Cannot resolve {component_name}: REQUEST-scoped, requires active scope')

        try:
            return self._rust_core.resolve(component_type)
        except KeyError as e:
            # Determine if this is a port (Protocol/ABC) or a service/component
            is_port = self._is_port(component_type)

            if is_port:
                # Build helpful error message for missing adapter
                error_msg = self._build_adapter_not_found_message(component_type)
                raise AdapterNotFoundError(error_msg) from e
            else:
                # Build helpful error message for missing service/component
                error_msg = self._build_service_not_found_message(component_type)
                raise ServiceNotFoundError(error_msg) from e

    def _resolve_multi_binding(self, component_type: Any) -> list[Any] | None:
        """Check if component_type is list[Port] and resolve multi-bindings.

        Args:
            component_type: The type to check. May be a generic alias like list[Port].

        Returns:
            List of adapter instances if this is a multi-binding resolution,
            None if not a list[Port] type hint.
        """
        import typing

        # Check if this is a generic alias (e.g., list[SomePort])
        origin = typing.get_origin(component_type)
        if origin is not list:
            return None

        # Get the type argument (the Port type)
        args = typing.get_args(component_type)
        if not args:
            return None

        port_type = args[0]

        # Check if we have multi-bindings for this port
        adapter_classes = self._multi_bindings.get(port_type)
        if adapter_classes is None:
            # Return empty list for multi-bindings with no implementations
            # (this is valid - it allows optional plugins)
            return []

        # Instantiate all adapters with dependency injection
        instances = []
        for adapter_class in adapter_classes:
            factory = self._create_auto_injecting_factory(adapter_class)
            instances.append(factory())

        return instances

    def _is_port(self, cls: type[Any]) -> bool:
        """Check if a type is a port (Protocol or ABC).

        Args:
            cls: The type to check.

        Returns:
            True if the type is a Protocol or ABC, False otherwise.
        """
        # Check if it's a Protocol
        if hasattr(cls, '_is_protocol') and cls._is_protocol:
            return True

        # Check if it's a subclass of Protocol (via __mro__)
        if hasattr(cls, '__mro__'):
            for base in cls.__mro__:
                if getattr(base, '__name__', None) == 'Protocol':
                    return True

        # Check if it's an ABC
        try:
            from abc import ABC

            if issubclass(cls, ABC):
                return True
        except TypeError:
            pass

        return False

    def _get_component_scope(self, component_type: type[Any]) -> Scope | None:
        """Get the scope for a component type.

        Args:
            component_type: The type to check.

        Returns:
            The Scope enum value for this component, or None if not found.
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry

        # Check if it's a registered component (service)
        for component_class in _get_registered_components():
            if component_class is component_type:
                return getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

        # Check if it's a port - look up the adapter for the port
        for adapter_class in _adapter_registry:
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is component_type:
                # Check if adapter matches active profile
                adapter_profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())
                if self._active_profile in adapter_profiles or '*' in adapter_profiles:
                    return getattr(adapter_class, '__dioxide_scope__', Scope.SINGLETON)

        return None

    def _check_captive_dependencies(self, port_to_adapters: dict[type[Any], list[type[Any]]]) -> None:
        """Check for captive dependencies (SINGLETON depends on REQUEST).

        A captive dependency occurs when a SINGLETON-scoped component depends
        on a REQUEST-scoped component. This is invalid because the REQUEST
        instance would be "captured" by the SINGLETON and never refreshed.

        Args:
            port_to_adapters: Map of port types to adapter classes for the current profile.

        Raises:
            CaptiveDependencyError: If a SINGLETON depends on a REQUEST-scoped component.
        """
        from dioxide._registry import _get_registered_components
        from dioxide.scope import Scope

        # Build a map of type -> scope for quick lookup
        type_to_scope: dict[type[Any], Scope] = {}

        # Add adapters (use port type as key since that's what services depend on)
        for port_class, adapters in port_to_adapters.items():
            if adapters:
                adapter_class = adapters[0]
                scope = getattr(adapter_class, '__dioxide_scope__', Scope.SINGLETON)
                type_to_scope[port_class] = scope

        # Add services/components
        for component_class in _get_registered_components():
            # Check profile filtering
            component_profiles: frozenset[str] = getattr(component_class, '__dioxide_profiles__', frozenset())
            if self._active_profile is not None:
                if self._active_profile not in component_profiles and '*' not in component_profiles:
                    continue
            scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)
            type_to_scope[component_class] = scope

        # Check each component's dependencies for captive dependency violations
        all_components = list(_get_registered_components())

        for component_class in all_components:
            # Check profile filtering
            component_profiles = getattr(component_class, '__dioxide_profiles__', frozenset())
            if self._active_profile is not None:
                if self._active_profile not in component_profiles and '*' not in component_profiles:
                    continue

            component_scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

            # Only check SINGLETON components (they can't depend on REQUEST)
            if component_scope != Scope.SINGLETON:
                continue

            # Get constructor dependencies
            try:
                init_signature = inspect.signature(component_class.__init__)
                globalns = getattr(component_class.__init__, '__globals__', {})
                localns = dict(vars(component_class))
                localns[component_class.__name__] = component_class

                # Handle local classes in tests
                if '<locals>' in component_class.__qualname__:
                    try:
                        import sys
                        from types import FrameType

                        frame: FrameType | None = sys._getframe()
                        while frame is not None:
                            frame_locals = frame.f_locals
                            for name, obj in frame_locals.items():
                                if inspect.isclass(obj):
                                    localns[name] = obj
                            frame = frame.f_back
                    except (AttributeError, ValueError):
                        pass

                type_hints = get_type_hints(component_class.__init__, globalns=globalns, localns=localns)
            except (ValueError, AttributeError, NameError):
                continue

            # Check each dependency
            for param_name in init_signature.parameters:
                if param_name == 'self':
                    continue
                if param_name not in type_hints:
                    continue

                dep_type = type_hints[param_name]
                dep_scope = type_to_scope.get(dep_type)

                # If dependency is REQUEST-scoped, we have a captive dependency
                if dep_scope == Scope.REQUEST:
                    raise CaptiveDependencyError(
                        f'Captive dependency: {component_class.__name__} (SINGLETON) -> {dep_type.__name__} (REQUEST)\n'
                        f'  SINGLETON cannot depend on REQUEST-scoped components'
                    )

    def _build_adapter_not_found_message(self, port_type: type[Any]) -> str:
        """Build terse error message for missing adapter.

        Args:
            port_type: The port type that couldn't be resolved.

        Returns:
            A terse error message (1-3 lines) with key diagnostic info.
        """
        from dioxide.adapter import _adapter_registry

        port_name = port_type.__name__
        profile_str = self._active_profile if self._active_profile else 'none'

        # Find all adapters for this port (across all profiles)
        adapters_for_port = []
        for adapter_class in _adapter_registry:
            if hasattr(adapter_class, '__dioxide_port__'):
                if adapter_class.__dioxide_port__ is port_type:
                    adapter_name = adapter_class.__name__
                    profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())
                    profile_list = ', '.join(sorted(profiles)) if profiles else 'none'
                    adapters_for_port.append(f'{adapter_name} ({profile_list})')

        # Build terse message: 1-3 lines max
        lines = [f"No adapter for {port_name} in profile '{profile_str}'"]
        if adapters_for_port:
            lines.append(f'  Registered: {", ".join(adapters_for_port)}')
        else:
            lines.append('  Registered: none')

        return '\n'.join(lines)

    def _build_service_not_found_message(self, service_type: type[Any]) -> str:
        """Build terse error message for missing service/component.

        Args:
            service_type: The service type that couldn't be resolved.

        Returns:
            A terse error message (1-3 lines) with key diagnostic info.
        """
        service_name = service_type.__name__
        profile_str = self._active_profile if self._active_profile else 'none'

        # Check if it's decorated with @service or @component
        from dioxide._registry import _get_registered_components

        registered_components = list(_get_registered_components())
        is_registered = service_type in registered_components

        # Build terse message: 1-3 lines max
        lines = [f"Cannot resolve {service_name} in profile '{profile_str}'"]

        if is_registered:
            # Service is registered but has unresolvable dependency
            try:
                init_signature = inspect.signature(service_type.__init__)
                type_hints = get_type_hints(service_type.__init__, globalns=service_type.__init__.__globals__)
                dependencies = [
                    type_hints[param_name].__name__
                    for param_name in init_signature.parameters
                    if param_name != 'self' and param_name in type_hints
                ]

                if dependencies:
                    lines.append(f'  Missing dependency: {", ".join(dependencies)}')
            except (ValueError, AttributeError, NameError):
                lines.append('  Missing dependency: unknown')
        else:
            lines.append('  Not registered (missing @service decorator)')

        return '\n'.join(lines)

    def __getitem__(self, component_type: type[T]) -> T:
        """Resolve a component using bracket syntax.

        Provides an alternative, more Pythonic syntax for resolving components.
        This method is equivalent to calling resolve() and simply delegates to it.

        Args:
            component_type: The type to resolve. Must have been previously
                registered via scan() or manual registration methods.

        Returns:
            An instance of the requested type. For SINGLETON scope, the same
            instance is returned on every call. For FACTORY scope, a new
            instance is created on each call.

        Raises:
            KeyError: If the type is not registered in this container.

        Example:
            >>> from dioxide import container, component
            >>>
            >>> @component
            ... class Logger:
            ...     def log(self, msg: str):
            ...         print(f'LOG: {msg}')
            >>>
            >>> container.scan()
            >>> logger = container[Logger]  # Bracket syntax
            >>> logger.log('Using bracket notation')

        Note:
            This is purely a convenience method. Both container[Type] and
            container.resolve(Type) work identically and return the same
            instance for singleton-scoped components.
        """
        return self.resolve(component_type)

    def is_empty(self) -> bool:
        """Check if container has no registered providers.

        Returns:
            True if no types have been registered, False if at least one
            type has been registered.

        Example:
            >>> from dioxide import Container
            >>>
            >>> container = Container()
            >>> assert container.is_empty()
            >>>
            >>> container.scan()  # Register @component classes
            >>> # If any @component classes exist, container is no longer empty
        """
        return self._rust_core.is_empty()

    def __len__(self) -> int:
        """Get count of registered providers.

        Returns:
            The number of types that have been registered in this container.

        Example:
            >>> from dioxide import Container, component
            >>>
            >>> @component
            ... class ServiceA:
            ...     pass
            >>>
            >>> @component
            ... class ServiceB:
            ...     pass
            >>>
            >>> container = Container()
            >>> assert len(container) == 0
            >>> container.scan()
            >>> assert len(container) == 2
        """
        return len(self._rust_core)

    def __repr__(self) -> str:
        """Return an informative string representation for debugging.

        Shows the active profile, port count, and service count so agents
        and developers can inspect container state in a REPL or debugger.

        Returns:
            A string like ``Container(profile=Profile('production'), ports=5, services=3)``
            or ``Container(profile=None, ports=0, services=0)`` when no profile is set.

        Example:
            >>> from dioxide import Container, Profile
            >>> container = Container(profile=Profile.PRODUCTION)
            >>> repr(container)
            "Container(profile=Profile('production'), ports=..., services=...)"
        """
        profile = self.active_profile
        profile_str = repr(profile) if profile is not None else 'None'

        registered_types = self.list_registered()
        port_count = sum(1 for t in registered_types if self._is_port(t))
        service_count = len(registered_types) - port_count

        return f'Container(profile={profile_str}, ports={port_count}, services={service_count})'

    # =========================================================================
    # Introspection API (for debugging)
    # =========================================================================

    def list_registered(self) -> list[type[Any]]:
        """List all types registered in this container.

        Returns a list of all type objects (classes, protocols, ABCs) that have
        been registered with this container, either through scan() or manual
        registration methods.

        This is useful for debugging registration issues - when you get a
        "not registered" error, call this method to see what IS registered.

        Returns:
            List of type objects registered in this container. The list order
            is not guaranteed to be consistent between calls.

        Example:
            >>> from dioxide import Container, Profile, adapter, service
            >>>
            >>> class EmailPort(Protocol):
            ...     async def send(self, to: str) -> None: ...
            >>>
            >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            ... class SendGridAdapter:
            ...     async def send(self, to: str) -> None:
            ...         pass
            >>>
            >>> @service
            ... class UserService:
            ...     pass
            >>>
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> registered = container.list_registered()
            >>> # registered contains [EmailPort, UserService]

        See Also:
            - :meth:`is_registered` - Check if a specific type is registered
            - :meth:`get_adapters_for` - Get adapter details for a port
        """
        return list(self._rust_core.get_registered_types())

    def is_registered(self, port_or_service: type[Any]) -> bool:
        """Check if a type is registered in this container.

        Useful for verifying that a type has been registered before attempting
        to resolve it, or for test assertions about container configuration.

        Args:
            port_or_service: The type to check. Can be a port (Protocol/ABC)
                or a service class.

        Returns:
            True if the type is registered, False otherwise.

        Example:
            >>> from dioxide import Container, Profile, adapter
            >>>
            >>> class EmailPort(Protocol):
            ...     async def send(self, to: str) -> None: ...
            >>>
            >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            ... class SendGridAdapter:
            ...     async def send(self, to: str) -> None:
            ...         pass
            >>>
            >>> container = Container()
            >>> assert container.is_registered(EmailPort) is False
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> assert container.is_registered(EmailPort) is True

        See Also:
            - :meth:`list_registered` - Get all registered types
            - :meth:`resolve` - Actually resolve a registered type
        """
        return self._rust_core.contains(port_or_service)

    @property
    def active_profile(self) -> Profile | None:
        """Get the profile this container was scanned with.

        Returns the Profile value used when scan() was called, or None if
        scan() hasn't been called yet. This is useful for debugging to verify
        which profile is active.

        Returns:
            The Profile value if scan() was called with a profile,
            None if scan() hasn't been called or was called without a profile.

        Example:
            >>> from dioxide import Container, Profile
            >>>
            >>> container = Container()
            >>> assert container.active_profile is None
            >>>
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> assert container.active_profile == Profile.PRODUCTION
            >>>
            >>> # Or with constructor profile:
            >>> container2 = Container(profile=Profile.TEST)
            >>> assert container2.active_profile == Profile.TEST

        See Also:
            - :meth:`scan` - Set the active profile during scanning
            - :class:`dioxide.Profile` - Extensible profile identifiers
        """
        from dioxide.profile_enum import Profile

        if self._active_profile is None:
            return None
        # Convert stored string back to Profile instance
        # Profile is a str subclass, so any string is valid
        return Profile(self._active_profile)

    def get_adapters_for(self, port: type[Any]) -> dict[Profile, type[Any]]:
        """Get all adapters registered for a port across all profiles.

        Inspects the global adapter registry to find all adapters that implement
        the specified port, organized by profile. This is useful for debugging
        to see which adapters are available for a port in different profiles.

        Note: This method looks at the global adapter registry, not just what's
        registered in this container instance. This allows you to see all
        available adapters even if the container was scanned with a different
        profile.

        Args:
            port: The port type (Protocol/ABC) to find adapters for.

        Returns:
            Dictionary mapping Profile enum values to adapter classes.
            Returns an empty dict if no adapters are registered for the port.

        Example:
            >>> from dioxide import Container, Profile, adapter
            >>>
            >>> class EmailPort(Protocol):
            ...     async def send(self, to: str) -> None: ...
            >>>
            >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
            ... class SendGridAdapter:
            ...     async def send(self, to: str) -> None:
            ...         pass
            >>>
            >>> @adapter.for_(EmailPort, profile=Profile.TEST)
            ... class FakeEmailAdapter:
            ...     async def send(self, to: str) -> None:
            ...         pass
            >>>
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> adapters = container.get_adapters_for(EmailPort)
            >>> # adapters = {
            >>> #     Profile.PRODUCTION: SendGridAdapter,
            >>> #     Profile.TEST: FakeEmailAdapter,
            >>> # }

        See Also:
            - :meth:`is_registered` - Check if a port has an adapter
            - :func:`adapter.for_` - Register adapters for ports
        """
        from dioxide.adapter import _adapter_registry
        from dioxide.profile_enum import Profile

        result: dict[Profile, type[Any]] = {}

        for adapter_class in _adapter_registry:
            adapter_port = getattr(adapter_class, '__dioxide_port__', None)
            if adapter_port is not port:
                continue

            # Get profiles for this adapter
            profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())

            for profile_str in profiles:
                try:
                    profile_enum = Profile(profile_str)
                    result[profile_enum] = adapter_class
                except ValueError:
                    # Custom profile string - skip it in the result
                    # (can't convert to Profile enum)
                    pass

        return result

    def debug(self, file: Any = None) -> str:
        """Print a summary of all registered components.

        Shows services, adapters (grouped by port), and active profile.
        Useful for verifying what's actually registered in the container.

        Args:
            file: Optional file-like object to write to (default: returns string).
                If provided, also writes the output to the file.

        Returns:
            Formatted debug string with container summary.

        Example:
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> print(container.debug())
            === dioxide Container Debug ===
            Active Profile: production

            Services (2):
              - UserService (SINGLETON)
              - NotificationService (SINGLETON)

            Adapters by Port:
              EmailPort:
                - SendGridAdapter (profiles: production)
              DatabasePort:
                - PostgresAdapter (profiles: production, lifecycle)
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry
        from dioxide.scope import Scope

        lines: list[str] = []
        lines.append('=== dioxide Container Debug ===')

        profile_str = self._active_profile if self._active_profile else 'none'
        lines.append(f'Active Profile: {profile_str}')
        lines.append('')

        services: list[tuple[str, str, bool]] = []
        for component_class in _get_registered_components():
            component_profiles: frozenset[str] = getattr(component_class, '__dioxide_profiles__', frozenset())
            if not self._matches_active_profile(component_profiles):
                continue

            name = component_class.__name__
            scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)
            scope_str = scope.name if hasattr(scope, 'name') else str(scope).upper()
            has_lifecycle = hasattr(component_class, '_dioxide_lifecycle')
            services.append((name, scope_str, has_lifecycle))

        # Sort services by name for consistent output
        services.sort(key=lambda x: x[0])

        if services:
            lines.append(f'Services ({len(services)}):')
            for name, scope_str, has_lifecycle in services:
                lifecycle_indicator = ', lifecycle' if has_lifecycle else ''
                lines.append(f'  - {name} ({scope_str}{lifecycle_indicator})')
            lines.append('')

        # Collect adapters grouped by port
        # Maps: port_name -> [(adapter_name, profiles_str, has_lifecycle)]
        port_adapters: dict[str, list[tuple[str, str, bool]]] = {}

        for adapter_class in _adapter_registry:
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is None:
                continue

            # Get adapter's profiles
            adapter_profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())

            port_name = port_class.__name__
            adapter_name = adapter_class.__name__
            profiles_str = ', '.join(sorted(adapter_profiles)) if adapter_profiles else 'none'
            has_lifecycle = hasattr(adapter_class, '_dioxide_lifecycle')

            if port_name not in port_adapters:
                port_adapters[port_name] = []
            port_adapters[port_name].append((adapter_name, profiles_str, has_lifecycle))

        if port_adapters:
            lines.append('Adapters by Port:')
            for port_name in sorted(port_adapters.keys()):
                lines.append(f'  {port_name}:')
                for adapter_name, profiles_str, has_lifecycle in sorted(port_adapters[port_name]):
                    lifecycle_indicator = ', lifecycle' if has_lifecycle else ''
                    lines.append(f'    - {adapter_name} (profiles: {profiles_str}{lifecycle_indicator})')

        output = '\n'.join(lines)

        # Write to file if provided
        if file is not None:
            file.write(output)

        return output

    def explain(self, cls: type[Any]) -> str:
        """Explain how a type would be resolved.

        Shows the resolution path, which adapter/service is selected,
        and all transitive dependencies in a tree format.

        Args:
            cls: The type to explain resolution for. Can be a service,
                port (Protocol/ABC), or any registered type.

        Returns:
            Formatted string showing the resolution tree.

        Example:
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> print(container.explain(UserService))
            === Resolution: UserService ===

            UserService (SINGLETON)
            +-- db: DatabasePort
            |   +-- PostgresAdapter (profile: production)
            |       +-- config: AppConfig
            +-- email: EmailPort
                +-- SendGridAdapter (profile: production)
                    +-- config: AppConfig
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry

        lines: list[str] = []
        cls_name = cls.__name__

        # Check if type is registered
        is_registered = self.is_registered(cls)
        if not is_registered:
            # Check if it's in the global registries but not in this container
            is_in_component_registry = cls in _get_registered_components()
            is_port_with_adapter = any(getattr(a, '__dioxide_port__', None) is cls for a in _adapter_registry)

            if not is_in_component_registry and not is_port_with_adapter:
                return f'=== Resolution: {cls_name} ===\n\n{cls_name} is not registered.'

        lines.append(f'=== Resolution: {cls_name} ===')
        lines.append('')

        # Build the resolution tree
        self._explain_type(cls, lines, prefix='', is_last=True, visited=set())

        return '\n'.join(lines)

    def _explain_type(
        self,
        cls: type[Any],
        lines: list[str],
        prefix: str,
        is_last: bool,
        visited: set[type[Any]],
    ) -> None:
        """Helper to recursively build the resolution tree.

        Args:
            cls: The type to explain.
            lines: List of lines to append to.
            prefix: Current indentation prefix.
            is_last: Whether this is the last sibling.
            visited: Set of already-visited types to detect cycles.
        """
        from dioxide.adapter import _adapter_registry
        from dioxide.scope import Scope

        cls_name = cls.__name__

        # Detect cycles
        if cls in visited:
            lines.append(f'{prefix}{cls_name} (circular reference)')
            return
        visited = visited | {cls}

        # Determine what kind of type this is
        is_port = self._is_port(cls)

        if is_port:
            adapter_class = None
            adapter_profiles_str = ''
            for adapter_cls in _adapter_registry:
                if getattr(adapter_cls, '__dioxide_port__', None) is cls:
                    adapter_profiles: frozenset[str] = getattr(adapter_cls, '__dioxide_profiles__', frozenset())
                    if self._matches_active_profile(adapter_profiles):
                        adapter_class = adapter_cls
                        adapter_profiles_str = ', '.join(sorted(adapter_profiles))
                        break

            if adapter_class:
                scope = getattr(adapter_class, '__dioxide_scope__', Scope.SINGLETON)
                scope_str = scope.name if hasattr(scope, 'name') else str(scope).upper()
                lines.append(f'{prefix}{cls_name}')
                # Show the implementing adapter
                new_prefix = prefix + ('    ' if is_last else '|   ')
                lines.append(f'{new_prefix}+-- {adapter_class.__name__} ({scope_str}, profile: {adapter_profiles_str})')

                # Get adapter's dependencies
                self._add_dependencies(adapter_class, lines, new_prefix + '    ', visited)
            else:
                lines.append(f'{prefix}{cls_name} (no adapter for profile: {self._active_profile})')
        else:
            # It's a service or component
            scope = getattr(cls, '__dioxide_scope__', Scope.SINGLETON)
            scope_str = scope.name if hasattr(scope, 'name') else str(scope).upper()
            lines.append(f'{prefix}{cls_name} ({scope_str})')

            # Get service's dependencies
            new_prefix = prefix + ('    ' if is_last else '|   ')
            self._add_dependencies(cls, lines, new_prefix, visited)

    def _add_dependencies(
        self,
        cls: type[Any],
        lines: list[str],
        prefix: str,
        visited: set[type[Any]],
    ) -> None:
        """Add dependencies of a class to the resolution tree.

        Args:
            cls: The class to get dependencies for.
            lines: List of lines to append to.
            prefix: Current indentation prefix.
            visited: Set of already-visited types.
        """
        try:
            init_signature = inspect.signature(cls.__init__)
            globalns = getattr(cls.__init__, '__globals__', {})
            localns = dict(vars(cls))
            localns[cls.__name__] = cls

            type_hints = get_type_hints(cls.__init__, globalns=globalns, localns=localns)

            deps = []
            for param_name in init_signature.parameters:
                if param_name == 'self':
                    continue
                if param_name in type_hints:
                    deps.append((param_name, type_hints[param_name]))

            for i, (param_name, dep_type) in enumerate(deps):
                is_last = i == len(deps) - 1
                connector = '+-- '
                lines.append(f'{prefix}{connector}{param_name}: {dep_type.__name__}')

                # Recursively explain this dependency
                child_prefix = prefix + ('    ' if is_last else '|   ')
                self._explain_type(dep_type, lines, child_prefix, is_last, visited)

        except (ValueError, AttributeError, NameError):
            pass

    def graph(self, format: str = 'mermaid') -> str:
        """Generate a dependency graph visualization.

        Creates a visual representation of the dependency graph that can be
        rendered with Mermaid (default) or Graphviz DOT format.

        Args:
            format: Output format, either 'mermaid' (default) or 'dot'.

        Returns:
            String containing the graph in the requested format.

        Example:
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> print(container.graph())
            graph TD
                subgraph Services
                    UserService[UserService<br/>SINGLETON]
                end

                subgraph Ports
                    EmailPort{{EmailPort}}
                end

                subgraph Adapters
                    SendGridAdapter[SendGridAdapter<br/>production]
                end

                UserService --> EmailPort
                EmailPort -.-> SendGridAdapter
        """
        if format == 'dot':
            return self._graph_dot()
        return self._graph_mermaid()

    def _matches_active_profile(self, profiles: frozenset[str]) -> bool:
        """Check if a component's profiles match the active profile.

        Args:
            profiles: The component's registered profiles.

        Returns:
            True if the component should be included for the active profile.
        """
        if self._active_profile is None:
            return True
        return self._active_profile in profiles or '*' in profiles

    def _collect_graph_data(
        self,
    ) -> tuple[
        list[tuple[str, str]],  # services: (name, scope)
        set[str],  # ports
        list[tuple[str, str, str]],  # adapters: (name, port_name, profiles)
        list[tuple[str, str]],  # edges: (from, to)
    ]:
        """Collect component data for graph generation.

        Returns:
            Tuple of (services, ports, adapters, edges).
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry
        from dioxide.scope import Scope

        services: list[tuple[str, str]] = []
        for component_class in _get_registered_components():
            component_profiles: frozenset[str] = getattr(component_class, '__dioxide_profiles__', frozenset())
            if not self._matches_active_profile(component_profiles):
                continue
            name = component_class.__name__
            scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)
            scope_str = scope.name if hasattr(scope, 'name') else str(scope).upper()
            services.append((name, scope_str))

        ports: set[str] = set()
        adapters: list[tuple[str, str, str]] = []
        for adapter_class in _adapter_registry:
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is None:
                continue
            adapter_profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())
            if not self._matches_active_profile(adapter_profiles):
                continue
            port_name = port_class.__name__
            adapter_name = adapter_class.__name__
            profiles_str = ', '.join(sorted(adapter_profiles))
            ports.add(port_name)
            adapters.append((adapter_name, port_name, profiles_str))

        edges: list[tuple[str, str]] = []
        service_names = {s[0] for s in services}
        for component_class in _get_registered_components():
            component_profiles = getattr(component_class, '__dioxide_profiles__', frozenset())
            if not self._matches_active_profile(component_profiles):
                continue
            try:
                init_signature = inspect.signature(component_class.__init__)
                globalns = getattr(component_class.__init__, '__globals__', {})
                localns = dict(vars(component_class))
                localns[component_class.__name__] = component_class
                type_hints = get_type_hints(component_class.__init__, globalns=globalns, localns=localns)
                for param_name in init_signature.parameters:
                    if param_name == 'self':
                        continue
                    if param_name in type_hints:
                        dep_type = type_hints[param_name]
                        dep_name = dep_type.__name__
                        if dep_name in ports or dep_name in service_names:
                            edges.append((component_class.__name__, dep_name))
            except (ValueError, AttributeError, NameError):
                pass

        return services, ports, adapters, edges

    def _graph_mermaid(self) -> str:
        """Generate Mermaid format dependency graph.

        Returns:
            Mermaid graph definition string.
        """
        services, ports, adapters, edges = self._collect_graph_data()

        lines: list[str] = ['graph TD']

        if services:
            lines.append('    subgraph Services')
            for name, scope_str in sorted(services):
                lines.append(f'        {name}["{name}<br/>{scope_str}"]')
            lines.append('    end')
            lines.append('')

        if ports:
            lines.append('    subgraph Ports')
            for port_name in sorted(ports):
                lines.append(f'        {port_name}{{{{{port_name}}}}}')
            lines.append('    end')
            lines.append('')

        if adapters:
            lines.append('    subgraph Adapters')
            for adapter_name, _port_name, profiles_str in sorted(adapters):
                lines.append(f'        {adapter_name}["{adapter_name}<br/>{profiles_str}"]')
            lines.append('    end')
            lines.append('')

        for from_node, to_node in edges:
            lines.append(f'    {from_node} --> {to_node}')

        for adapter_name, port_name, _ in adapters:
            lines.append(f'    {port_name} -.-> {adapter_name}')

        return '\n'.join(lines)

    def _graph_dot(self) -> str:
        """Generate Graphviz DOT format dependency graph.

        Returns:
            DOT graph definition string.
        """
        services, ports, adapters, edges = self._collect_graph_data()

        lines: list[str] = ['digraph Container {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box];')
        lines.append('')

        if services:
            lines.append('    subgraph cluster_services {')
            lines.append('        label="Services";')
            for name, scope_str in sorted(services):
                lines.append(f'        {name} [label="{name}\\n{scope_str}"];')
            lines.append('    }')
            lines.append('')

        if ports:
            lines.append('    subgraph cluster_ports {')
            lines.append('        label="Ports";')
            lines.append('        node [shape=diamond];')
            for port_name in sorted(ports):
                lines.append(f'        {port_name};')
            lines.append('    }')
            lines.append('')

        if adapters:
            lines.append('    subgraph cluster_adapters {')
            lines.append('        label="Adapters";')
            for adapter_name, _port_name, profiles_str in sorted(adapters):
                lines.append(f'        {adapter_name} [label="{adapter_name}\\n{profiles_str}"];')
            lines.append('    }')
            lines.append('')

        for from_node, to_node in edges:
            lines.append(f'    {from_node} -> {to_node};')

        for adapter_name, port_name, _ in adapters:
            lines.append(f'    {port_name} -> {adapter_name} [style=dashed];')

        lines.append('}')
        return '\n'.join(lines)

    def _import_package(self, package_name: str) -> int:
        """Import all modules in a package to trigger decorator execution.

        Recursively walks through the package and all sub-packages, importing
        each module to ensure all @component and @adapter decorators are executed
        and the classes are registered in the global registries.

        Args:
            package_name: The fully-qualified package name to import (e.g. "app.services").

        Raises:
            ImportError: If the package name is invalid or cannot be imported.
            ValueError: If package_name is not in allowed_packages list (if configured).

        Example:
            >>> container._import_package('app.services')
            # All modules in app.services and its sub-packages are now imported

        Note:
            This is an internal method used by scan() to support package-based
            scanning. It should not be called directly by users.
        """
        import logging

        # Security: Validate package is in allowed list (if configured)
        if self._allowed_packages is not None:
            if not any(package_name.startswith(prefix) for prefix in self._allowed_packages):
                msg = (
                    f"Package '{package_name}' is not in allowed_packages list. "
                    f'Allowed prefixes: {self._allowed_packages}'
                )
                raise ValueError(msg)

        try:
            # Import the package itself
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as e:
            raise ImportError(f"Package '{package_name}' not found") from e

        # If the package doesn't have a __path__, it's a module not a package
        # Just importing it above was sufficient
        if not hasattr(package, '__path__'):
            return 1

        # Walk all modules in the package (including sub-packages)
        count = 1  # Count the package itself
        for _importer, modname, _ispkg in pkgutil.walk_packages(
            path=package.__path__,
            prefix=package.__name__ + '.',
            onerror=lambda x: None,  # Silently skip modules that fail to import
        ):
            try:
                importlib.import_module(modname)
                count += 1
            except Exception as e:
                # Log import failures for debugging
                logging.warning(f'Failed to import module {modname}: {e}')
                # Skip modules that fail to import (missing dependencies, etc.)
                pass

        return count

    def scan(
        self,
        package: str | None = None,
        profile: str | Profile | None = None,
        stats: bool = False,
    ) -> ScanStats | None:
        """Discover and register all @component and @adapter decorated classes.

        Scans the global registries for all classes decorated with @component
        or @adapter and registers them with the container. Dependencies are
        automatically resolved based on constructor type hints.

        This is the primary method for setting up the container in a
        declarative style. Call it once after all components are imported.

        Args:
            package: Optional package name to scan. If None, scans all registered
                components. If provided, imports all modules in the specified package
                (including sub-packages) to trigger decorator execution, then scans
                only components from that package.
            profile: Optional profile to filter components/adapters. Accepts either a
                Profile enum value (Profile.PRODUCTION, Profile.TEST, etc.) or a string
                profile name. If None, registers all components/adapters regardless of
                profile. If provided, only registers components/adapters that have the
                matching profile in their __dioxide_profiles__ attribute. Components/
                adapters decorated with Profile.ALL ("*") are registered in all profiles.
                Profile names are normalized to lowercase for matching.

        Registration behavior:
            - SINGLETON scope (default): Creates singleton factory with caching
            - FACTORY scope: Creates transient factory for new instances
            - Manual registrations take precedence over @component/@adapter decorators
            - Already-registered types are silently skipped
            - Profile filtering applies to components/adapters with @profile decorator
            - Adapters are registered under their port type (Protocol/ABC)
            - Multiple adapters for same port+profile raises ValueError

        Example:
            >>> from dioxide import Container, Profile, component, adapter, Scope, profile
            >>>
            >>> # Define a port (Protocol)
            >>> class EmailPort(Protocol):
            ...     async def send(self, to: str, subject: str, body: str) -> None: ...
            >>>
            >>> # Create adapter for production
            >>> @adapter.for_(EmailPort, profile='production')
            ... class SendGridAdapter:
            ...     async def send(self, to: str, subject: str, body: str) -> None:
            ...         pass
            >>>
            >>> # Create service that depends on port
            >>> @component
            ... class UserService:
            ...     def __init__(self, email: EmailPort):
            ...         self.email = email
            >>>
            >>> # Scan with Profile enum (recommended)
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> service = container.resolve(UserService)
            >>> # service.email is a SendGridAdapter instance
            >>>
            >>> # Or with string profile (also supported)
            >>> container2 = Container()
            >>> container2.scan(profile='production')  # Same as above

        Raises:
            ValueError: If multiple adapters are registered for the same port
                and profile combination (ambiguous registration)

        Note:
            - Ensure all component/adapter classes are imported before calling scan()
            - Constructor dependencies must have type hints
            - Circular dependencies will cause infinite recursion
            - Manual registrations (register_*) take precedence over scan()
            - Profile names are case-insensitive (normalized to lowercase)
        """
        from dioxide._registry import (
            PROFILE_ATTRIBUTE,
            _get_registered_components,
        )
        from dioxide.adapter import _adapter_registry
        from dioxide.scope import Scope

        start_time = time.perf_counter() if stats else None
        adapters_registered_count = 0
        services_registered_count = 0
        modules_imported_count = 0

        # Import package modules if package parameter provided
        if package is not None:
            modules_imported_count = self._import_package(package)

        # Normalize profile to lowercase if provided
        # Profile is a str subclass, so we can call .lower() directly on any str
        if profile is not None:
            normalized_profile = profile.lower()
        else:
            normalized_profile = None

        # Track active profile for error messages
        self._active_profile = normalized_profile

        # First, scan adapters and separate single vs multi-binding adapters
        port_to_single_adapters: dict[type[Any], list[type[Any]]] = {}
        port_to_multi_adapters: dict[type[Any], list[type[Any]]] = {}

        for adapter_class in _adapter_registry:
            # Apply package filtering if package parameter provided
            if package is not None:
                # Get the module where the adapter class is defined
                adapter_module = adapter_class.__module__
                # Check if adapter belongs to the scanned package
                if not adapter_module.startswith(package):
                    continue

            # Apply profile filtering if profile parameter provided
            if normalized_profile is not None:
                # Get adapter's profiles (if any)
                adapter_profiles: frozenset[str] = getattr(adapter_class, PROFILE_ATTRIBUTE, frozenset())

                # Skip if adapter doesn't have the requested profile AND doesn't have '*' (all profiles)
                if normalized_profile not in adapter_profiles and '*' not in adapter_profiles:
                    continue

            # Get the port this adapter implements
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is None:
                # This shouldn't happen if @adapter.for_() was used correctly
                continue

            # Check if this is a multi-binding adapter
            is_multi = getattr(adapter_class, '__dioxide_multi__', False)

            if is_multi:
                # Track multi-binding adapters separately
                if port_class not in port_to_multi_adapters:
                    port_to_multi_adapters[port_class] = []
                port_to_multi_adapters[port_class].append(adapter_class)
            else:
                # Track single adapters per port
                if port_class not in port_to_single_adapters:
                    port_to_single_adapters[port_class] = []
                port_to_single_adapters[port_class].append(adapter_class)

        # Check for ambiguous registrations (multiple SINGLE adapters for same port)
        for port_class, adapters in port_to_single_adapters.items():
            if len(adapters) > 1:
                adapter_names = ', '.join(cls.__name__ for cls in adapters)
                profile_str = f" for profile '{normalized_profile}'" if normalized_profile else ''
                raise ValueError(
                    f'Ambiguous adapter registration for port {port_class.__name__}{profile_str}: '
                    f'multiple adapters found ({adapter_names}). '
                    f'Only one adapter per port+profile combination is allowed.'
                )

        # Check for mixed single/multi registrations (same port has both)
        for port_class, single_adapters in port_to_single_adapters.items():
            if port_class in port_to_multi_adapters:
                single_names = ', '.join(cls.__name__ for cls in single_adapters)
                multi_names = ', '.join(cls.__name__ for cls in port_to_multi_adapters[port_class])
                raise ValueError(
                    f'Port {port_class.__name__} has both single adapters ({single_names}) '
                    f'and multi-binding adapters ({multi_names}). '
                    f'A port must be either single-binding OR multi-binding, not both.'
                )

        # Use single adapters for ambiguity checking downstream
        port_to_adapters = port_to_single_adapters

        # Check for captive dependencies (SINGLETON depends on REQUEST)
        self._check_captive_dependencies(port_to_adapters)

        # Register adapters under their port type
        for port_class, adapters in port_to_adapters.items():
            adapter_class = adapters[0]  # Only one adapter per port (checked above)

            # Create a factory that auto-injects dependencies
            factory = self._create_auto_injecting_factory(adapter_class)

            # Get the scope (adapters default to SINGLETON)
            scope = getattr(adapter_class, '__dioxide_scope__', Scope.SINGLETON)

            # Register under port type
            try:
                if scope == Scope.SINGLETON:
                    self.register_singleton_factory(port_class, factory)
                else:
                    self.register_transient_factory(port_class, factory)
                adapters_registered_count += 1
            except KeyError:
                # Already registered manually - skip it (manual takes precedence)
                pass

        # Register multi-binding adapters (sorted by priority)
        for port_class, adapters in port_to_multi_adapters.items():
            # Sort by priority (lower values first)
            sorted_adapters = sorted(adapters, key=lambda cls: getattr(cls, '__dioxide_priority__', 0))
            self._multi_bindings[port_class] = sorted_adapters

        # Then, scan components (existing logic)
        for component_class in _get_registered_components():
            # Apply package filtering if package parameter provided
            if package is not None:
                # Get the module where the component class is defined
                component_module = component_class.__module__
                # Check if component belongs to the scanned package
                if not component_module.startswith(package):
                    continue

            # Apply profile filtering if profile parameter provided
            if normalized_profile is not None:
                # Get component's profiles (if any)
                component_profiles: frozenset[str] = getattr(component_class, PROFILE_ATTRIBUTE, frozenset())

                # Skip if component doesn't have the requested profile AND doesn't have Profile.ALL
                # Profile.ALL ("*") makes a component available in all profiles
                if normalized_profile not in component_profiles and '*' not in component_profiles:
                    continue

            # Create a factory that auto-injects dependencies
            factory = self._create_auto_injecting_factory(component_class)

            # Check the scope
            scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

            # Check if this class implements a protocol
            protocol_class = getattr(component_class, '__dioxide_implements__', None)

            # Register the implementation under its concrete type
            try:
                if scope == Scope.SINGLETON:
                    # Register as singleton factory (Rust will cache the result)
                    self.register_singleton_factory(component_class, factory)
                else:
                    # Register as transient factory (Rust creates new instance each time)
                    self.register_transient_factory(component_class, factory)
                services_registered_count += 1
            except KeyError:
                # Already registered manually - skip it (manual takes precedence)
                pass

            # If this class implements a protocol, also register it under the protocol type
            # IMPORTANT: For singleton scope, both protocol and concrete class must resolve
            # to the same instance. We achieve this by creating a factory that resolves
            # the concrete class (which is already cached by Rust if singleton).
            if protocol_class is not None:
                # Create a factory that resolves via the concrete class
                # This ensures singleton instances are shared between protocol and concrete type
                def create_protocol_factory(impl_class: type[Any]) -> Callable[[], Any]:
                    """Create factory that resolves the concrete implementation."""
                    return lambda: self.resolve(impl_class)

                protocol_factory = create_protocol_factory(component_class)
                try:
                    if scope == Scope.SINGLETON:
                        self.register_singleton_factory(protocol_class, protocol_factory)
                    else:
                        self.register_transient_factory(protocol_class, protocol_factory)
                except KeyError:
                    # Protocol already has an implementation registered - skip it
                    # (This will happen with multiple implementations - we'll handle
                    # profile-based selection in a future iteration)
                    pass

        # Warn if profile was specified but matched zero components
        if normalized_profile is not None and len(self) == 0:
            logger.warning(
                "Profile '%s' matched zero components. Verify @adapter.for_() decorators are correctly applied.",
                normalized_profile,
            )

        if stats and start_time is not None:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ScanStats(
                services_registered=services_registered_count,
                adapters_registered=adapters_registered_count,
                modules_imported=modules_imported_count,
                duration_ms=round(elapsed_ms, 3),
            )

        return None

    def _create_auto_injecting_factory(self, cls: type[T]) -> Callable[[], T]:
        """Create a factory function that auto-injects dependencies from type hints.

        Internal method used by scan() to create factory functions that
        automatically resolve constructor dependencies and instantiate classes.

        Args:
            cls: The class to create a factory for. Must be a class type.

        Returns:
            A factory function that:
            - Inspects the class's __init__ type hints
            - Resolves each dependency from the container
            - Instantiates the class with resolved dependencies
            - Returns the fully-constructed instance

        Note:
            - If the class has no __init__ or no type hints, returns the class itself
            - Only parameters with type hints are resolved from the container
            - Parameters without type hints are skipped (not passed to __init__)
        """
        try:
            init_signature = inspect.signature(cls.__init__)
            # Pass both global and local namespaces to resolve forward references
            # For local classes (e.g., in tests), we need to pass the class's __dict__ as localns
            globalns = getattr(cls.__init__, '__globals__', {})
            # Include the class's own namespace to handle references to sibling local classes
            localns = dict(vars(cls))
            # Also include the class itself in case it's referenced
            localns[cls.__name__] = cls

            # For local classes defined in test functions, we need to get the frame locals
            # Try to extract locals from the class's qualname
            if '<locals>' in cls.__qualname__:
                # This is a local class - try to get its defining scope
                # We can't reliably get the locals, but we can at least handle the common case
                # by checking if there are any classes in the same module with the same qualname pattern
                try:
                    import sys
                    from types import FrameType

                    frame: FrameType | None = sys._getframe()
                    # Walk up the stack to find locals that might contain our dependencies
                    while frame is not None:
                        frame_locals = frame.f_locals
                        # Add any classes from frame locals
                        for name, obj in frame_locals.items():
                            if inspect.isclass(obj):
                                localns[name] = obj
                        frame = frame.f_back
                except (AttributeError, ValueError):
                    # Frame walking failed - continue without local class resolution
                    pass

            type_hints = get_type_hints(cls.__init__, globalns=globalns, localns=localns)
        except (ValueError, AttributeError, NameError):
            # No __init__ or no type hints, or can't resolve type hints - just instantiate directly
            return cls

        # Check if there are any actual dependencies to inject
        # If there are no type hints (empty dict) or only 'return' hint, just use the class directly
        injectable_params = [name for name in init_signature.parameters if name != 'self' and name in type_hints]
        if not injectable_params:
            # No dependencies to inject - return the class itself for direct instantiation
            return cls

        # Build factory that resolves dependencies
        def factory() -> T:
            kwargs: dict[str, Any] = {}
            for param_name in init_signature.parameters:
                if param_name == 'self':
                    continue
                if param_name in type_hints:
                    dependency_type = type_hints[param_name]
                    kwargs[param_name] = self.resolve(dependency_type)
            return cls(**kwargs)

        return factory

    def _build_lifecycle_dependency_order(self) -> list[Any]:
        """Build list of lifecycle components in dependency order.

        Returns:
            List of component instances sorted by dependency order (dependencies first).
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry

        # Collect all lifecycle component classes
        lifecycle_classes: dict[type[Any], Any] = {}

        # Check registered components (services)
        # Skip REQUEST-scoped components - they are initialized in scope, not at container start
        from dioxide.scope import Scope

        for component_class in _get_registered_components():
            if hasattr(component_class, '_dioxide_lifecycle'):
                # Skip REQUEST-scoped components - they're initialized within scopes
                component_scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)
                if component_scope == Scope.REQUEST:
                    continue
                try:
                    instance = self.resolve(component_class)
                    lifecycle_classes[component_class] = instance
                except (AdapterNotFoundError, ServiceNotFoundError):
                    # Component not registered for this profile - skip
                    pass

        # Check adapters - map port class to adapter instance
        # Only include adapters that ACTUALLY have @lifecycle (check the resolved instance's class)
        adapter_instances: dict[type[Any], Any] = {}
        for adapter_class in _adapter_registry:
            # Get the port this adapter implements
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is not None and port_class not in adapter_instances:
                try:
                    instance = self.resolve(port_class)
                    # Check if the RESOLVED instance's class has @lifecycle
                    # (not the registry class - that might be a different profile's adapter)
                    if hasattr(instance.__class__, '_dioxide_lifecycle'):
                        adapter_instances[port_class] = instance
                except (AdapterNotFoundError, ServiceNotFoundError):
                    # Adapter not registered for this profile - skip
                    pass

        # Build dependency graph
        dependencies: dict[Any, set[Any]] = {}
        all_instances: list[Any] = list(lifecycle_classes.values()) + list(adapter_instances.values())

        for component_class, instance in lifecycle_classes.items():
            deps = set()
            # Check constructor dependencies
            try:
                init_signature = inspect.signature(component_class.__init__)
                # Use the same logic as _create_auto_injecting_factory to handle local classes
                globalns = getattr(component_class.__init__, '__globals__', {})
                localns = dict(vars(component_class))
                localns[component_class.__name__] = component_class

                if '<locals>' in component_class.__qualname__:
                    try:
                        import sys
                        from types import FrameType

                        frame: FrameType | None = sys._getframe()
                        while frame is not None:
                            frame_locals = frame.f_locals
                            for name, obj in frame_locals.items():
                                if inspect.isclass(obj):
                                    localns[name] = obj
                            frame = frame.f_back
                    except (AttributeError, ValueError):
                        # Frame walking failed - continue without local class resolution
                        pass

                type_hints = get_type_hints(component_class.__init__, globalns=globalns, localns=localns)

                for param_name in init_signature.parameters:
                    if param_name == 'self':
                        continue
                    if param_name in type_hints:
                        dep_type = type_hints[param_name]
                        # Check if dependency is a lifecycle component
                        if dep_type in lifecycle_classes:
                            deps.add(lifecycle_classes[dep_type])
                        elif dep_type in adapter_instances:
                            deps.add(adapter_instances[dep_type])
            except (ValueError, AttributeError, NameError):
                pass

            dependencies[instance] = deps

        # Add adapters (they typically have no dependencies among lifecycle components)
        for instance in adapter_instances.values():
            if instance not in dependencies:
                dependencies[instance] = set()

        # Topological sort using Kahn's algorithm
        # in_degree[node] = number of dependencies node has (edges pointing TO node)
        from collections import deque

        in_degree = dict.fromkeys(all_instances, 0)
        for node in all_instances:
            for dep in dependencies.get(node, set()):
                if dep in in_degree:
                    # node depends on dep, so node has one incoming edge
                    in_degree[node] += 1

        queue = deque([node for node in all_instances if in_degree[node] == 0])
        sorted_instances = []

        while queue:
            node = queue.popleft()
            sorted_instances.append(node)

            # Find nodes that depend on this node
            for other_node in all_instances:
                if node in dependencies.get(other_node, set()):
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)

        # Detect circular dependencies
        if len(sorted_instances) < len(all_instances):
            unprocessed = set(all_instances) - set(sorted_instances)
            from dioxide.exceptions import CircularDependencyError

            # Build terse message with component names
            component_names = ', '.join(sorted(type(inst).__name__ for inst in unprocessed))
            raise CircularDependencyError(
                f'Circular dependency in @lifecycle components\n  Involved: {component_names}'
            )

        return sorted_instances

    async def start(self) -> None:
        """Initialize all @lifecycle components in dependency order.

        Resolves all registered components and calls initialize() on those
        decorated with @lifecycle. Components are initialized in dependency
        order (dependencies before their dependents).

        The list of lifecycle instances is cached during start() and reused
        during stop() to ensure all initialized components are disposed.

        If initialization fails for any component, all previously initialized
        components are disposed in reverse order (rollback).

        Raises:
            Exception: If any component's initialize() method raises an exception.
                Already-initialized components are disposed before re-raising.

        Example:
            >>> from dioxide import Container, service, lifecycle, Profile
            >>>
            >>> @service
            ... @lifecycle
            ... class Database:
            ...     async def initialize(self) -> None:
            ...         print('Database connected')
            ...
            ...     async def dispose(self) -> None:
            ...         print('Database disconnected')
            >>>
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> await container.start()
            Database connected
        """
        # Build dependency-ordered list and cache it for stop()
        self._lifecycle_instances = self._build_lifecycle_dependency_order()

        # Track initialized components for rollback
        initialized_components: list[Any] = []

        try:
            # Initialize components in dependency order
            for component in self._lifecycle_instances:
                await component.initialize()
                initialized_components.append(component)

        except Exception:
            # Rollback: dispose already-initialized components in reverse order
            for component in reversed(initialized_components):
                try:
                    await component.dispose()
                except Exception:
                    # Log but don't raise - we're already in error state
                    pass
            # Clear the cache on failure
            self._lifecycle_instances = None
            raise

    async def stop(self) -> None:
        """Dispose all @lifecycle components in reverse dependency order.

        Calls dispose() on all components decorated with @lifecycle. Components
        are disposed in reverse dependency order (dependents before their
        dependencies).

        Uses the cached list of lifecycle instances from start() to ensure
        exactly the components that were initialized are disposed.

        If disposal fails for any component, continues disposing remaining
        components (does not raise until all disposals are attempted).

        Example:
            >>> from dioxide import Container, service, lifecycle, Profile
            >>>
            >>> @service
            ... @lifecycle
            ... class Database:
            ...     async def initialize(self) -> None:
            ...         pass
            ...
            ...     async def dispose(self) -> None:
            ...         print('Database disconnected')
            >>>
            >>> container = Container()
            >>> container.scan(profile=Profile.PRODUCTION)
            >>> await container.start()
            >>> await container.stop()
            Database disconnected
        """
        # Use cached lifecycle instances from start()
        # If start() was never called, there's nothing to dispose
        if self._lifecycle_instances is None:
            return

        # Dispose components in reverse order (dependents first)
        for component in reversed(self._lifecycle_instances):
            try:
                await component.dispose()
            except Exception as e:
                # Continue disposing other components even if one fails
                import logging

                logging.error(f'Error disposing component {component.__class__.__name__}: {e}')

        # Clear the cache after disposal
        self._lifecycle_instances = None

    async def __aenter__(self) -> Container:
        """Enter async context manager - calls start().

        Example:
            >>> from dioxide import Container, service, lifecycle
            >>>
            >>> @service
            ... @lifecycle
            ... class Database:
            ...     async def initialize(self) -> None:
            ...         print('Connected')
            ...
            ...     async def dispose(self) -> None:
            ...         print('Disconnected')
            >>>
            >>> async with Container() as container:
            ...     container.scan()
            ...     # Use container
            Connected
            Disconnected
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager - calls stop().

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        await self.stop()

    def reset(self) -> None:
        """Clear cached instances for test isolation.

        Clears the singleton cache but preserves provider registrations.
        Use this between tests to ensure fresh instances without re-scanning.

        This method is particularly useful in pytest fixtures to ensure
        test isolation while avoiding the overhead of re-scanning:

        Example::

            @pytest.fixture(autouse=True)
            def setup_container():
                container.scan(profile=Profile.TEST)
                yield
                container.reset()  # Fresh instances for next test

        For complete isolation (including new provider registrations),
        consider using fresh Container instances instead.

        Note:
            - Instance registrations (via register_instance) are NOT cleared
              because they reference external objects
            - Provider registrations are preserved (no need to re-scan)
            - Lifecycle instance cache is cleared

        See Also:
            Container: Create fresh instances for complete isolation
        """
        self._rust_core.reset()
        self._lifecycle_instances = None

    def create_scope(self) -> ScopedContainerContextManager:
        """Create a new scope for REQUEST-scoped dependency resolution.

        Returns an async context manager that provides a ScopedContainer for
        resolving REQUEST-scoped dependencies. Each scope maintains its own
        cache of REQUEST-scoped instances.

        Usage::

            async with container.create_scope() as scope:
                # REQUEST-scoped components are cached within this scope
                handler = scope.resolve(RequestHandler)
                # Same scope = same instance
                handler2 = scope.resolve(RequestHandler)
                assert handler is handler2

            # Scope exits - REQUEST components are disposed

        Scope behavior:
            - **SINGLETON**: Resolved from parent container (shared)
            - **REQUEST**: Cached within scope (fresh per scope)
            - **FACTORY**: New instance each resolution

        Lifecycle management:
            REQUEST-scoped components decorated with @lifecycle have their
            dispose() method called when the scope exits.

        Returns:
            An async context manager that yields a ScopedContainer.

        Example:
            >>> from dioxide import Container, service, Scope
            >>>
            >>> @service(scope=Scope.REQUEST)
            ... class RequestContext:
            ...     def __init__(self):
            ...         self.request_id = str(uuid.uuid4())
            >>>
            >>> container = Container()
            >>> container.scan()
            >>>
            >>> async with container.create_scope() as scope:
            ...     ctx1 = scope.resolve(RequestContext)
            ...     ctx2 = scope.resolve(RequestContext)
            ...     assert ctx1 is ctx2  # Same within scope
            >>>
            >>> async with container.create_scope() as scope2:
            ...     ctx3 = scope2.resolve(RequestContext)
            ...     assert ctx3 is not ctx1  # Different scope = different instance

        See Also:
            - :class:`ScopedContainer` - The scoped container type
            - :class:`dioxide.scope.Scope` - Scope enum
            - :class:`dioxide.exceptions.ScopeError` - Scope errors
        """
        return ScopedContainerContextManager(self)


class ScopedContainer:
    """A scoped container for REQUEST-scoped dependency resolution.

    ScopedContainer provides a context for resolving REQUEST-scoped dependencies.
    It wraps a parent Container and maintains its own cache of REQUEST-scoped
    instances that are unique to this scope.

    Key behaviors:
        - **SINGLETON**: Resolved from parent container (shared across all scopes)
        - **REQUEST**: Cached within this scope (fresh per scope, shared within scope)
        - **FACTORY**: New instance each time (same as parent container)

    Creating a ScopedContainer:
        Use the async context manager pattern via ``container.create_scope()``::

            async with container.create_scope() as scope:
                # REQUEST-scoped components are cached within this scope
                handler = scope.resolve(RequestHandler)
                # Same scope = same instance
                handler2 = scope.resolve(RequestHandler)
                assert handler is handler2

            # Scope exits - REQUEST components are disposed

        Each scope has a unique ID for tracking and debugging::

            async with container.create_scope() as scope:
                print(f'Scope ID: {scope.scope_id}')  # e.g., "abc123..."

    REQUEST-scoped dependencies:
        Components decorated with ``@service(scope=Scope.REQUEST)`` require
        a scope context for resolution::

            @service(scope=Scope.REQUEST)
            class RequestContext:
                def __init__(self):
                    self.request_id = str(uuid.uuid4())


            # Outside scope - raises ScopeError
            container.resolve(RequestContext)  # Error!

            # Inside scope - works
            async with container.create_scope() as scope:
                ctx = scope.resolve(RequestContext)  # OK

    Lifecycle management:
        REQUEST-scoped components with ``@lifecycle`` are disposed when
        the scope exits::

            @service(scope=Scope.REQUEST)
            @lifecycle
            class DbConnection:
                async def initialize(self) -> None:
                    self.conn = await create_connection()

                async def dispose(self) -> None:
                    await self.conn.close()


            async with container.create_scope() as scope:
                db = scope.resolve(DbConnection)
                # db.initialize() called automatically
            # db.dispose() called automatically on scope exit

    Attributes:
        scope_id: Unique identifier for this scope
        parent: The parent Container

    See Also:
        - :meth:`Container.create_scope` - How to create scopes
        - :class:`dioxide.scope.Scope` - Scope enum (SINGLETON, REQUEST, FACTORY)
        - :class:`dioxide.exceptions.ScopeError` - Raised for scope violations
    """

    def __init__(self, parent: Container, scope_id: str) -> None:
        """Initialize a scoped container.

        Args:
            parent: The parent Container to delegate SINGLETON resolution to.
            scope_id: A unique identifier for this scope.

        Note:
            This constructor is internal. Use ``container.create_scope()`` instead.
        """
        self._parent = parent
        self._scope_id = scope_id
        self._request_cache: dict[type[Any], Any] = {}
        self._lifecycle_instances: list[Any] = []  # Track for disposal

    @property
    def scope_id(self) -> str:
        """Get the unique identifier for this scope."""
        return self._scope_id

    @property
    def parent(self) -> Container:
        """Get the parent container."""
        return self._parent

    def __repr__(self) -> str:
        """Return an informative string representation for debugging.

        Shows the active profile from the parent container and the parent type
        so agents and developers can inspect scoped container state.

        Returns:
            A string like ``ScopedContainer(profile=Profile('test'), parent=Container)``.

        Example:
            >>> async with container.create_scope() as scope:
            ...     repr(scope)
            "ScopedContainer(profile=Profile('test'), parent=Container)"
        """
        profile = self._parent.active_profile
        profile_str = repr(profile) if profile is not None else 'None'
        parent_type = type(self._parent).__name__

        return f'ScopedContainer(profile={profile_str}, parent={parent_type})'

    def resolve(self, component_type: type[T]) -> T:
        """Resolve a component instance within this scope.

        Resolution behavior depends on the component's scope:
            - **SINGLETON**: Delegates to parent container (shared instance)
            - **REQUEST**: Caches in this scope (fresh per scope)
            - **FACTORY**: New instance each resolution (no caching)

        Args:
            component_type: The type to resolve.

        Returns:
            An instance of the requested type.

        Raises:
            AdapterNotFoundError: If the type is a port with no adapter.
            ServiceNotFoundError: If the type is an unregistered service.

        Example:
            >>> async with container.create_scope() as scope:
            ...     # REQUEST-scoped: cached within scope
            ...     ctx1 = scope.resolve(RequestContext)
            ...     ctx2 = scope.resolve(RequestContext)
            ...     assert ctx1 is ctx2  # Same instance
            ...
            ...     # SINGLETON: shared with parent
            ...     config = scope.resolve(AppConfig)
        """
        from dioxide.scope import Scope

        # Get the scope for this component type
        scope = self._get_component_scope(component_type)

        if scope == Scope.SINGLETON:
            # Delegate to parent container for SINGLETON
            return self._parent.resolve(component_type)

        elif scope == Scope.REQUEST:
            # Check cache first
            if component_type in self._request_cache:
                return self._request_cache[component_type]  # type: ignore[no-any-return]

            # Create new instance using parent's factory logic
            instance = self._create_instance(component_type)

            # Cache in scope
            self._request_cache[component_type] = instance

            # Track lifecycle components for disposal
            if hasattr(component_type, '_dioxide_lifecycle'):
                self._lifecycle_instances.append(instance)

            return instance

        else:  # FACTORY
            # Always create new instance, no caching
            return self._create_instance(component_type)

    def _get_component_scope(self, component_type: type[Any]) -> Scope:
        """Get the scope for a component type.

        Args:
            component_type: The type to check.

        Returns:
            The Scope enum value for this component.
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry

        # Check if it's a registered component (service)
        for component_class in _get_registered_components():
            if component_class is component_type:
                return getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

        # Check if it's a port - look up the adapter for the port
        for adapter_class in _adapter_registry:
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is component_type:
                return getattr(adapter_class, '__dioxide_scope__', Scope.SINGLETON)

        # Default to SINGLETON for unknown types
        return Scope.SINGLETON

    def _create_instance(self, component_type: type[T]) -> T:
        """Create an instance of a component, resolving dependencies.

        This method handles dependency injection for REQUEST-scoped components,
        ensuring that dependencies are resolved from the appropriate scope.

        Args:
            component_type: The type to instantiate.

        Returns:
            A new instance with dependencies injected.
        """
        from dioxide._registry import _get_registered_components
        from dioxide.adapter import _adapter_registry
        from dioxide.scope import Scope

        # Find the actual implementation class
        impl_class: type[Any] | None = None

        # Check if it's a port - find the adapter
        for adapter_class in _adapter_registry:
            port_class = getattr(adapter_class, '__dioxide_port__', None)
            if port_class is component_type:
                # Check if adapter matches active profile
                adapter_profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())
                active_profile = self._parent._active_profile
                if active_profile in adapter_profiles or '*' in adapter_profiles:
                    impl_class = adapter_class
                    break

        # Check if it's a registered component
        if impl_class is None:
            for component_class in _get_registered_components():
                if component_class is component_type:
                    impl_class = component_class
                    break

        if impl_class is None:
            # Fall back to resolving from parent (might be manually registered)
            # This will raise appropriate errors if not found
            return self._parent.resolve(component_type)

        # Inspect constructor for dependencies
        try:
            init_signature = inspect.signature(impl_class.__init__)
            globalns = getattr(impl_class.__init__, '__globals__', {})
            localns = dict(vars(impl_class))
            localns[impl_class.__name__] = impl_class

            # Handle local classes in tests
            if '<locals>' in impl_class.__qualname__:
                try:
                    import sys
                    from types import FrameType

                    frame: FrameType | None = sys._getframe()
                    while frame is not None:
                        frame_locals = frame.f_locals
                        for name, obj in frame_locals.items():
                            if inspect.isclass(obj):
                                localns[name] = obj
                        frame = frame.f_back
                except (AttributeError, ValueError):
                    pass

            type_hints = get_type_hints(impl_class.__init__, globalns=globalns, localns=localns)
        except (ValueError, AttributeError, NameError):
            # No type hints - instantiate directly
            return impl_class()  # type: ignore[no-any-return]

        # Resolve dependencies
        kwargs: dict[str, Any] = {}
        for param_name in init_signature.parameters:
            if param_name == 'self':
                continue
            if param_name in type_hints:
                dependency_type = type_hints[param_name]
                dep_scope = self._get_component_scope(dependency_type)

                if dep_scope == Scope.SINGLETON:
                    # SINGLETON deps come from parent
                    kwargs[param_name] = self._parent.resolve(dependency_type)
                else:
                    # REQUEST and FACTORY deps come from this scope
                    kwargs[param_name] = self.resolve(dependency_type)

        return impl_class(**kwargs)  # type: ignore[no-any-return]

    def __getitem__(self, component_type: type[T]) -> T:
        """Resolve a component using bracket syntax.

        Equivalent to calling ``scope.resolve(component_type)``.

        Args:
            component_type: The type to resolve.

        Returns:
            An instance of the requested type.

        Example:
            >>> async with container.create_scope() as scope:
            ...     ctx = scope[RequestContext]  # Same as scope.resolve(RequestContext)
        """
        return self.resolve(component_type)

    def create_scope(self) -> ScopedContainerContextManager:
        """Nested scopes are not supported in v0.3.0.

        Raises:
            ScopeError: Always raises, as nested scopes are not supported.
        """
        raise ScopeError('Nested scopes not supported')

    async def _dispose_lifecycle_components(self) -> None:
        """Dispose all REQUEST-scoped lifecycle components in reverse order.

        Called when the scope exits to clean up resources.
        """
        # Dispose in reverse order (dependents before dependencies)
        for component in reversed(self._lifecycle_instances):
            try:
                await component.dispose()
            except Exception as e:
                logger.error(f'Error disposing scoped component {component.__class__.__name__}: {e}')

        self._lifecycle_instances.clear()


class ScopedContainerContextManager:
    """Async context manager for ScopedContainer.

    This class manages the lifecycle of a ScopedContainer, handling
    setup on entry and disposal on exit.

    Usage:
        >>> async with container.create_scope() as scope:
        ...     handler = scope.resolve(RequestHandler)
    """

    def __init__(self, parent: Container) -> None:
        """Initialize the context manager.

        Args:
            parent: The parent container.
        """
        self._parent = parent
        self._scope: ScopedContainer | None = None

    async def __aenter__(self) -> ScopedContainer:
        """Enter the scope context.

        Creates a new ScopedContainer with a unique ID.

        Returns:
            The newly created ScopedContainer.
        """
        import uuid

        scope_id = str(uuid.uuid4())
        self._scope = ScopedContainer(self._parent, scope_id)
        return self._scope

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the scope context.

        Disposes all REQUEST-scoped lifecycle components.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        if self._scope is not None:
            await self._scope._dispose_lifecycle_components()
            self._scope = None


# Global singleton container instance for simplified API.
#
# This provides the MLP-style ergonomic API while keeping the Container class
# available for advanced use cases (testing isolation, multi-tenant apps).
#
# THREAD SAFETY GUARANTEES:
#
# This global container is thread-safe due to Python's module import system:
#
# 1. INITIALIZATION: Python's import machinery holds a lock during module
#    initialization, ensuring this Container() instantiation happens exactly
#    once, even if multiple threads import dioxide simultaneously.
#
# 2. ACCESS: Once the module is initialized, reading the `container` variable
#    is a simple atomic attribute lookup, protected by the GIL.
#
# 3. RESOLUTION: The underlying Rust container uses thread-safe data structures
#    for singleton caching and provider storage.
#
# RECOMMENDED USAGE PATTERN:
#
#     # At application startup (single-threaded context):
#     from dioxide import container, Profile
#     container.scan(profile=Profile.PRODUCTION)
#
#     # From any thread after startup:
#     service = container.resolve(MyService)  # Thread-safe
#
# FOR PER-THREAD ISOLATION:
#
# If you need completely isolated dependency graphs per thread (e.g., for
# multi-tenant applications or testing), create separate Container instances:
#
#     thread_local_container = Container()
#     thread_local_container.scan(profile=Profile.TEST)
#
# Alternatively, use scoped containers for request-level isolation:
#
#     async with container.create_scope() as scope:
#         ctx = scope.resolve(RequestContext)  # Fresh per scope
#
container: Container = Container()


def reset_global_container() -> None:
    """Reset the global container to an empty state.

    This function replaces the global container's internal state with a fresh
    Rust container instance, clearing all registrations and cached singletons.
    The global container object reference remains the same, so any code holding
    a reference to ``container`` will see the reset state.

    .. warning::

        **This function is intended for testing only.**

        Calling this in production code will cause unpredictable behavior as
        all registered services and adapters will be lost. Any code that has
        already resolved dependencies will hold stale references.

    Use this function in test fixtures to ensure test isolation::

        import pytest
        from dioxide import container, reset_global_container, Profile


        @pytest.fixture(autouse=True)
        def isolated_container():
            container.scan(profile=Profile.TEST)
            yield
            reset_global_container()

    For most testing scenarios, consider using :func:`dioxide.testing.fresh_container`
    instead, which creates completely isolated Container instances::

        from dioxide.testing import fresh_container


        async def test_something():
            async with fresh_container(profile=Profile.TEST) as c:
                service = c.resolve(MyService)
                # ... test with isolated container

    Returns:
        None

    Example:
        >>> from dioxide import container, reset_global_container, service
        >>>
        >>> @service
        ... class MyService:
        ...     pass
        >>>
        >>> container.scan()
        >>> assert not container.is_empty()
        >>> reset_global_container()
        >>> assert container.is_empty()

    See Also:
        :meth:`Container.reset`: Clears singleton cache but preserves registrations
        :func:`dioxide.testing.fresh_container`: Creates isolated container instances
    """
    global container
    # Replace internal state rather than reassigning the global
    # This ensures code that imported `container` sees the reset state
    container._rust_core = RustContainer()
    container._active_profile = None
    container._lifecycle_instances = None
