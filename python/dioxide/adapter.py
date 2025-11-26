"""Adapter decorator for hexagonal architecture.

The @adapter decorator enables marking concrete implementations (adapters) for
Protocol/ABC ports with explicit profile associations, supporting hexagonal
(ports-and-adapters) architecture patterns.

In hexagonal architecture:
    - **Ports** are abstract interfaces (Protocols/ABCs) that define contracts
    - **Adapters** are concrete implementations that fulfill port contracts
    - **Profiles** determine which adapters are active in different environments

The @adapter decorator makes this pattern explicit and type-safe, allowing you
to swap implementations based on environment (production vs test vs development)
without changing business logic.

Basic Example:
    Define a port and multiple adapters for different profiles::

        from typing import Protocol
        from dioxide import adapter, Profile


        # Port (interface) - defines the contract
        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...


        # Production adapter - real SendGrid implementation
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            def __init__(self, config: AppConfig):
                self.api_key = config.sendgrid_api_key

            async def send(self, to: str, subject: str, body: str) -> None:
                # Real SendGrid API calls
                async with httpx.AsyncClient() as client:
                    await client.post(
                        'https://api.sendgrid.com/v3/mail/send',
                        headers={'Authorization': f'Bearer {self.api_key}'},
                        json={'to': to, 'subject': subject, 'body': body},
                    )


        # Test adapter - fast fake for testing
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            async def send(self, to: str, subject: str, body: str) -> None:
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})


        # Development adapter - console logging
        @adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
        class ConsoleEmailAdapter:
            async def send(self, to: str, subject: str, body: str) -> None:
                print(f'📧 Email to {to}: {subject}')

Advanced Example:
    Multiple profiles and lifecycle management::

        from dioxide import adapter, Profile, lifecycle


        # Adapter available in multiple profiles
        @adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
        class InMemoryCacheAdapter:
            def __init__(self):
                self._cache = {}

            def get(self, key: str) -> Any | None:
                return self._cache.get(key)

            def set(self, key: str, value: Any) -> None:
                self._cache[key] = value


        # Production adapter with lifecycle management
        @adapter.for_(CachePort, profile=Profile.PRODUCTION)
        @lifecycle
        class RedisCacheAdapter:
            def __init__(self, config: AppConfig):
                self.config = config
                self.redis = None

            async def initialize(self) -> None:
                self.redis = await aioredis.create_redis_pool(self.config.redis_url)

            async def dispose(self) -> None:
                if self.redis:
                    self.redis.close()
                    await self.redis.wait_closed()

            async def get(self, key: str) -> Any | None:
                return await self.redis.get(key)

            async def set(self, key: str, value: Any) -> None:
                await self.redis.set(key, value)

Container Resolution:
    The container activates profile-specific adapters::

        from dioxide import container, Profile

        # Production container - activates SendGridAdapter
        container.scan(profile=Profile.PRODUCTION)
        email = container.resolve(EmailPort)  # Returns SendGridAdapter

        # Test container - activates FakeEmailAdapter
        test_container = Container()
        test_container.scan(profile=Profile.TEST)
        email = test_container.resolve(EmailPort)  # Returns FakeEmailAdapter

See Also:
    - :class:`dioxide.services.service` - For marking core domain logic
    - :class:`dioxide.profile_enum.Profile` - Standard profile enum values
    - :class:`dioxide.lifecycle.lifecycle` - For lifecycle management
    - :class:`dioxide.container.Container` - For profile-based resolution
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from dioxide.scope import Scope

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar('T')

# Global registry for adapter-decorated classes
_adapter_registry: set[type[Any]] = set()


class AdapterDecorator:
    """Main decorator class with .for_() method for marking adapters.

    This decorator enables hexagonal architecture by explicitly marking
    concrete implementations (adapters) for abstract ports (Protocols/ABCs)
    with environment-specific profiles.

    The decorator requires explicit profile association to make deployment
    configuration visible at the seams.
    """

    def for_(
        self,
        port: type[Any],
        *,
        profile: str | list[str] = '*',
        scope: Scope = Scope.SINGLETON,
    ) -> Callable[[type[T]], type[T]]:
        """Register an adapter for a port with profile(s) and optional scope.

        This method marks a concrete class as an adapter implementation for an
        abstract port (Protocol/ABC), associated with one or more environment profiles.
        The adapter will be activated when the container scans with a matching profile.

        The decorator:
            1. Stores port, profile, and scope metadata on the class
            2. Registers the adapter in the global registry for auto-discovery
            3. Uses the specified scope (default: SINGLETON) for instance lifecycle
            4. Normalizes profile names to lowercase for consistent matching

        Args:
            port: The Protocol or ABC that this adapter implements. This defines
                the interface contract that the adapter must fulfill. Services depend
                on this port type, and the container will inject the active adapter.
            profile: Profile name(s) determining when this adapter is active. Can be:

                - Single string: ``profile='production'``
                - List of strings: ``profile=['test', 'development']``
                - Profile enum: ``profile=Profile.PRODUCTION``
                - List of enums: ``profile=[Profile.TEST, Profile.DEVELOPMENT]``
                - Universal: ``profile='*'`` or ``profile=Profile.ALL`` (all profiles)

                Profile names are normalized to lowercase for case-insensitive matching.
                Default is '*' (available in all profiles).
            scope: Instance lifecycle scope. Controls how instances are created:

                - ``Scope.SINGLETON`` (default): Same instance returned on every
                  resolution. Use for stateless adapters or shared resources.
                - ``Scope.FACTORY``: New instance created on each resolution.
                  Use for test fakes that need fresh state per resolution,
                  or adapters that should not share state between callers.

        Returns:
            Decorator function that marks the class as an adapter. The decorated
            class can be used normally and will be discovered by Container.scan().

        Raises:
            TypeError: If the decorated class does not implement the port's required
                methods (detected at runtime during resolution).

        Examples:
            Single profile (production)::

                @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
                class SendGridAdapter:
                    async def send(self, to: str, subject: str, body: str) -> None:
                        # Real SendGrid implementation
                        pass

            Multiple profiles (test and development)::

                @adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
                class FakeEmailAdapter:
                    def __init__(self):
                        self.sent_emails = []

                    async def send(self, to: str, subject: str, body: str) -> None:
                        self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

            Universal adapter (all profiles)::

                @adapter.for_(LoggerPort, profile=Profile.ALL)
                class ConsoleLogger:
                    def log(self, message: str) -> None:
                        print(message)

            With constructor dependencies::

                @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
                class PostgresAdapter:
                    def __init__(self, config: AppConfig):
                        # Dependencies are automatically injected
                        self.config = config

                    async def query(self, sql: str) -> list[dict]:
                        # PostgreSQL implementation
                        pass

            With lifecycle management::

                @adapter.for_(CachePort, profile=Profile.PRODUCTION)
                @lifecycle
                class RedisAdapter:
                    async def initialize(self) -> None:
                        self.redis = await aioredis.create_redis_pool(...)

                    async def dispose(self) -> None:
                        self.redis.close()

            With FACTORY scope (new instance per resolution)::

                @adapter.for_(EmailPort, profile=Profile.TEST, scope=Scope.FACTORY)
                class FreshFakeEmailAdapter:
                    def __init__(self):
                        self.sent_emails = []  # Fresh state each time

                    async def send(self, to: str, subject: str, body: str) -> None:
                        self.sent_emails.append({'to': to, 'subject': subject, 'body': body})


                # Each resolution returns a new instance with empty sent_emails
                email1 = container.resolve(EmailPort)
                email2 = container.resolve(EmailPort)
                assert email1 is not email2  # Different instances

        See Also:
            - :class:`dioxide.scope.Scope` - SINGLETON vs FACTORY scope
            - :class:`dioxide.profile_enum.Profile` - Standard profile enum values
            - :class:`dioxide.container.Container.scan` - Profile-based scanning
            - :class:`dioxide.lifecycle.lifecycle` - For initialization/cleanup
            - :class:`dioxide.services.service` - For core domain logic
        """

        def decorator(cls: type[T]) -> type[T]:
            # Normalize profile to set of lowercase strings
            if isinstance(profile, str):
                profiles = {profile.lower()}
            else:
                # Deduplicate and normalize to lowercase
                profiles = {p.lower() for p in profile}

            # Store metadata on class
            cls.__dioxide_port__ = port  # type: ignore[attr-defined]
            cls.__dioxide_profiles__ = frozenset(profiles)  # type: ignore[attr-defined]
            cls.__dioxide_scope__ = scope  # type: ignore[attr-defined]

            # Register with global registry
            _adapter_registry.add(cls)

            return cls

        return decorator


# Global singleton instance for use as decorator
adapter = AdapterDecorator()

__all__ = ['AdapterDecorator', 'adapter']
