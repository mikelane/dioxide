dioxide.container
=================

.. py:module:: dioxide.container

.. autoapi-nested-parse::

   Profile-based dependency injection container with lifecycle management.

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
       For most applications, use the global singleton container::

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

   .. seealso::

      - :class:`dioxide.adapter.adapter` - For marking infrastructure adapters
      - :class:`dioxide.services.service` - For marking core domain services
      - :class:`dioxide.lifecycle.lifecycle` - For initialization/cleanup
      - :class:`dioxide.profile_enum.Profile` - Standard profile enum values
      - :class:`dioxide.exceptions.AdapterNotFoundError` - Port resolution error
      - :class:`dioxide.exceptions.ServiceNotFoundError` - Service resolution error



Attributes
----------

.. autoapisummary::

   dioxide.container.logger
   dioxide.container.T
   dioxide.container.container


Classes
-------

.. autoapisummary::

   dioxide.container.Container


Module Contents
---------------

.. py:data:: logger

.. py:data:: T

.. py:class:: Container(allowed_packages = None)

   Dependency injection container.

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

   .. admonition:: Examples

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

   .. note::

      The container should be created once at application startup and
      reused throughout the application lifecycle. Each container maintains
      its own singleton cache and registration state.


   .. py:method:: register_instance(component_type, instance)

      Register a pre-created instance for a given type.

      This method registers an already-instantiated object that will be
      returned whenever the type is resolved. Useful for registering
      configuration objects or external dependencies.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param instance: The pre-created instance to return for this type. Must
                       be an instance of component_type or a compatible type.

      :raises KeyError: If the type is already registered in this container.
          Each type can only be registered once.

      .. admonition:: Example

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



   .. py:method:: register_class(component_type, implementation)

      Register a class to instantiate for a given type.

      Registers a class that will be instantiated with no arguments when
      the type is resolved. The class's __init__ method will be called
      without parameters.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param implementation: The class to instantiate. Must have a no-argument
                             __init__ method (or no __init__ at all).

      :raises KeyError: If the type is already registered in this container.

      .. admonition:: Example

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

      .. note::

         For classes requiring constructor arguments, use
         register_singleton_factory() or register_transient_factory()
         with a lambda that provides the arguments.



   .. py:method:: register_singleton_factory(component_type, factory)

      Register a singleton factory function for a given type.

      The factory will be called once when the type is first resolved,
      and the result will be cached. All subsequent resolve() calls for
      this type will return the same cached instance.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param factory: A callable that takes no arguments and returns an instance
                      of component_type. Called exactly once, on first resolve().

      :raises KeyError: If the type is already registered in this container.

      .. admonition:: Example

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

      .. note::

         This is the recommended registration method for most services,
         as it provides lazy initialization and instance sharing.



   .. py:method:: register_transient_factory(component_type, factory)

      Register a transient factory function for a given type.

      The factory will be called every time the type is resolved, creating
      a new instance for each resolve() call. Use this for stateful objects
      that should not be shared.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param factory: A callable that takes no arguments and returns an instance
                      of component_type. Called on every resolve() to create a fresh
                      instance.

      :raises KeyError: If the type is already registered in this container.

      .. admonition:: Example

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

      .. note::

         Use this for objects with per-request or per-operation lifecycle.
         For shared services, use register_singleton_factory() instead.



   .. py:method:: register_singleton(component_type, factory)

      Register a singleton provider manually.

      Convenience method that calls register_singleton_factory(). The factory
      will be called once when the type is first resolved, and the result
      will be cached for the lifetime of the container.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param factory: A callable that takes no arguments and returns an instance
                      of component_type. Called exactly once, on first resolve().

      :raises KeyError: If the type is already registered in this container.

      .. admonition:: Example

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

      .. note::

         This is an alias for register_singleton_factory() provided for
         convenience and clarity.



   .. py:method:: register_factory(component_type, factory)

      Register a transient (factory) provider manually.

      Convenience method that calls register_transient_factory(). The factory
      will be called every time the type is resolved, creating a new instance
      for each resolve() call.

      :param component_type: The type to register. This is used as the lookup
                             key when resolving dependencies.
      :param factory: A callable that takes no arguments and returns an instance
                      of component_type. Called on every resolve() to create a fresh
                      instance.

      :raises KeyError: If the type is already registered in this container.

      .. admonition:: Example

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

      .. note::

         This is an alias for register_transient_factory() provided for
         convenience and clarity.



   .. py:method:: resolve(component_type)

      Resolve a component instance.

      Retrieves or creates an instance of the requested type based on its
      registration. For singletons, returns the cached instance (creating
      it on first call). For factories, creates a new instance every time.

      :param component_type: The type to resolve. Must have been previously
                             registered via scan() or manual registration methods.

      :returns: An instance of the requested type. For SINGLETON scope, the same
                instance is returned on every call. For FACTORY scope, a new
                instance is created on each call.

      :raises AdapterNotFoundError: If the type is a port (Protocol/ABC) and no
          adapter is registered for the current profile.
      :raises ServiceNotFoundError: If the type is a service/component that cannot
          be resolved (not registered or has unresolvable dependencies).

      .. admonition:: Example

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

      .. note::

         Type annotations in constructors enable automatic dependency
         injection. The container recursively resolves all dependencies.



   .. py:method:: __getitem__(component_type)

      Resolve a component using bracket syntax.

      Provides an alternative, more Pythonic syntax for resolving components.
      This method is equivalent to calling resolve() and simply delegates to it.

      :param component_type: The type to resolve. Must have been previously
                             registered via scan() or manual registration methods.

      :returns: An instance of the requested type. For SINGLETON scope, the same
                instance is returned on every call. For FACTORY scope, a new
                instance is created on each call.

      :raises KeyError: If the type is not registered in this container.

      .. admonition:: Example

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

      .. note::

         This is purely a convenience method. Both container[Type] and
         container.resolve(Type) work identically and return the same
         instance for singleton-scoped components.



   .. py:method:: is_empty()

      Check if container has no registered providers.

      :returns: True if no types have been registered, False if at least one
                type has been registered.

      .. admonition:: Example

         >>> from dioxide import Container
         >>>
         >>> container = Container()
         >>> assert container.is_empty()
         >>>
         >>> container.scan()  # Register @component classes
         >>> # If any @component classes exist, container is no longer empty



   .. py:method:: __len__()

      Get count of registered providers.

      :returns: The number of types that have been registered in this container.

      .. admonition:: Example

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



   .. py:method:: scan(package = None, profile = None)

      Discover and register all @component and @adapter decorated classes.

      Scans the global registries for all classes decorated with @component
      or @adapter and registers them with the container. Dependencies are
      automatically resolved based on constructor type hints.

      This is the primary method for setting up the container in a
      declarative style. Call it once after all components are imported.

      :param package: Optional package name to scan. If None, scans all registered
                      components. If provided, imports all modules in the specified package
                      (including sub-packages) to trigger decorator execution, then scans
                      only components from that package.
      :param profile: Optional profile to filter components/adapters. Accepts either a
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

      .. admonition:: Example

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

      :raises ValueError: If multiple adapters are registered for the same port
          and profile combination (ambiguous registration)

      .. note::

         - Ensure all component/adapter classes are imported before calling scan()
         - Constructor dependencies must have type hints
         - Circular dependencies will cause infinite recursion
         - Manual registrations (register_*) take precedence over scan()
         - Profile names are case-insensitive (normalized to lowercase)



   .. py:method:: start()
      :async:


      Initialize all @lifecycle components in dependency order.

      Resolves all registered components and calls initialize() on those
      decorated with @lifecycle. Components are initialized in dependency
      order (dependencies before their dependents).

      The list of lifecycle instances is cached during start() and reused
      during stop() to ensure all initialized components are disposed.

      If initialization fails for any component, all previously initialized
      components are disposed in reverse order (rollback).

      :raises Exception: If any component's initialize() method raises an exception.
          Already-initialized components are disposed before re-raising.

      .. admonition:: Example

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



   .. py:method:: stop()
      :async:


      Dispose all @lifecycle components in reverse dependency order.

      Calls dispose() on all components decorated with @lifecycle. Components
      are disposed in reverse dependency order (dependents before their
      dependencies).

      Uses the cached list of lifecycle instances from start() to ensure
      exactly the components that were initialized are disposed.

      If disposal fails for any component, continues disposing remaining
      components (does not raise until all disposals are attempted).

      .. admonition:: Example

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



   .. py:method:: __aenter__()
      :async:


      Enter async context manager - calls start().

      .. admonition:: Example

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



   .. py:method:: __aexit__(exc_type, exc_val, exc_tb)
      :async:


      Exit async context manager - calls stop().

      :param exc_type: Exception type if an exception was raised
      :param exc_val: Exception value if an exception was raised
      :param exc_tb: Exception traceback if an exception was raised



   .. py:method:: reset()

      Clear cached instances for test isolation.

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

      .. note::

         - Instance registrations (via register_instance) are NOT cleared
           because they reference external objects
         - Provider registrations are preserved (no need to re-scan)
         - Lifecycle instance cache is cleared

      .. seealso:: Container: Create fresh instances for complete isolation



.. py:data:: container
   :type:  Container
