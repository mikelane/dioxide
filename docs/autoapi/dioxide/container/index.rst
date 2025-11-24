dioxide.container
=================

.. py:module:: dioxide.container

.. autoapi-nested-parse::

   Dependency injection container.

   The Container class is the heart of dioxide's dependency injection system.
   It manages component registration, dependency resolution, and lifecycle scopes.
   The container supports both automatic discovery via @component decorators and
   manual registration for fine-grained control.



Attributes
----------

.. autoapisummary::

   dioxide.container.T
   dioxide.container.container


Classes
-------

.. autoapisummary::

   dioxide.container.Container


Module Contents
---------------

.. py:data:: T

.. py:class:: Container(allowed_packages = None)

   Initialize a new dependency injection container.

   Creates a new container with an empty registry. The container is
   ready to accept registrations via scan() for @component classes
   or via manual registration methods.

   :param allowed_packages: Optional list of package prefixes allowed for scanning.
                            If provided, only modules matching these prefixes can be imported.
                            This prevents arbitrary code execution via package scanning.
                            If None, no validation is performed (backward compatible).
                            Example: ['myapp', 'tests.fixtures'] allows 'myapp.services'
                            and 'tests.fixtures.mocks' but blocks 'os' or 'sys'.

   .. admonition:: Example

      >>> from dioxide import Container
      >>> container = Container()
      >>> assert container.is_empty()

      Security example:
      >>> # Only allow scanning within your application package
      >>> container = Container(allowed_packages=['myapp', 'tests'])
      >>> container.scan(package='myapp.services')  # OK
      >>> container.scan(package='os')  # Raises ValueError


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



.. py:data:: container
   :type:  Container
