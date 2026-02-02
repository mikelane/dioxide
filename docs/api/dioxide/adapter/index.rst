dioxide.adapter
===============

.. py:module:: dioxide.adapter

.. autoapi-nested-parse::

   Adapter decorator for hexagonal architecture.

   The @adapter decorator enables marking concrete implementations (adapters) for
   Protocol/ABC ports with explicit profile associations, supporting hexagonal
   (ports-and-adapters) architecture patterns.

   When to Use @adapter.for_():
       Use @adapter.for_() when you are implementing a **boundary component** that:

       - **Connects to external systems** (databases, APIs, filesystems, network)
       - Needs **different implementations per profile** (production, test, development)
       - **Implements a port** (Protocol/ABC) contract
       - Should be **swappable** without changing business logic

       Do NOT use @adapter.for_() if:

       - The component is core business logic (use @service instead)
       - The component should be the same across all environments (use @service)
       - You're not implementing a port interface

       **Decision Tree**::

           Do you need different implementations based on profile (test/prod/dev)?
           |-- YES --> Define a Port (Protocol) + use @adapter.for_(Port, profile=...)
           |-- NO  --> Use @service

           Does this component talk to external systems (DB, network, filesystem)?
           |-- YES --> Port + @adapter.for_() (allows faking in tests)
           |-- NO  --> Probably @service

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

   .. seealso::

      - :class:`dioxide.services.service` - For marking core domain logic
      - :class:`dioxide.profile_enum.Profile` - Extensible profile identifiers
      - :class:`dioxide.lifecycle.lifecycle` - For lifecycle management
      - :class:`dioxide.container.Container` - For profile-based resolution



Attributes
----------

.. autoapisummary::

   dioxide.adapter.adapter


Classes
-------

.. autoapisummary::

   dioxide.adapter.AdapterDecorator


Module Contents
---------------

.. py:class:: AdapterDecorator

   Main decorator class with .for_() method for marking adapters.

   This decorator enables hexagonal architecture by explicitly marking
   concrete implementations (adapters) for abstract ports (Protocols/ABCs)
   with environment-specific profiles.

   The decorator requires explicit profile association to make deployment
   configuration visible at the seams.


   .. py:method:: for_(port, *, profile = Profile.ALL, scope = Scope.SINGLETON, multi = False, priority = 0)

      Register an adapter for a port with profile(s) and optional scope.

      This method marks a concrete class as an adapter implementation for an
      abstract port (Protocol/ABC), associated with one or more environment profiles.
      The adapter will be activated when the container scans with a matching profile.

      The decorator:
          1. Stores port, profile, scope, multi, and priority metadata on the class
          2. Registers the adapter in the global registry for auto-discovery
          3. Uses the specified scope (default: SINGLETON) for instance lifecycle
          4. Normalizes profile names to lowercase for consistent matching

      :param port: The Protocol or ABC that this adapter implements. This defines
                   the interface contract that the adapter must fulfill. Services depend
                   on this port type, and the container will inject the active adapter.
      :param profile: Profile value(s) determining when this adapter is active.

                      **Canonical patterns (recommended)**:

                      - Single enum: ``profile=Profile.PRODUCTION``
                      - List of enums: ``profile=[Profile.TEST, Profile.DEVELOPMENT]``
                      - Universal: ``profile=Profile.ALL`` (all profiles)

                      **Deprecated patterns** (emit DeprecationWarning):

                      - Known string: ``profile='production'`` - use ``Profile.PRODUCTION`` instead
                      - Wildcard string: ``profile='*'`` - use ``Profile.ALL`` instead

                      **Custom profiles** (allowed without warning):

                      - Custom string: ``profile='integration'`` - no enum equivalent, allowed
                      - Custom list: ``profile=['perf', 'load']`` - custom profiles are extensible

                      Profile names are normalized to lowercase for case-insensitive matching.
                      Default is ``Profile.ALL`` (available in all profiles).
      :param scope: Instance lifecycle scope. Controls how instances are created:

                    - ``Scope.SINGLETON`` (default): Same instance returned on every
                      resolution. Use for stateless adapters or shared resources.
                    - ``Scope.FACTORY``: New instance created on each resolution.
                      Use for test fakes that need fresh state per resolution,
                      or adapters that should not share state between callers.
      :param multi: Enable multi-binding mode for plugin patterns. When ``True``,
                    multiple adapters can be registered for the same port, and they
                    can be injected as a collection using ``list[Port]`` type hint.
                    Default is ``False`` (single adapter per port per profile).

                    Multi-binding is useful for plugin systems where multiple
                    implementations should be collected rather than selecting one.
                    A port must be either single-binding OR multi-binding, not both.
      :param priority: Ordering priority for multi-bindings (only used when
                       ``multi=True``). Lower values are instantiated first. Default is 0.
                       Use negative values to run before default, positive to run after.

      :returns: Decorator function that marks the class as an adapter. The decorated
                class can be used normally and will be discovered by Container.scan().

      :raises TypeError: If the decorated class does not implement the port's required
          methods (detected at runtime during resolution).
      :raises ValueError: At scan time if a port has both single and multi adapters.

      .. admonition:: Examples

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

             # Recommended order (but both work identically)
             @adapter.for_(CachePort, profile=Profile.PRODUCTION)
             @lifecycle
             class RedisAdapter:
                 async def initialize(self) -> None:
                     self.redis = await aioredis.create_redis_pool(...)

                 async def dispose(self) -> None:
                     self.redis.close()

         Note: Decorator order is flexible - dioxide decorators only add metadata
         attributes, so ``@lifecycle @adapter.for_(...)`` also works. We recommend
         ``@adapter.for_() @lifecycle`` for consistency across the codebase.

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

         Multi-binding for plugin systems::

             class PluginPort(Protocol):
                 def process(self, data: str) -> str: ...


             @adapter.for_(PluginPort, multi=True, priority=10)
             class ValidationPlugin:
                 def process(self, data: str) -> str:
                     return validate(data)


             @adapter.for_(PluginPort, multi=True, priority=20)
             class TransformPlugin:
                 def process(self, data: str) -> str:
                     return transform(data)


             @service
             class DataProcessor:
                 def __init__(self, plugins: list[PluginPort]):
                     self.plugins = plugins  # All plugins, ordered by priority

                 def run(self, data: str) -> str:
                     for plugin in self.plugins:
                         data = plugin.process(data)
                     return data


             container = Container()
             container.scan(profile=Profile.PRODUCTION)
             processor = container.resolve(DataProcessor)
             # processor.plugins == [ValidationPlugin, TransformPlugin]

      .. seealso::

         - :class:`dioxide.scope.Scope` - SINGLETON vs FACTORY scope
         - :class:`dioxide.profile_enum.Profile` - Extensible profile identifiers
         - :class:`dioxide.container.Container.scan` - Profile-based scanning
         - :class:`dioxide.lifecycle.lifecycle` - For initialization/cleanup
         - :class:`dioxide.services.service` - For core domain logic



.. py:data:: adapter
