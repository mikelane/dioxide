dioxide
=======

.. py:module:: dioxide

.. autoapi-nested-parse::

   dioxide: Fast, Rust-backed declarative dependency injection for Python.

   dioxide is a modern dependency injection framework that combines:
   - Declarative Python API with hexagonal architecture support
   - High-performance Rust-backed container implementation
   - Type-safe dependency resolution with IDE autocomplete support
   - Profile-based configuration for different environments

   Quick Start (using global singleton container):
       >>> from dioxide import container, service, adapter, Profile
       >>> from typing import Protocol
       >>>
       >>> class EmailPort(Protocol):
       ...     async def send(self, to: str, subject: str, body: str) -> None: ...
       >>>
       >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
       ... class SendGridAdapter:
       ...     async def send(self, to: str, subject: str, body: str) -> None:
       ...         pass  # Real implementation
       >>>
       >>> @service
       ... class UserService:
       ...     def __init__(self, email: EmailPort):
       ...         self.email = email
       >>>
       >>> container.scan(profile=Profile.PRODUCTION)
       >>> service = container.resolve(UserService)
       >>> # Or use bracket syntax:
       >>> service = container[UserService]

   Advanced: Creating separate containers for testing isolation:
       >>> from dioxide import Container
       >>>
       >>> test_container = Container()
       >>> test_container.scan(profile=Profile.TEST)
       >>> service = test_container.resolve(UserService)

   For more information, see the README and documentation.



Submodules
----------

.. toctree::
   :maxdepth: 1

   /api/dioxide/adapter/index
   /api/dioxide/celery/index
   /api/dioxide/click/index
   /api/dioxide/container/index
   /api/dioxide/django/index
   /api/dioxide/exceptions/index
   /api/dioxide/fastapi/index
   /api/dioxide/flask/index
   /api/dioxide/lifecycle/index
   /api/dioxide/ninja/index
   /api/dioxide/profile_enum/index
   /api/dioxide/scope/index
   /api/dioxide/services/index
   /api/dioxide/testing/index


Attributes
----------

.. autoapisummary::

   dioxide.adapter
   dioxide.container


Exceptions
----------

.. autoapisummary::

   dioxide.AdapterNotFoundError
   dioxide.CaptiveDependencyError
   dioxide.ScopeError
   dioxide.ServiceNotFoundError


Classes
-------

.. autoapisummary::

   dioxide.Container
   dioxide.ScopedContainer
   dioxide.Profile
   dioxide.Scope


Functions
---------

.. autoapisummary::

   dioxide.reset_global_container
   dioxide.lifecycle
   dioxide.service
   dioxide.fresh_container


Package Contents
----------------

.. py:data:: adapter

.. py:class:: Container(allowed_packages = None, profile = None)

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
      :raises ScopeError: If trying to resolve a REQUEST-scoped component outside
          of a scope context. Use ``container.create_scope()`` to create
          a scope.

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



   .. py:method:: create_scope()

      Create a new scope for REQUEST-scoped dependency resolution.

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

      :returns: An async context manager that yields a ScopedContainer.

      .. admonition:: Example

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

      .. seealso::

         - :class:`ScopedContainer` - The scoped container type
         - :class:`dioxide.scope.Scope` - Scope enum
         - :class:`dioxide.exceptions.ScopeError` - Scope errors



.. py:class:: ScopedContainer(parent, scope_id)

   A scoped container for REQUEST-scoped dependency resolution.

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

   .. attribute:: scope_id

      Unique identifier for this scope

   .. attribute:: parent

      The parent Container

   .. seealso::

      - :meth:`Container.create_scope` - How to create scopes
      - :class:`dioxide.scope.Scope` - Scope enum (SINGLETON, REQUEST, FACTORY)
      - :class:`dioxide.exceptions.ScopeError` - Raised for scope violations


   .. py:property:: scope_id
      :type: str


      Get the unique identifier for this scope.


   .. py:property:: parent
      :type: Container


      Get the parent container.


   .. py:method:: resolve(component_type)

      Resolve a component instance within this scope.

      Resolution behavior depends on the component's scope:
          - **SINGLETON**: Delegates to parent container (shared instance)
          - **REQUEST**: Caches in this scope (fresh per scope)
          - **FACTORY**: New instance each resolution (no caching)

      :param component_type: The type to resolve.

      :returns: An instance of the requested type.

      :raises AdapterNotFoundError: If the type is a port with no adapter.
      :raises ServiceNotFoundError: If the type is an unregistered service.

      .. admonition:: Example

         >>> async with container.create_scope() as scope:
         ...     # REQUEST-scoped: cached within scope
         ...     ctx1 = scope.resolve(RequestContext)
         ...     ctx2 = scope.resolve(RequestContext)
         ...     assert ctx1 is ctx2  # Same instance
         ...
         ...     # SINGLETON: shared with parent
         ...     config = scope.resolve(AppConfig)



   .. py:method:: __getitem__(component_type)

      Resolve a component using bracket syntax.

      Equivalent to calling ``scope.resolve(component_type)``.

      :param component_type: The type to resolve.

      :returns: An instance of the requested type.

      .. admonition:: Example

         >>> async with container.create_scope() as scope:
         ...     ctx = scope[RequestContext]  # Same as scope.resolve(RequestContext)



   .. py:method:: create_scope()

      Nested scopes are not supported in v0.3.0.

      :raises ScopeError: Always raises, as nested scopes are not supported.



.. py:data:: container
   :type:  Container

.. py:function:: reset_global_container()

   Reset the global container to an empty state.

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

   :returns: None

   .. admonition:: Example

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

   .. seealso::

      :meth:`Container.reset`: Clears singleton cache but preserves registrations
      :func:`dioxide.testing.fresh_container`: Creates isolated container instances


.. py:exception:: AdapterNotFoundError

   Bases: :py:obj:`Exception`


   Raised when no adapter is registered for a port in the active profile.

   This error occurs when trying to resolve a Protocol or ABC (port) but no
   concrete implementation (adapter) is registered for the current profile.
   It indicates a profile mismatch or missing adapter registration.

   In hexagonal architecture, ports are abstract interfaces (Protocols/ABCs)
   and adapters are concrete implementations. The container injects the active
   adapter based on the current profile. This error means:
   1. No adapter exists for this port + profile combination, OR
   2. An adapter exists but for a different profile, OR
   3. The adapter wasn't imported before container.scan()

   The error message includes:
       - **Port type**: Which Protocol/ABC couldn't be resolved
       - **Active profile**: Current profile from container.scan(profile=...)
       - **Available adapters**: List of adapters for this port in other profiles
       - **Registration hint**: Code example showing how to fix

   When This Occurs:
       - ``container.resolve(PortType)`` - Port has no adapter for active profile
       - ``container.resolve(ServiceType)`` - Service depends on port with no adapter
       - ``container.start()`` - Lifecycle component depends on port with no adapter

   Common Causes:
       1. **Profile mismatch**: Adapter registered for PRODUCTION, scanning TEST
       2. **Missing test adapter**: Production adapter exists, no TEST fake created
       3. **Typo in profile name**: 'test' vs 'testing' (case-insensitive)
       4. **Adapter not imported**: Decorator not executed before scan()
       5. **Forgot @adapter.for_() decorator**: Class exists but not registered

   .. admonition:: Examples

      Profile mismatch (most common)::

          from typing import Protocol
          from dioxide import Container, adapter, Profile


          class EmailPort(Protocol):
              async def send(self, to: str, subject: str, body: str) -> None: ...


          # Only production adapter registered
          @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
          class SendGridAdapter:
              async def send(self, to: str, subject: str, body: str) -> None:
                  pass


          container = Container()
          container.scan(profile=Profile.TEST)  # Scanning TEST profile

          try:
              container.resolve(EmailPort)  # No TEST adapter!
          except AdapterNotFoundError as e:
              print(e)
              # Output:
              # No adapter registered for port EmailPort with profile 'test'.
              #
              # Available adapters for EmailPort:
              #   SendGridAdapter (profiles: production)
              #
              # Hint: Add an adapter for profile 'test':
              #   @adapter.for_(EmailPort, profile='test')


          # Solution: Add TEST adapter
          @adapter.for_(EmailPort, profile=Profile.TEST)
          class FakeEmailAdapter:
              def __init__(self):
                  self.sent_emails = []

              async def send(self, to: str, subject: str, body: str) -> None:
                  self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

      Missing adapter completely::

          class DatabasePort(Protocol):
              async def query(self, sql: str) -> list[dict]: ...


          @service
          class UserService:
              def __init__(self, db: DatabasePort):  # Depends on DatabasePort
                  self.db = db


          container = Container()
          container.scan(profile=Profile.PRODUCTION)

          try:
              container.resolve(UserService)  # UserService needs DatabasePort
          except AdapterNotFoundError as e:
              print(e)
              # Output:
              # No adapter registered for port DatabasePort with profile 'production'.
              #
              # No adapters registered for DatabasePort.
              #
              # Hint: Register an adapter:
              #   @adapter.for_(DatabasePort, profile='production')
              #   class YourAdapter:
              #       ...


          # Solution: Register adapter
          @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
          class PostgresAdapter:
              async def query(self, sql: str) -> list[dict]:
                  pass

      Universal adapter (works in all profiles)::

          @adapter.for_(LoggerPort, profile=Profile.ALL)  # '*' means all profiles
          class ConsoleLogger:
              def log(self, message: str) -> None:
                  print(message)


          # Works with any profile
          container.scan(profile=Profile.TEST)
          logger = container.resolve(LoggerPort)  # Success!

   Troubleshooting:
       1. **Check profile**: Verify ``container.scan(profile=X)`` matches adapter profile
       2. **List available**: Look at "Available adapters" section in error message
       3. **Check imports**: Ensure adapter module is imported before scan()
       4. **Verify decorator**: Check ``@adapter.for_(Port, profile=...)`` is present
       5. **Use Profile enum**: Prefer ``Profile.TEST`` over string ``'test'``
       6. **Case-insensitive**: 'Test', 'TEST', 'test' all match (normalized to lowercase)

   Best Practices:
       - **Create fake adapters**: Every production adapter needs a test fake
       - **Use Profile.ALL sparingly**: Only for truly universal adapters (logging, etc.)
       - **Fail fast**: Resolve all services at startup to catch missing adapters early
       - **Explicit profiles**: Use ``Profile`` enum instead of strings
       - **Import all adapters**: Use ``container.scan(package="myapp")`` for auto-import

   .. seealso::

      - :class:`dioxide.adapter.adapter` - How to register adapters
      - :class:`dioxide.container.Container.scan` - Profile-based scanning
      - :class:`dioxide.container.Container.resolve` - Where this is raised
      - :class:`dioxide.profile_enum.Profile` - Standard profile values


.. py:exception:: CaptiveDependencyError

   Bases: :py:obj:`Exception`


   Raised when a longer-lived scope depends on a shorter-lived scope.

   This error occurs during ``container.scan()`` when a SINGLETON component
   depends on a REQUEST-scoped component. This is called a "captive dependency"
   because the REQUEST component would be "captured" by the SINGLETON and never
   refreshed, defeating the purpose of request scoping.

   The problem with captive dependencies:
       - SINGLETON lives for the container's lifetime
       - REQUEST should be fresh for each scope
       - If SINGLETON holds REQUEST, the same REQUEST instance is reused forever
       - This violates the REQUEST scope contract and causes subtle bugs

   The error message includes:
       - **Parent component**: The SINGLETON that incorrectly depends on REQUEST
       - **Child component**: The REQUEST-scoped dependency
       - **Explanation**: Why this combination is invalid
       - **Fix suggestions**: How to restructure the dependencies

   When This Occurs:
       - ``container.scan()`` - During dependency graph validation
       - Early detection prevents runtime issues

   Common Causes:
       1. **SINGLETON depends on REQUEST**: Most common case
       2. **Scope mismatch**: Accidentally used wrong scope on decorator
       3. **Transitive dependency**: SINGLETON -> SERVICE -> REQUEST

   Valid Scope Dependencies:
       - SINGLETON -> SINGLETON (OK: same lifetime)
       - SINGLETON -> FACTORY (OK: creates new instance)
       - REQUEST -> SINGLETON (OK: shorter uses longer)
       - REQUEST -> REQUEST (OK: same scope)
       - REQUEST -> FACTORY (OK: creates new instance)
       - FACTORY -> any (OK: always creates new)

   Invalid Scope Dependencies:
       - SINGLETON -> REQUEST (INVALID: captive dependency)

   .. admonition:: Examples

      Captive dependency detected at scan time::

          from dioxide import service, Scope, Container


          @service(scope=Scope.REQUEST)
          class RequestContext:
              def __init__(self):
                  self.request_id = '...'


          @service  # SINGLETON (default)
          class GlobalService:
              def __init__(self, ctx: RequestContext):  # BAD: SINGLETON -> REQUEST
                  self.ctx = ctx


          container = Container()

          try:
              container.scan()
          except CaptiveDependencyError as e:
              print(e)
              # Output:
              # Captive dependency detected: GlobalService (SINGLETON) depends on
              # RequestContext (REQUEST).
              #
              # SINGLETON components cannot depend on REQUEST-scoped components because
              # the REQUEST instance would be captured and never refreshed.
              #
              # Solutions:
              # 1. Change GlobalService to REQUEST scope:
              #    @service(scope=Scope.REQUEST)
              # 2. Change RequestContext to SINGLETON scope (if appropriate)
              # 3. Use a factory/provider pattern to get fresh instances

      Valid dependency structure::

          @service(scope=Scope.SINGLETON)
          class AppConfig:
              pass


          @service(scope=Scope.REQUEST)
          class RequestHandler:
              def __init__(self, config: AppConfig):  # OK: REQUEST -> SINGLETON
                  self.config = config

   Solutions:
       1. **Change parent scope**::

           # Make the parent REQUEST-scoped too
           @service(scope=Scope.REQUEST)
           class RequestService:
               def __init__(self, ctx: RequestContext):
                   self.ctx = ctx

       2. **Change child scope** (if appropriate)::

           # If the child doesn't truly need request scope
           @service  # SINGLETON
           class SharedContext:
               pass

       3. **Use factory/provider pattern**::

           @service  # SINGLETON
           class GlobalService:
               def __init__(self, container: Container):
                   self.container = container

               def get_context(self) -> RequestContext:
                   # Get fresh instance from current scope
                   return current_scope.resolve(RequestContext)

   Best Practices:
       - **Review scope assignments**: Ensure scopes match component lifetimes
       - **Fail fast**: Error at scan() time prevents runtime surprises
       - **Draw dependency graph**: Visualize scope relationships
       - **Default to REQUEST**: For components that vary per-request

   .. seealso::

      - :class:`dioxide.scope.Scope` - Scope enum (SINGLETON, REQUEST, FACTORY)
      - :class:`dioxide.container.Container.scan` - Where this error is raised
      - :class:`ScopeError` - For runtime scope errors


.. py:exception:: ScopeError

   Bases: :py:obj:`Exception`


   Raised when scope-related operations fail.

   This error occurs when:
   1. Attempting to resolve a REQUEST-scoped component outside of a scope context
   2. Attempting to create nested scopes (not supported in v0.3.0)
   3. Other scope lifecycle violations

   REQUEST-scoped components require an active scope created via
   ``container.create_scope()``. Attempting to resolve them from the parent
   container or outside any scope context will raise this error.

   The error message includes:
       - **Component type**: Which component couldn't be resolved
       - **Scope requirement**: Why a scope is needed
       - **Fix hint**: How to create a scope context

   When This Occurs:
       - ``container.resolve(RequestScopedType)`` - REQUEST component outside scope
       - ``scope.create_scope()`` - Nested scope attempt (not supported)
       - Other scope lifecycle violations

   Common Causes:
       1. **No scope context**: Resolving REQUEST component from parent container
       2. **Scope not started**: Scope context manager not entered
       3. **Nested scope**: Trying to create scope within another scope

   .. admonition:: Examples

      REQUEST component outside scope::

          from dioxide import service, Scope, Container


          @service(scope=Scope.REQUEST)
          class RequestContext:
              pass


          container = Container()
          container.scan()

          try:
              container.resolve(RequestContext)  # No scope!
          except ScopeError as e:
              print(e)
              # Output:
              # Cannot resolve RequestContext: REQUEST-scoped components require an active scope.
              #
              # Hint: Use container.create_scope() to create a scope context:
              #   async with container.create_scope() as scope:
              #       ctx = scope.resolve(RequestContext)


          # Solution: Create a scope
          async with container.create_scope() as scope:
              ctx = scope.resolve(RequestContext)  # Works!

      Nested scope attempt::

          async with container.create_scope() as outer:
              try:
                  async with outer.create_scope() as inner:  # Nested!
                      pass
              except ScopeError as e:
                  print(e)
                  # Output:
                  # Nested scopes are not supported in v0.3.0

   Best Practices:
       - **Create scope at entry points**: Web request handlers, CLI commands, background tasks
       - **Pass scope to dependencies**: Or let container inject scoped dependencies
       - **One scope per request**: Don't nest scopes; use one scope per logical request
       - **Use async context manager**: ``async with container.create_scope() as scope:``

   .. seealso::

      - :class:`dioxide.container.Container.create_scope` - How to create scopes
      - :class:`dioxide.container.ScopedContainer` - The scoped container type
      - :class:`dioxide.scope.Scope` - Scope enum including REQUEST


.. py:exception:: ServiceNotFoundError

   Bases: :py:obj:`Exception`


   Raised when a service or component cannot be resolved.

   This error occurs when trying to resolve a service/component that either:
   1. Is not registered in the container (missing ``@service`` decorator), OR
   2. Has dependencies that cannot be resolved (missing adapters or services), OR
   3. Was not imported before ``container.scan()`` was called

   Unlike AdapterNotFoundError (for ports), this error applies to concrete classes
   marked with ``@service`` or ``@component``. The error message helps identify
   whether the service itself is missing or one of its dependencies is unresolvable.

   The error message includes:
       - **Service type**: Which service/component couldn't be resolved
       - **Active profile**: Current profile (if relevant to the error)
       - **Dependencies**: Constructor parameters and their types
       - **Missing dependency**: Which specific dependency failed (if applicable)
       - **Registration hint**: Code example showing how to fix

   When This Occurs:
       - ``container.resolve(ServiceType)`` - Service not registered or has missing deps
       - ``container.resolve(OtherService)`` - OtherService depends on unregistered service
       - ``container.start()`` - Lifecycle component can't be resolved

   Common Causes:
       1. **Missing @service decorator**: Class not decorated, not in registry
       2. **Unresolvable dependency**: Service depends on unregistered port or service
       3. **Not imported**: Service module not imported before scan()
       4. **Profile mismatch on dependency**: Dependency is an adapter with wrong profile
       5. **Typo in type hint**: Constructor parameter references non-existent type

   .. admonition:: Examples

      Service not registered::

          from dioxide import Container


          # Forgot @service decorator!
          class UserService:
              def create_user(self, name: str):
                  pass


          container = Container()
          container.scan()

          try:
              container.resolve(UserService)
          except ServiceNotFoundError as e:
              print(e)
              # Output:
              # Cannot resolve UserService.
              #
              # UserService is not registered in the container.
              #
              # Hint: Register the service:
              #   @service
              #   class UserService:
              #       ...

          # Solution: Add @service decorator
          from dioxide import service


          @service
          class UserService:
              def create_user(self, name: str):
                  pass

      Service with unresolvable dependency::

          from dioxide import service, Container


          @service
          class UserService:
              def __init__(self, db: DatabasePort):  # DatabasePort not registered!
                  self.db = db


          container = Container()
          container.scan()

          try:
              container.resolve(UserService)
          except ServiceNotFoundError as e:
              print(e)
              # Output:
              # Cannot resolve UserService.
              #
              # UserService has dependencies: db: DatabasePort
              #
              # One or more dependencies could not be resolved.
              # Check that all dependencies are registered with @service or @adapter.for_().

          # Solution: Register adapter for DatabasePort
          from dioxide import adapter, Profile


          @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
          class PostgresAdapter:
              async def query(self, sql: str) -> list[dict]:
                  pass

      Service with multiple dependencies::

          @service
          class NotificationService:
              def __init__(self, email: EmailPort, sms: SMSPort, db: DatabasePort):
                  self.email = email
                  self.sms = sms
                  self.db = db

          # If any dependency is missing, error shows ALL dependencies
          try:
              container.resolve(NotificationService)
          except ServiceNotFoundError as e:
              # Shows: email: EmailPort, sms: SMSPort, db: DatabasePort
              # Helps identify which specific dependency is missing

      Circular dependency (non-lifecycle)::

          @service
          class ServiceA:
              def __init__(self, b: 'ServiceB'):  # Forward reference
                  self.b = b


          @service
          class ServiceB:
              def __init__(self, a: ServiceA):
                  self.a = a


          # This will cause RecursionError during resolution
          # (CircularDependencyError only applies to @lifecycle components)
          try:
              container.resolve(ServiceA)
          except RecursionError:
              # Redesign to break circular dependency
              pass

   Troubleshooting:
       1. **Check decorator**: Verify ``@service`` or ``@component`` is present
       2. **Verify imports**: Ensure service module is imported before scan()
       3. **Check dependencies**: Look at "has dependencies" section in error message
       4. **Resolve dependencies first**: Manually resolve each dependency to find which one fails
       5. **Check type hints**: Ensure constructor parameters have correct type annotations
       6. **Profile mismatch**: If dependency is a port, check adapter profile matches
       7. **Forward references**: Use string quotes for forward references: ``'ServiceB'``

   Best Practices:
       - **Fail fast**: Resolve all services at startup to catch missing registrations early
       - **Integration tests**: Test that all services can be resolved in each profile
       - **Explicit imports**: Import all service modules before calling scan()
       - **Use scan(package="myapp")**: Auto-import all modules in a package
       - **Type hints required**: Constructor parameters must have type annotations
       - **Check profiles**: Dependency adapters must match active profile

   .. seealso::

      - :class:`dioxide.services.service` - How to register services
      - :class:`dioxide.adapter.adapter` - How to register adapters (for dependencies)
      - :class:`dioxide.container.Container.scan` - Auto-discovery and registration
      - :class:`dioxide.container.Container.resolve` - Where this is raised
      - :class:`AdapterNotFoundError` - For port resolution errors


.. py:function:: lifecycle(cls)

   Mark a class for lifecycle management with initialization and cleanup.

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

   :param cls: The class to mark for lifecycle management. Must implement both
               ``initialize()`` and ``dispose()`` methods as async coroutines.

   :returns: The decorated class with ``_dioxide_lifecycle = True`` attribute set.
             The class can be used normally and will be discovered by the container.

   :raises TypeError: If the class does not implement ``initialize()`` method.
   :raises TypeError: If ``initialize()`` is not an async coroutine function.
   :raises TypeError: If the class does not implement ``dispose()`` method.
   :raises TypeError: If ``dispose()`` is not an async coroutine function.

   .. admonition:: Examples

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

   .. seealso::

      - :class:`dioxide.container.Container.start` - Initialize all lifecycle components
      - :class:`dioxide.container.Container.stop` - Dispose all lifecycle components
      - :class:`dioxide.adapter.adapter` - For marking infrastructure adapters
      - :class:`dioxide.services.service` - For marking core domain services


.. py:class:: Profile

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Profile specification for adapters.

   Profiles determine which adapter implementations are active
   for a given environment. The Profile enum provides standard
   environment profiles used throughout dioxide for adapter selection.

   .. attribute:: PRODUCTION

      Production environment profile

   .. attribute:: TEST

      Test environment profile

   .. attribute:: DEVELOPMENT

      Development environment profile

   .. attribute:: STAGING

      Staging environment profile

   .. attribute:: CI

      Continuous integration environment profile

   .. attribute:: ALL

      Universal profile - available in all environments

   .. admonition:: Examples

      >>> Profile.PRODUCTION
      <Profile.PRODUCTION: 'production'>
      >>> Profile.PRODUCTION.value
      'production'
      >>> str(Profile.TEST)
      'test'
      >>> Profile('production') == Profile.PRODUCTION
      True


   .. py:attribute:: PRODUCTION
      :value: 'production'



   .. py:attribute:: TEST
      :value: 'test'



   .. py:attribute:: DEVELOPMENT
      :value: 'development'



   .. py:attribute:: STAGING
      :value: 'staging'



   .. py:attribute:: CI
      :value: 'ci'



   .. py:attribute:: ALL
      :value: '*'



.. py:class:: Scope

   Bases: :py:obj:`str`, :py:obj:`enum.Enum`


   Component lifecycle scope.

   Defines how instances of a component are created and cached:

   - SINGLETON: One shared instance for the lifetime of the container.
     The factory is called once and the result is cached. Subsequent
     resolve() calls return the same instance.

   - FACTORY: New instance created on each resolve() call. The factory
     is invoked every time the component is requested, creating a fresh
     instance.

   .. admonition:: Example

      >>> from dioxide import Container, component, Scope
      >>>
      >>> @component  # Default: SINGLETON scope
      ... class Database:
      ...     pass
      >>>
      >>> @component(scope=Scope.FACTORY)
      ... class RequestHandler:
      ...     request_id: int = 0
      ...
      ...     def __init__(self):
      ...         RequestHandler.request_id += 1
      ...         self.id = RequestHandler.request_id
      >>>
      >>> container = Container()
      >>> container.scan()
      >>>
      >>> # Singleton: same instance every time
      >>> db1 = container.resolve(Database)
      >>> db2 = container.resolve(Database)
      >>> assert db1 is db2
      >>>
      >>> # Factory: new instance every time
      >>> handler1 = container.resolve(RequestHandler)
      >>> handler2 = container.resolve(RequestHandler)
      >>> assert handler1 is not handler2
      >>> assert handler1.id != handler2.id


   .. py:attribute:: SINGLETON
      :value: 'singleton'


      One shared instance for the lifetime of the container.

      The component factory is called once and the result is cached.
      All subsequent resolve() calls return the same instance.

      Use for:
      - Database connections
      - Configuration objects
      - Services with shared state
      - Expensive-to-create objects


   .. py:attribute:: FACTORY
      :value: 'factory'


      New instance created on each resolve() call.

      The component factory is invoked every time the component is
      requested, creating a fresh instance.

      Use for:
      - Request handlers
      - Transient data objects
      - Stateful components that shouldn't be shared
      - Objects with per-request lifecycle


   .. py:attribute:: REQUEST
      :value: 'request'


      New instance created per request scope.

      Similar to FACTORY but intended for request-scoped contexts like
      web frameworks where the same instance should be reused within a
      single request but fresh instances created for each new request.

      Use for:
      - Request-scoped services in web frameworks
      - Per-request database sessions
      - Request context objects
      - User authentication/authorization state per request

      Note: Request scope behavior requires integration with a request
      context provider (e.g., FastAPI dependencies, Flask request context).
      Without such integration, REQUEST scope behaves like FACTORY.


.. py:function:: service(cls: type[T]) -> type[T]
                 service(*, scope: dioxide.scope.Scope = Scope.SINGLETON) -> collections.abc.Callable[[type[T]], type[T]]

   Mark a class as a core domain service.

   Services are components that represent core business logic.
   They are available in all profiles (production, test, development) and
   support automatic dependency injection.

   This is a specialized form of @component that:
   - Uses SINGLETON scope by default (one shared instance)
   - Can use REQUEST scope for per-request instances
   - Does not require profile specification (available everywhere)
   - Represents core domain logic in hexagonal architecture

   Usage:
       Basic service (SINGLETON by default):
           >>> from dioxide import service
           >>>
           >>> @service
           ... class UserService:
           ...     def create_user(self, name: str) -> dict:
           ...         return {'name': name, 'id': 1}

       Service with dependencies:
           >>> @service
           ... class EmailService:
           ...     pass
           >>>
           >>> @service
           ... class NotificationService:
           ...     def __init__(self, email: EmailService):
           ...         self.email = email

       Request-scoped service:
           >>> from dioxide import service, Scope
           >>>
           >>> @service(scope=Scope.REQUEST)
           ... class RequestContext:
           ...     def __init__(self):
           ...         self.request_id = str(uuid.uuid4())

       Auto-discovery and resolution:
           >>> from dioxide import container
           >>>
           >>> container.scan()
           >>> notifications = container.resolve(NotificationService)
           >>> assert isinstance(notifications.email, EmailService)

   :param cls: The class being decorated (when used without parentheses).
   :param scope: The lifecycle scope for this service. Defaults to SINGLETON.
                 - SINGLETON: One shared instance for the lifetime of the container
                 - REQUEST: One instance per scope (via container.create_scope())
                 - FACTORY: New instance on every resolve()

   :returns: The decorated class with dioxide metadata attached, or a decorator
             function if called with keyword arguments.

   .. note::

      - Services default to SINGLETON scope
      - Services are available in all profiles
      - Dependencies are resolved from constructor (__init__) type hints
      - For profile-specific implementations, use @adapter.for_()


.. py:function:: fresh_container(profile = None, package = None)
   :async:


   Create a fresh, isolated container for testing.

   This context manager creates a new Container instance, scans for components,
   manages lifecycle (start/stop), and ensures complete isolation between tests.

   :param profile: Profile to scan with (e.g., Profile.TEST). If None, scans all profiles.
   :param package: Optional package to scan. If None, scans all registered components.

   :Yields: A fresh Container instance with lifecycle management.

   .. admonition:: Example

      async with fresh_container(profile=Profile.TEST) as container:
          service = container.resolve(UserService)
          # ... test with isolated container
      # Container automatically cleaned up
