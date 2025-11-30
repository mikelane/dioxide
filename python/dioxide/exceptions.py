"""Custom exception classes for dioxide dependency injection errors.

This module defines descriptive exception classes that provide helpful, actionable
error messages when dependency resolution fails. These exceptions replace generic
KeyError exceptions with detailed information about what went wrong and how to fix it.

dioxide's error messages follow a consistent pattern:
    1. **What failed**: Clear identification of the problem
    2. **Context**: Active profile, available alternatives, dependencies
    3. **Troubleshooting**: Specific guidance on how to fix the issue
    4. **Code examples**: Concrete examples showing the fix

All exceptions are raised during ``container.resolve()`` operations when the
requested type cannot be provided. The exceptions include contextual information
to help you quickly identify and fix configuration issues.

Exception Hierarchy:
    - AdapterNotFoundError: Raised when resolving a port (Protocol/ABC) fails
    - ServiceNotFoundError: Raised when resolving a service/component fails
    - CircularDependencyError: Raised when lifecycle initialization detects cycles

Common Resolution Patterns:

    1. **Missing adapter for profile**::

        # Problem: No TEST adapter for EmailPort
        container.scan(profile=Profile.TEST)
        container.resolve(EmailPort)  # AdapterNotFoundError


        # Solution: Add TEST adapter
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            pass

    2. **Missing service registration**::

        # Problem: UserService not decorated
        class UserService:
            pass


        container.resolve(UserService)  # ServiceNotFoundError


        # Solution: Add @service decorator
        @service
        class UserService:
            pass

    3. **Unresolvable dependency**::

        # Problem: DatabasePort dependency not registered
        @service
        class UserService:
            def __init__(self, db: DatabasePort):
                pass


        container.resolve(UserService)  # ServiceNotFoundError (shows DatabasePort missing)


        # Solution: Register adapter for DatabasePort
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        class PostgresAdapter:
            pass

    4. **Profile mismatch**::

        # Problem: Only PRODUCTION adapter exists, scanning TEST profile
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            pass


        container.scan(profile=Profile.TEST)
        container.resolve(EmailPort)  # AdapterNotFoundError (lists available profiles)


        # Solution: Add TEST profile adapter
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            pass

    5. **Circular dependency in lifecycle**::

        # Problem: A depends on B, B depends on A
        @service
        @lifecycle
        class ServiceA:
            def __init__(self, b: ServiceB):
                pass


        @service
        @lifecycle
        class ServiceB:
            def __init__(self, a: ServiceA):
                pass


        await container.start()  # CircularDependencyError

        # Solution: Break the cycle (use interface, lazy resolution, or redesign)

Error Message Anatomy:
    dioxide error messages include multiple sections to help debugging:

    **AdapterNotFoundError message structure**::

        No adapter registered for port EmailPort with profile 'test'.

        Available adapters for EmailPort:
          SendGridAdapter (profiles: production)
          ConsoleEmailAdapter (profiles: development)

        Hint: Add an adapter for profile 'test':
          @adapter.for_(EmailPort, profile='test')

    **ServiceNotFoundError message structure**::

        Cannot resolve UserService (active profile: 'test').

        UserService has dependencies: db: DatabasePort, email: EmailPort

        One or more dependencies could not be resolved.
        Check that all dependencies are registered with @service or @adapter.for_().

Debugging Strategies:

    1. **Check profile matches**:
        - Verify ``container.scan(profile=X)`` matches adapter profiles
        - Use ``Profile.ALL`` ('*') for universal adapters
        - Check for typos in profile names (case-insensitive)

    2. **Verify decorators**:
        - Services need ``@service`` decorator
        - Adapters need ``@adapter.for_(Port, profile=...)`` decorator
        - Lifecycle components need ``@lifecycle`` decorator
        - Check decorator order: ``@adapter.for_() @lifecycle class ...``

    3. **Inspect dependencies**:
        - Constructor parameters must have type hints
        - Type hints must reference registered types (ports or services)
        - Circular dependencies are not allowed for @lifecycle components

    4. **Check import order**:
        - Decorators execute at import time
        - Call ``container.scan()`` after all modules are imported
        - Or use ``container.scan(package="myapp")`` to auto-import

    5. **Use separate containers for tests**:
        - Create fresh container per test for isolation
        - Scan with ``Profile.TEST`` to activate fake adapters
        - Check that fake adapters are decorated with correct profile

Prevention Tips:
    - **Use type hints**: Enable early detection of missing dependencies
    - **Run mypy**: Static type checking catches port/implementation mismatches
    - **Profile-specific tests**: Verify each profile has required adapters
    - **Integration smoke tests**: Test that production profile resolves all services
    - **Fail fast**: Resolve all services at startup to catch errors early

See Also:
    - :class:`dioxide.container.Container.resolve` - Where exceptions are raised
    - :class:`dioxide.container.Container.scan` - Profile-based scanning
    - :class:`dioxide.adapter.adapter` - For marking adapters
    - :class:`dioxide.services.service` - For marking services
"""

from __future__ import annotations


class AdapterNotFoundError(Exception):
    """Raised when no adapter is registered for a port in the active profile.

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

    Examples:
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

    See Also:
        - :class:`dioxide.adapter.adapter` - How to register adapters
        - :class:`dioxide.container.Container.scan` - Profile-based scanning
        - :class:`dioxide.container.Container.resolve` - Where this is raised
        - :class:`dioxide.profile_enum.Profile` - Standard profile values
    """

    pass


class ServiceNotFoundError(Exception):
    """Raised when a service or component cannot be resolved.

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

    Examples:
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

    See Also:
        - :class:`dioxide.services.service` - How to register services
        - :class:`dioxide.adapter.adapter` - How to register adapters (for dependencies)
        - :class:`dioxide.container.Container.scan` - Auto-discovery and registration
        - :class:`dioxide.container.Container.resolve` - Where this is raised
        - :class:`AdapterNotFoundError` - For port resolution errors
    """

    pass


class ScopeError(Exception):
    """Raised when scope-related operations fail.

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

    Examples:
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

    See Also:
        - :class:`dioxide.container.Container.create_scope` - How to create scopes
        - :class:`dioxide.container.ScopedContainer` - The scoped container type
        - :class:`dioxide.scope.Scope` - Scope enum including REQUEST
    """

    pass


class CaptiveDependencyError(Exception):
    """Raised when a longer-lived scope depends on a shorter-lived scope.

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

    Examples:
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

    See Also:
        - :class:`dioxide.scope.Scope` - Scope enum (SINGLETON, REQUEST, FACTORY)
        - :class:`dioxide.container.Container.scan` - Where this error is raised
        - :class:`ScopeError` - For runtime scope errors
    """

    pass


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected among @lifecycle components.

    This error occurs during ``container.start()`` when @lifecycle components have
    circular dependencies that prevent topological sorting. The container needs to
    determine initialization order (dependencies before dependents), but a cycle
    makes this impossible.

    This error ONLY applies to @lifecycle components during startup. Regular services
    without @lifecycle can have circular dependencies (though not recommended) because
    they're instantiated lazily on-demand, not in dependency order at startup.

    A circular dependency exists when:
        - Component A depends on B
        - Component B depends on C
        - Component C depends on A (cycle!)

    The container cannot determine which component to initialize first because each
    depends on another being already initialized.

    The error message includes:
        - **Unprocessed components**: Set of components involved in the cycle
        - **Context**: Which lifecycle components couldn't be sorted

    When This Occurs:
        - ``await container.start()`` - During lifecycle initialization order calculation
        - ``async with container:`` - When entering the context manager

    Common Causes:
        1. **Direct cycle**: A → B → A
        2. **Indirect cycle**: A → B → C → D → A
        3. **Self-dependency**: Component depends on itself (rare)
        4. **Bidirectional deps**: Two components that need each other

    Examples:
        Direct circular dependency::

            from dioxide import service, lifecycle, Container


            @service
            @lifecycle
            class ServiceA:
                def __init__(self, b: 'ServiceB'):  # Depends on B
                    self.b = b

                async def initialize(self) -> None:
                    pass

                async def dispose(self) -> None:
                    pass


            @service
            @lifecycle
            class ServiceB:
                def __init__(self, a: ServiceA):  # Depends on A - CYCLE!
                    self.a = a

                async def initialize(self) -> None:
                    pass

                async def dispose(self) -> None:
                    pass


            container = Container()
            container.scan()

            try:
                await container.start()
            except CircularDependencyError as e:
                print(e)
                # Output:
                # Circular dependency detected involving: {<ServiceA>, <ServiceB>}

        Indirect circular dependency::

            @service
            @lifecycle
            class CacheService:
                def __init__(self, user_repo: UserRepository):
                    self.user_repo = user_repo


            @service
            @lifecycle
            class UserRepository:
                def __init__(self, db: DatabaseAdapter):
                    self.db = db


            @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
            @lifecycle
            class DatabaseAdapter:
                def __init__(self, cache: CacheService):  # CYCLE!
                    self.cache = cache


            # Cycle: CacheService → UserRepository → DatabaseAdapter → CacheService
            await container.start()  # CircularDependencyError

    Solutions:
        1. **Break dependency with interface**::

            # Instead of depending on concrete class, depend on port
            class CachePort(Protocol):
                def get(self, key: str) -> Any: ...


            @service
            @lifecycle
            class ServiceA:
                def __init__(self, cache: CachePort):  # Depend on abstraction
                    self.cache = cache

        2. **Remove @lifecycle from one component**::

            # If only one component truly needs lifecycle, remove from others
            @service  # No @lifecycle - lazy initialization
            class ServiceB:
                def __init__(self, a: ServiceA):
                    self.a = a


            @service
            @lifecycle  # Only this one has lifecycle
            class ServiceA:
                async def initialize(self) -> None:
                    pass

        3. **Lazy resolution**::

            @service
            @lifecycle
            class ServiceA:
                def __init__(self, container: Container):
                    self.container = container
                    self._b = None

                @property
                def b(self) -> ServiceB:
                    if self._b is None:
                        self._b = self.container.resolve(ServiceB)
                    return self._b

        4. **Redesign to remove cycle**::

            # Extract shared logic to a third service
            @service
            class SharedLogic:
                pass


            @service
            @lifecycle
            class ServiceA:
                def __init__(self, shared: SharedLogic):
                    self.shared = shared


            @service
            @lifecycle
            class ServiceB:
                def __init__(self, shared: SharedLogic):
                    self.shared = shared

    Troubleshooting:
        1. **Identify cycle**: Look at "involving" set in error message
        2. **Map dependencies**: Draw dependency graph on paper
        3. **Find weak link**: Identify which dependency is least essential
        4. **Remove @lifecycle**: Not all components need lifecycle management
        5. **Use abstractions**: Depend on ports instead of concrete classes
        6. **Lazy initialization**: Defer resolution to first use

    Best Practices:
        - **Avoid circular dependencies**: Design for acyclic dependency graphs
        - **Use hexagonal architecture**: Depend on abstractions (ports) at boundaries
        - **Limit @lifecycle**: Only use for components that truly need init/dispose
        - **Dependency injection**: Let container manage dependencies, avoid manual creation
        - **Single Responsibility**: Components with clear responsibilities rarely cycle
        - **Test initialization**: Integration test that calls ``container.start()``

    Note:
        Non-lifecycle services CAN have circular dependencies (though not recommended).
        The container resolves them lazily on-demand. This error ONLY applies to
        @lifecycle components during ``start()`` because they need explicit ordering.

    See Also:
        - :class:`dioxide.lifecycle.lifecycle` - Lifecycle management decorator
        - :class:`dioxide.container.Container.start` - Where this error is raised
        - :class:`dioxide.services.service` - For marking services
        - :class:`dioxide.adapter.adapter` - For marking adapters
    """

    pass
