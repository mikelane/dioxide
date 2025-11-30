"""Service decorator for core domain logic.

The @service decorator marks classes as core domain logic in hexagonal architecture.
Services represent the business rules layer that sits between ports (interfaces) and
adapters (implementations), containing the core application logic that doesn't depend
on infrastructure details.

Key Characteristics:
    - **Singleton scope**: One shared instance across the application
    - **Profile-agnostic**: Available in ALL profiles (production, test, development)
    - **Depends on ports**: Services depend on Protocols/ABCs, not concrete implementations
    - **Pure business logic**: No knowledge of databases, APIs, or infrastructure
    - **Constructor injection**: Dependencies resolved from __init__ type hints

In hexagonal architecture, services form the hexagon's center - the core domain
that is isolated from external concerns. They depend on ports (abstractions), and
the container injects the appropriate adapters based on the active profile.

Basic Example:
    Core service with port dependencies::

        from typing import Protocol
        from dioxide import service, adapter, Profile


        # Port (interface) - what the service needs
        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...


        class UserRepository(Protocol):
            async def find_by_email(self, email: str) -> User | None: ...
            async def save(self, user: User) -> None: ...


        # Service - core business logic
        @service
        class UserService:
            def __init__(self, email: EmailPort, users: UserRepository):
                # Depends on PORTS, not concrete adapters
                self.email = email
                self.users = users

            async def register_user(self, email_addr: str, name: str) -> User:
                # Pure business logic
                existing = await self.users.find_by_email(email_addr)
                if existing:
                    raise ValueError(f'User {email_addr} already exists')

                user = User(email=email_addr, name=name)
                await self.users.save(user)
                await self.email.send(email_addr, 'Welcome!', f'Hello {name}!')
                return user

Advanced Example:
    Service with multiple dependencies and complex logic::

        @service
        class NotificationService:
            def __init__(self, email: EmailPort, sms: SMSPort, users: UserRepository, clock: ClockPort):
                self.email = email
                self.sms = sms
                self.users = users
                self.clock = clock

            async def send_welcome(self, user_id: int) -> bool:
                user = await self.users.find_by_id(user_id)
                if not user:
                    return False

                # Throttle: Don't send if already sent within 30 days
                if user.last_welcome_sent:
                    elapsed = self.clock.now() - user.last_welcome_sent
                    if elapsed < timedelta(days=30):
                        return False

                # Send notifications
                await self.email.send(user.email, 'Welcome!', '...')
                if user.phone:
                    await self.sms.send(user.phone, 'Welcome to our service!')

                # Update user
                user.last_welcome_sent = self.clock.now()
                await self.users.save(user)
                return True

Testing Example:
    Services are testable with fakes, no mocks needed::

        import pytest
        from dioxide import Container, Profile


        @pytest.fixture
        def container():
            c = Container()
            c.scan(profile=Profile.TEST)  # Activates fake adapters
            return c


        async def test_user_registration(container):
            # Arrange: Get service and fakes
            service = container.resolve(UserService)
            email = container.resolve(EmailPort)  # FakeEmailAdapter
            users = container.resolve(UserRepository)  # InMemoryUserRepository

            # Act: Call real service
            user = await service.register_user('alice@example.com', 'Alice')

            # Assert: Check real observable outcomes
            assert user.email == 'alice@example.com'
            assert len(email.sent_emails) == 1
            assert email.sent_emails[0]['to'] == 'alice@example.com'
            saved_user = await users.find_by_email('alice@example.com')
            assert saved_user is not None

See Also:
    - :class:`dioxide.adapter.adapter` - For marking boundary implementations
    - :class:`dioxide.profile_enum.Profile` - Standard profile values
    - :class:`dioxide.container.Container` - For dependency resolution
    - :class:`dioxide.lifecycle.lifecycle` - For initialization/cleanup
"""

from collections.abc import Callable
from typing import (
    TypeVar,
    overload,
)

from dioxide._registry import _component_registry
from dioxide.scope import Scope

T = TypeVar('T')


@overload
def service(cls: type[T]) -> type[T]: ...


@overload
def service(
    *,
    scope: Scope = Scope.SINGLETON,
) -> Callable[[type[T]], type[T]]: ...


def service(
    cls: type[T] | None = None,
    *,
    scope: Scope = Scope.SINGLETON,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Mark a class as a core domain service.

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

    Args:
        cls: The class being decorated (when used without parentheses).
        scope: The lifecycle scope for this service. Defaults to SINGLETON.
            - SINGLETON: One shared instance for the lifetime of the container
            - REQUEST: One instance per scope (via container.create_scope())
            - FACTORY: New instance on every resolve()

    Returns:
        The decorated class with dioxide metadata attached, or a decorator
        function if called with keyword arguments.

    Note:
        - Services default to SINGLETON scope
        - Services are available in all profiles
        - Dependencies are resolved from constructor (__init__) type hints
        - For profile-specific implementations, use @adapter.for_()
    """

    def decorator(cls_to_decorate: type[T]) -> type[T]:
        # Store DI metadata on the class
        cls_to_decorate.__dioxide_scope__ = scope  # type: ignore[attr-defined]
        cls_to_decorate.__dioxide_profiles__ = frozenset(['*'])  # type: ignore[attr-defined]  # Available in all profiles
        # Add to global registry for auto-discovery
        _component_registry.add(cls_to_decorate)
        return cls_to_decorate

    # Handle both @service and @service(scope=...) syntaxes
    if cls is not None:
        # Called as @service without parentheses
        return decorator(cls)
    else:
        # Called as @service(scope=...) with parentheses
        return decorator
