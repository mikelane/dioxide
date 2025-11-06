"""Dependency injection container.

The Container class is the heart of dioxide's dependency injection system.
It manages component registration, dependency resolution, and lifecycle scopes.
The container supports both automatic discovery via @component decorators and
manual registration for fine-grained control.
"""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from dioxide._dioxide_core import Container as RustContainer

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

    def __init__(self) -> None:
        """Initialize a new dependency injection container.

        Creates a new container with an empty registry. The container is
        ready to accept registrations via scan() for @component classes
        or via manual registration methods.

        Example:
            >>> from dioxide import Container
            >>> container = Container()
            >>> assert container.is_empty()
        """
        self._rust_core = RustContainer()

    def register_instance(self, component_type: type[T], instance: T) -> None:
        """Register a pre-created instance for a given type.

        This method registers an already-instantiated object that will be
        returned whenever the type is resolved. Useful for registering
        configuration objects or external dependencies.

        Args:
            component_type: The type to register. This is used as the lookup
                key when resolving dependencies.
            instance: The pre-created instance to return for this type. Must
                be an instance of component_type or a compatible type.

        Raises:
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
        """
        self._rust_core.register_instance(component_type, instance)

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
        return self._rust_core.resolve(component_type)

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

    def scan(self) -> None:
        """Discover and register all @component decorated classes.

        Scans the global component registry for all classes decorated with
        @component and registers them with the container. Dependencies are
        automatically resolved based on constructor type hints.

        This is the primary method for setting up the container in a
        declarative style. Call it once after all components are imported.

        Registration behavior:
            - SINGLETON scope (default): Creates singleton factory with caching
            - FACTORY scope: Creates transient factory for new instances
            - Manual registrations take precedence over @component decorators
            - Already-registered types are silently skipped

        Example:
            >>> from dioxide import Container, component, Scope
            >>>
            >>> @component
            ... class Database:
            ...     def __init__(self):
            ...         self.connected = True
            >>>
            >>> @component
            ... class UserRepository:
            ...     def __init__(self, db: Database):
            ...         self.db = db
            >>>
            >>> @component(scope=Scope.FACTORY)
            ... class RequestHandler:
            ...     def __init__(self, repo: UserRepository):
            ...         self.repo = repo
            >>>
            >>> container = Container()
            >>> container.scan()
            >>>
            >>> # All dependencies auto-injected
            >>> handler = container.resolve(RequestHandler)
            >>> assert handler.repo.db.connected

        Note:
            - Ensure all component classes are imported before calling scan()
            - Constructor dependencies must have type hints
            - Circular dependencies will cause infinite recursion
            - Manual registrations (register_*) take precedence over scan()
        """
        from dioxide.decorators import _get_registered_components
        from dioxide.scope import Scope

        for component_class in _get_registered_components():
            # Create a factory that auto-injects dependencies
            factory = self._create_auto_injecting_factory(component_class)

            # Check the scope
            scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

            try:
                if scope == Scope.SINGLETON:
                    # Register as singleton factory (Rust will cache the result)
                    self.register_singleton_factory(component_class, factory)
                else:
                    # Register as transient factory (Rust creates new instance each time)
                    self.register_transient_factory(component_class, factory)
            except KeyError:
                # Already registered manually - skip it (manual takes precedence)
                pass

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
            # Pass the class's module globals to resolve forward references
            type_hints = get_type_hints(cls.__init__, globalns=cls.__init__.__globals__)
        except (ValueError, AttributeError, NameError):
            # No __init__ or no type hints, or can't resolve type hints - just instantiate directly
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
