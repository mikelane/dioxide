"""Dependency injection container.

The Container class is the heart of dioxide's dependency injection system.
It manages component registration, dependency resolution, and lifecycle scopes.
The container supports both automatic discovery via @component decorators and
manual registration for fine-grained control.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
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
    ServiceNotFoundError,
)

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

    def __init__(self, allowed_packages: list[str] | None = None) -> None:
        """Initialize a new dependency injection container.

        Creates a new container with an empty registry. The container is
        ready to accept registrations via scan() for @component classes
        or via manual registration methods.

        Args:
            allowed_packages: Optional list of package prefixes allowed for scanning.
                If provided, only modules matching these prefixes can be imported.
                This prevents arbitrary code execution via package scanning.
                If None, no validation is performed (backward compatible).
                Example: ['myapp', 'tests.fixtures'] allows 'myapp.services'
                and 'tests.fixtures.mocks' but blocks 'os' or 'sys'.

        Example:
            >>> from dioxide import Container
            >>> container = Container()
            >>> assert container.is_empty()

            Security example:
            >>> # Only allow scanning within your application package
            >>> container = Container(allowed_packages=['myapp', 'tests'])
            >>> container.scan(package='myapp.services')  # OK
            >>> container.scan(package='os')  # Raises ValueError
        """
        self._rust_core = RustContainer()
        self._active_profile: str | None = None  # Track active profile for error messages
        self._allowed_packages = allowed_packages  # Security: restrict scannable packages

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
            AdapterNotFoundError: If the type is a port (Protocol/ABC) and no
                adapter is registered for the current profile.
            ServiceNotFoundError: If the type is a service/component that cannot
                be resolved (not registered or has unresolvable dependencies).

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

    def _build_adapter_not_found_message(self, port_type: type[Any]) -> str:
        """Build helpful error message for missing adapter.

        Args:
            port_type: The port type that couldn't be resolved.

        Returns:
            A detailed error message with context and hints.
        """
        from dioxide.adapter import _adapter_registry

        port_name = port_type.__name__
        profile_str = f" '{self._active_profile}'" if self._active_profile else ' (no profile active)'

        # Find all adapters for this port (across all profiles)
        adapters_for_port = []
        for adapter_class in _adapter_registry:
            if hasattr(adapter_class, '__dioxide_port__'):
                if adapter_class.__dioxide_port__ is port_type:
                    adapter_name = adapter_class.__name__
                    profiles: frozenset[str] = getattr(adapter_class, '__dioxide_profiles__', frozenset())
                    profile_list = ', '.join(sorted(profiles)) if profiles else 'no profiles'
                    adapters_for_port.append(f'{adapter_name} (profiles: {profile_list})')

        if adapters_for_port:
            available_adapters = '\n  '.join(adapters_for_port)
            hint = (
                f'\n\nAvailable adapters for {port_name}:\n  {available_adapters}\n\n'
                f'Hint: Add an adapter for profile{profile_str}:\n'
                f'  @adapter.for_({port_name}, profile={self._active_profile or "your_profile"!r})'
            )
        else:
            hint = (
                f'\n\nNo adapters registered for {port_name}.\n\n'
                f'Hint: Register an adapter:\n'
                f'  @adapter.for_({port_name}, profile={self._active_profile or "your_profile"!r})\n'
                f'  class YourAdapter:\n'
                f'      ...'
            )

        return f'No adapter registered for port {port_name} with profile{profile_str}.{hint}'

    def _build_service_not_found_message(self, service_type: type[Any]) -> str:
        """Build helpful error message for missing service/component.

        Args:
            service_type: The service type that couldn't be resolved.

        Returns:
            A detailed error message with context and hints.
        """
        service_name = service_type.__name__
        profile_str = f" '{self._active_profile}'" if self._active_profile else ''

        # Check if it's decorated with @service or @component
        from dioxide.decorators import _get_registered_components

        registered_components = list(_get_registered_components())
        is_registered = service_type in registered_components

        if is_registered:
            # Service is registered but has unresolvable dependency
            # Try to identify the missing dependency
            try:
                init_signature = inspect.signature(service_type.__init__)
                type_hints = get_type_hints(service_type.__init__, globalns=service_type.__init__.__globals__)
                dependencies = [
                    (param_name, type_hints[param_name].__name__)
                    for param_name in init_signature.parameters
                    if param_name != 'self' and param_name in type_hints
                ]

                if dependencies:
                    deps_str = ', '.join(f'{name}: {type_name}' for name, type_name in dependencies)
                    hint = (
                        f'\n\n{service_name} has dependencies: {deps_str}\n\n'
                        f'One or more dependencies could not be resolved.\n'
                        f'Check that all dependencies are registered with @service or @adapter.for_().'
                    )
                else:
                    hint = f'\n\nCheck the {service_name} constructor dependencies.'
            except (ValueError, AttributeError, NameError):
                hint = f'\n\nCheck the {service_name} constructor dependencies.'
        else:
            # Service is not registered at all
            hint = (
                f'\n\n{service_name} is not registered in the container.\n\n'
                f'Hint: Register the service:\n'
                f'  @service  # or @component\n'
                f'  class {service_name}:\n'
                f'      ...'
            )

        profile_context = f' (active profile: {profile_str})' if profile_str else ''
        return f'Cannot resolve {service_name}{profile_context}.{hint}'

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

    def _import_package(self, package_name: str) -> None:
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
            return

        # Walk all modules in the package (including sub-packages)
        for _importer, modname, _ispkg in pkgutil.walk_packages(
            path=package.__path__,
            prefix=package.__name__ + '.',
            onerror=lambda x: None,  # Silently skip modules that fail to import
        ):
            try:
                importlib.import_module(modname)
            except Exception as e:
                # Log import failures for debugging
                logging.warning(f'Failed to import module {modname}: {e}')
                # Skip modules that fail to import (missing dependencies, etc.)
                pass

    def scan(self, package: str | None = None, profile: str | Profile | None = None) -> None:
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
        from dioxide.adapter import _adapter_registry
        from dioxide.decorators import _get_registered_components
        from dioxide.profile import PROFILE_ATTRIBUTE
        from dioxide.profile_enum import Profile
        from dioxide.scope import Scope

        # Import package modules if package parameter provided
        if package is not None:
            self._import_package(package)

        # Normalize profile to lowercase if provided
        # Handle both Profile enum and string values
        if profile is not None:
            if isinstance(profile, Profile):
                normalized_profile = profile.value.lower()
            else:
                normalized_profile = profile.lower()
        else:
            normalized_profile = None

        # Track active profile for error messages
        self._active_profile = normalized_profile

        # First, scan adapters and detect ambiguous registrations
        port_to_adapters: dict[type[Any], list[type[Any]]] = {}

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

            # Track adapters per port
            if port_class not in port_to_adapters:
                port_to_adapters[port_class] = []
            port_to_adapters[port_class].append(adapter_class)

        # Check for ambiguous registrations (multiple adapters for same port)
        for port_class, adapters in port_to_adapters.items():
            if len(adapters) > 1:
                adapter_names = ', '.join(cls.__name__ for cls in adapters)
                profile_str = f" for profile '{normalized_profile}'" if normalized_profile else ''
                raise ValueError(
                    f'Ambiguous adapter registration for port {port_class.__name__}{profile_str}: '
                    f'multiple adapters found ({adapter_names}). '
                    f'Only one adapter per port+profile combination is allowed.'
                )

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
            except KeyError:
                # Already registered manually - skip it (manual takes precedence)
                pass

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

    def _build_lifecycle_dependency_order(self) -> list[Any]:
        """Build list of lifecycle components in dependency order.

        Returns:
            List of component instances sorted by dependency order (dependencies first).
        """
        from dioxide.adapter import _adapter_registry
        from dioxide.decorators import _get_registered_components

        # Collect all lifecycle component classes
        lifecycle_classes: dict[type[Any], Any] = {}

        # Check registered components (services)
        for component_class in _get_registered_components():
            if hasattr(component_class, '_dioxide_lifecycle'):
                try:
                    instance = self.resolve(component_class)
                    lifecycle_classes[component_class] = instance
                except (AdapterNotFoundError, ServiceNotFoundError):
                    # Component not registered for this profile - skip
                    pass

        # Check adapters - map port class to adapter instance
        adapter_instances: dict[type[Any], Any] = {}
        for adapter_class in _adapter_registry:
            if hasattr(adapter_class, '_dioxide_lifecycle'):
                # Get the port this adapter implements
                port_class = getattr(adapter_class, '__dioxide_port__', None)
                if port_class is not None:
                    try:
                        instance = self.resolve(port_class)
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
                type_hints = get_type_hints(component_class.__init__, globalns=component_class.__init__.__globals__)

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
                    in_degree[node] = in_degree.get(node, 0) + 1

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

            raise CircularDependencyError(f'Circular dependency detected involving: {unprocessed}')

        return sorted_instances

    async def start(self) -> None:
        """Initialize all @lifecycle components in dependency order.

        Resolves all registered components and calls initialize() on those
        decorated with @lifecycle. Components are initialized in dependency
        order (dependencies before their dependents).

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
        # Build dependency-ordered list
        lifecycle_components = self._build_lifecycle_dependency_order()

        # Track initialized components for rollback
        initialized_components: list[Any] = []

        try:
            # Initialize components in dependency order
            for component in lifecycle_components:
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
            raise

    async def stop(self) -> None:
        """Dispose all @lifecycle components in reverse dependency order.

        Calls dispose() on all components decorated with @lifecycle. Components
        are disposed in reverse dependency order (dependents before their
        dependencies).

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
        # Build dependency-ordered list (same as start())
        lifecycle_components = self._build_lifecycle_dependency_order()

        # Dispose components in reverse order (dependents first)
        for component in reversed(lifecycle_components):
            try:
                await component.dispose()
            except Exception as e:
                # Continue disposing other components even if one fails
                import logging

                logging.error(f'Error disposing component {component.__class__.__name__}: {e}')

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


# Global singleton container instance for simplified API
# This provides the MLP-style ergonomic API while keeping Container class
# available for advanced use cases (testing isolation, multi-tenant apps)
container: Container = Container()
