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

   /autoapi/dioxide/adapter/index
   /autoapi/dioxide/container/index
   /autoapi/dioxide/exceptions/index
   /autoapi/dioxide/lifecycle/index
   /autoapi/dioxide/profile_enum/index
   /autoapi/dioxide/scope/index
   /autoapi/dioxide/services/index


Attributes
----------

.. autoapisummary::

   dioxide.adapter
   dioxide.container


Exceptions
----------

.. autoapisummary::

   dioxide.AdapterNotFoundError
   dioxide.ServiceNotFoundError


Classes
-------

.. autoapisummary::

   dioxide.Container
   dioxide.Profile
   dioxide.Scope


Functions
---------

.. autoapisummary::

   dioxide.lifecycle
   dioxide.service


Package Contents
----------------

.. py:data:: adapter

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



.. py:data:: container
   :type:  Container

.. py:exception:: AdapterNotFoundError

   Bases: :py:obj:`Exception`


   Raised when no adapter is registered for a port.

   This error occurs when trying to resolve a Protocol/ABC (port) but no
   concrete implementation (adapter) is registered for the current profile.

   The error message includes:
   - The port type that couldn't be resolved
   - The active profile
   - List of available adapters (if any) for other profiles
   - Hint for how to register an adapter

   .. admonition:: Example

      >>> from dioxide import Container, Profile, adapter
      >>> from typing import Protocol
      >>>
      >>> class EmailPort(Protocol):
      ...     async def send(self, to: str, subject: str, body: str) -> None: ...
      >>>
      >>> @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
      ... class SendGridAdapter:
      ...     async def send(self, to: str, subject: str, body: str) -> None:
      ...         pass
      >>>
      >>> container = Container()
      >>> container.scan(profile=Profile.TEST)  # No TEST adapter
      >>>
      >>> try:
      ...     container.resolve(EmailPort)
      ... except AdapterNotFoundError as e:
      ...     print(e)  # Shows available adapters and profile mismatch


.. py:exception:: ServiceNotFoundError

   Bases: :py:obj:`Exception`


   Raised when a service or component cannot be resolved.

   This error occurs when:
   1. Trying to resolve an unregistered type
   2. A service depends on an unresolvable dependency
   3. The dependency chain is broken

   The error message includes:
   - The service/component type that failed to resolve
   - The missing dependency (if applicable)
   - The active profile
   - List of available types in the container
   - Hint for how to register the service

   .. admonition:: Example

      >>> from dioxide import Container, service
      >>>
      >>> @service
      >>> class UserService:
      ...     def __init__(self, db: DatabasePort):  # DatabasePort not registered
      ...         self.db = db
      >>>
      >>> container = Container()
      >>> container.scan(profile='test')
      >>>
      >>> try:
      ...     container.resolve(UserService)
      ... except ServiceNotFoundError as e:
      ...     print(e)  # Shows missing DatabasePort dependency


.. py:function:: lifecycle(cls)

   Mark a class as having lifecycle management.

   Components decorated with @lifecycle must implement:
   - async def initialize(self) -> None: Called at container startup
   - async def dispose(self) -> None: Called at container shutdown

   :param cls: The class to mark for lifecycle management

   :returns: The class with _dioxide_lifecycle attribute set

   :raises TypeError: If the class does not implement initialize() method

   .. admonition:: Example

      >>> @service
      ... @lifecycle
      ... class Database:
      ...     async def initialize(self) -> None:
      ...         self.engine = create_async_engine(...)
      ...
      ...     async def dispose(self) -> None:
      ...         await self.engine.dispose()


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


.. py:function:: service(cls)

   Mark a class as a core domain service.

   Services are singleton components that represent core business logic.
   They are available in all profiles (production, test, development) and
   support automatic dependency injection.

   This is a specialized form of @component that:
   - Always uses SINGLETON scope (one shared instance)
   - Does not require profile specification (available everywhere)
   - Represents core domain logic in hexagonal architecture

   Usage:
       Basic service:
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

       Auto-discovery and resolution:
           >>> from dioxide import container
           >>>
           >>> container.scan()
           >>> notifications = container.resolve(NotificationService)
           >>> assert isinstance(notifications.email, EmailService)

   :param cls: The class being decorated.

   :returns: The decorated class with dioxide metadata attached. The class can be
             used normally and will be discovered by Container.scan().

   .. note::

      - Services are always SINGLETON scope
      - Services are available in all profiles
      - Dependencies are resolved from constructor (__init__) type hints
      - For profile-specific implementations, use @component with @profile
