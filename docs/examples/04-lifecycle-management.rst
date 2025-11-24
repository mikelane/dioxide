Tutorial 4: Lifecycle Management
==================================

This tutorial demonstrates how to manage resources that need initialization and cleanup using dioxide's ``@lifecycle`` decorator.

The Problem: Resource Management
---------------------------------

Many components need setup and teardown:

* **Database connections** - Connect on startup, close on shutdown
* **HTTP clients** - Create session on startup, close on shutdown
* **Message queues** - Connect on startup, disconnect on shutdown
* **File handles** - Open on startup, close on shutdown

Without proper lifecycle management:

* Resource leaks (connections never closed)
* Tests leave resources hanging
* Shutdown takes forever (waiting for timeouts)
* Errors during startup go unnoticed

The Solution: ``@lifecycle`` Decorator
---------------------------------------

dioxide provides the ``@lifecycle`` decorator for opt-in lifecycle management:

.. code-block:: python

   from dioxide import service, lifecycle

   @service
   @lifecycle
   class Database:
       """Database with lifecycle management."""

       def __init__(self, config: AppConfig):
           self.config = config
           self.engine = None

       async def initialize(self) -> None:
           """Called automatically on container startup."""
           self.engine = create_async_engine(self.config.database_url)
           print(f"✅ Connected to {self.config.database_url}")

       async def dispose(self) -> None:
           """Called automatically on container shutdown."""
           if self.engine:
               await self.engine.dispose()
               print(f"🔌 Database connection closed")

**Key points:**

* ``@lifecycle`` marks components for lifecycle management
* ``initialize()`` - Called once on container startup (in dependency order)
* ``dispose()`` - Called once on container shutdown (in reverse dependency order)
* Both methods must be ``async`` coroutines

Using Lifecycle Components
---------------------------

**Option 1: Async Context Manager (Recommended)**

The container provides an async context manager that automatically calls ``initialize()`` and ``dispose()``:

.. code-block:: python

   from dioxide import Container, Profile

   async def main():
       container = Container()
       container.scan("myapp", profile=Profile.PRODUCTION)

       async with container:
           # All @lifecycle components initialized here (in dependency order)
           app = container.resolve(Application)
           await app.run()
       # All @lifecycle components disposed here (in reverse order)

**Option 2: Manual Control**

For more control, use ``start()`` and ``stop()`` explicitly:

.. code-block:: python

   async def main():
       container = Container()
       container.scan("myapp", profile=Profile.PRODUCTION)

       try:
           await container.start()  # Initialize all @lifecycle components
           app = container.resolve(Application)
           await app.run()
       finally:
           await container.stop()  # Dispose all @lifecycle components

Lifecycle Order
---------------

dioxide initializes and disposes components in the correct order:

**Initialization Order**: Dependencies before dependents

.. code-block:: python

   @service
   @lifecycle
   class Database:
       async def initialize(self):
           print("1️⃣  Database initializing")

   @service
   @lifecycle
   class Cache:
       def __init__(self, db: Database):  # Depends on Database
           self.db = db

       async def initialize(self):
           print("2️⃣  Cache initializing")

   @service
   @lifecycle
   class Application:
       def __init__(self, db: Database, cache: Cache):  # Depends on both
           self.db = db
           self.cache = cache

       async def initialize(self):
           print("3️⃣  Application initializing")

**Order**: Database → Cache → Application (dependencies first)

**Disposal Order**: Reverse of initialization

.. code-block:: text

   Dispose order: Application → Cache → Database (dependents first)

This ensures resources are cleaned up in the correct order.

Complete Example: Database Connection
--------------------------------------

Here's a complete example with a database connection:

.. code-block:: python

   """
   Lifecycle Management Example

   This example demonstrates:
   - @lifecycle decorator for initialization and cleanup
   - Async context manager usage
   - Dependency-ordered initialization/disposal
   - Resource leak prevention
   """
   import asyncio
   from dioxide import service, lifecycle, Container, Profile, adapter
   from typing import Protocol
   from dataclasses import dataclass

   # ===== CONFIGURATION =====
   @service
   class AppConfig:
       """Application configuration."""
       database_url: str = "postgresql://localhost/myapp"

   # ===== DOMAIN MODEL =====
   @dataclass
   class User:
       id: int
       name: str
       email: str

   # ===== PORT =====
   class UserRepository(Protocol):
       async def find_all(self) -> list[User]: ...
       async def save(self, user: User) -> None: ...

   # ===== PRODUCTION ADAPTER WITH LIFECYCLE =====
   @service
   @lifecycle
   class Database:
       """Database connection with lifecycle management."""

       def __init__(self, config: AppConfig):
           self.config = config
           self.engine = None
           self.connected = False

       async def initialize(self) -> None:
           """Initialize database connection."""
           print(f"🔌 Connecting to {self.config.database_url}")
           # Simulate connection
           await asyncio.sleep(0.1)
           self.connected = True
           print(f"✅ Database connected")

       async def dispose(self) -> None:
           """Close database connection."""
           if self.connected:
               print(f"🔌 Closing database connection")
               # Simulate cleanup
               await asyncio.sleep(0.1)
               self.connected = False
               print(f"✅ Database connection closed")

   @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   @lifecycle
   class PostgresUserRepository:
       """Production repository with lifecycle."""

       def __init__(self, db: Database):
           self.db = db
           self.prepared = False

       async def initialize(self) -> None:
           """Prepare repository (e.g., create tables, indexes)."""
           print(f"⚙️  Preparing PostgresUserRepository")
           await asyncio.sleep(0.05)
           self.prepared = True
           print(f"✅ PostgresUserRepository ready")

       async def dispose(self) -> None:
           """Clean up repository resources."""
           if self.prepared:
               print(f"🧹 Cleaning up PostgresUserRepository")
               self.prepared = False
               print(f"✅ PostgresUserRepository cleaned up")

       async def find_all(self) -> list[User]:
           """Find all users (simulated)."""
           return [
               User(1, "Alice", "alice@example.com"),
               User(2, "Bob", "bob@example.com")
           ]

       async def save(self, user: User) -> None:
           """Save user (simulated)."""
           print(f"💾 Saving user: {user.name}")

   # ===== TEST ADAPTER WITHOUT LIFECYCLE =====
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class InMemoryUserRepository:
       """Test repository - no lifecycle needed!"""

       def __init__(self):
           self.users: list[User] = []

       async def find_all(self) -> list[User]:
           return self.users

       async def save(self, user: User) -> None:
           self.users.append(user)

       def seed(self, *users: User) -> None:
           """Helper for tests - no initialization required."""
           self.users.extend(users)

   # ===== SERVICE =====
   @service
   class UserService:
       """User service - no lifecycle needed."""

       def __init__(self, users: UserRepository):
           self.users = users

       async def list_users(self) -> list[User]:
           """List all users."""
           return await self.users.find_all()

       async def create_user(self, name: str, email: str) -> User:
           """Create a new user."""
           user = User(id=len(await self.users.find_all()) + 1, name=name, email=email)
           await self.users.save(user)
           return user

   # ===== USAGE =====
   async def main():
       print("=" * 70)
       print("LIFECYCLE MANAGEMENT EXAMPLE")
       print("=" * 70)

       # Production with lifecycle
       print("\n🏭 PRODUCTION - With Lifecycle Management")
       print("-" * 70)

       container = Container()
       container.scan(__name__, profile=Profile.PRODUCTION)

       async with container:
           # All @lifecycle components initialized here
           print("\n📋 Application running...")
           user_service = container.resolve(UserService)
           users = await user_service.list_users()
           print(f"Found {len(users)} users")

           await user_service.create_user("Charlie", "charlie@example.com")
           print()
       # All @lifecycle components disposed here

       # Test without lifecycle
       print("\n🧪 TEST - No Lifecycle Needed")
       print("-" * 70)

       test_container = Container()
       test_container.scan(__name__, profile=Profile.TEST)

       # No async context manager needed for test fakes!
       user_repo = test_container.resolve(UserRepository)
       user_repo.seed(
           User(1, "Alice", "alice@test.com"),
           User(2, "Bob", "bob@test.com")
       )

       test_service = test_container.resolve(UserService)
       users = await test_service.list_users()
       print(f"✅ Found {len(users)} test users (no lifecycle overhead!)")

       print("\n" + "=" * 70)
       print("KEY TAKEAWAYS:")
       print("✅ @lifecycle for resources that need init/cleanup")
       print("✅ async with container: auto-manages lifecycle")
       print("✅ Initialization in dependency order")
       print("✅ Disposal in reverse dependency order")
       print("✅ Test fakes don't need lifecycle (fast!)")
       print("=" * 70)

   if __name__ == "__main__":
       asyncio.run(main())

Running the Example
-------------------

Save the example to a file (e.g., ``lifecycle.py``) and run it:

.. code-block:: bash

   python lifecycle.py

**Expected Output:**

.. code-block:: text

   ======================================================================
   LIFECYCLE MANAGEMENT EXAMPLE
   ======================================================================

   🏭 PRODUCTION - With Lifecycle Management
   ----------------------------------------------------------------------
   🔌 Connecting to postgresql://localhost/myapp
   ✅ Database connected
   ⚙️  Preparing PostgresUserRepository
   ✅ PostgresUserRepository ready

   📋 Application running...
   Found 2 users
   💾 Saving user: Charlie

   🧹 Cleaning up PostgresUserRepository
   ✅ PostgresUserRepository cleaned up
   🔌 Closing database connection
   ✅ Database connection closed

   🧪 TEST - No Lifecycle Needed
   ----------------------------------------------------------------------
   ✅ Found 2 test users (no lifecycle overhead!)

   ======================================================================
   KEY TAKEAWAYS:
   ✅ @lifecycle for resources that need init/cleanup
   ✅ async with container: auto-manages lifecycle
   ✅ Initialization in dependency order
   ✅ Disposal in reverse dependency order
   ✅ Test fakes don't need lifecycle (fast!)
   ======================================================================

When to Use ``@lifecycle``
---------------------------

Use ``@lifecycle`` For
~~~~~~~~~~~~~~~~~~~~~~~

* **Database connections** - Need to connect/disconnect
* **HTTP clients** - Need to create/close sessions
* **Message queues** - Need to connect/disconnect
* **File handles** - Need to open/close
* **Thread pools** - Need to start/shutdown
* **Cache warmup** - Need to pre-load data

Don't Use ``@lifecycle`` For
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Stateless services** - No setup/teardown needed
* **Pure domain logic** - No external resources
* **Test fakes** - Usually don't need init/cleanup
* **Simple adapters** - Connection created per request

.. code-block:: python

   # ❌ Don't use @lifecycle here
   @service
   class Calculator:
       def add(self, a: int, b: int) -> int:
           return a + b  # Stateless, no resources

   # ✅ Do use @lifecycle here
   @service
   @lifecycle
   class Database:
       async def initialize(self):
           self.connection = await connect()  # Resource!

Testing with Lifecycle
----------------------

Test fakes typically **don't need** ``@lifecycle`` because they have no resources to manage:

.. code-block:: python

   # Production adapter - needs lifecycle
   @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   @lifecycle
   class PostgresUserRepository:
       async def initialize(self):
           self.pool = await create_connection_pool()  # Resource!

       async def dispose(self):
           await self.pool.close()

   # Test fake - no lifecycle needed!
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class InMemoryUserRepository:
       def __init__(self):
           self.users = []  # Just a list, no resources

This makes tests **fast** - no initialization overhead!

Lifecycle in Tests
~~~~~~~~~~~~~~~~~~

If you need lifecycle in tests, it works the same way:

.. code-block:: python

   import pytest
   from dioxide import Container, Profile

   @pytest.fixture
   async def container():
       """Container with lifecycle management."""
       c = Container()
       c.scan("myapp", profile=Profile.TEST)

       async with c:
           yield c
       # Automatic cleanup after test

   @pytest.mark.asyncio
   async def test_user_service(container):
       """All lifecycle components initialized before test."""
       user_service = container.resolve(UserService)
       users = await user_service.list_users()
       assert len(users) == 0

Error Handling
--------------

If initialization fails, dioxide stops and reports the error:

.. code-block:: python

   @service
   @lifecycle
   class Database:
       async def initialize(self):
           raise ConnectionError("Cannot connect to database")

   # This will raise an exception during container startup
   async with container:
       pass  # Never reached - initialization failed

**Result**: Clear error message pointing to the failing component.

Circular Dependencies
~~~~~~~~~~~~~~~~~~~~~

dioxide detects circular dependencies at scan time:

.. code-block:: python

   @service
   class A:
       def __init__(self, b: B):
           pass

   @service
   class B:
       def __init__(self, a: A):
           pass

   container.scan(__name__)  # Raises: CircularDependencyError

**No silent failures** - circular dependencies are caught immediately.

Advanced Patterns
-----------------

Conditional Initialization
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can conditionally skip initialization:

.. code-block:: python

   @service
   @lifecycle
   class Cache:
       def __init__(self, config: AppConfig):
           self.config = config
           self.redis = None

       async def initialize(self):
           if self.config.enable_cache:
               self.redis = await connect_redis()
           else:
               print("Cache disabled, skipping initialization")

       async def dispose(self):
           if self.redis:
               await self.redis.close()

Graceful Degradation
~~~~~~~~~~~~~~~~~~~~

Handle initialization errors gracefully:

.. code-block:: python

   @service
   @lifecycle
   class MetricsCollector:
       async def initialize(self):
           try:
               self.client = await connect_metrics_server()
           except ConnectionError:
               print("⚠️  Metrics server unavailable, disabling metrics")
               self.client = None

       async def collect(self, metric: str, value: float):
           if self.client:
               await self.client.send(metric, value)

Warmup Data Loading
~~~~~~~~~~~~~~~~~~~

Pre-load data during initialization:

.. code-block:: python

   @service
   @lifecycle
   class ProductCatalog:
       def __init__(self, db: Database):
           self.db = db
           self.products = []

       async def initialize(self):
           """Warmup cache with popular products."""
           print("🔥 Warming up product cache")
           self.products = await self.db.query("SELECT * FROM products WHERE popular = true")
           print(f"✅ Cached {len(self.products)} popular products")

Key Concepts
------------

``@lifecycle`` Decorator
~~~~~~~~~~~~~~~~~~~~~~~~

Marks components for lifecycle management:

* Must implement ``async def initialize() -> None``
* Must implement ``async def dispose() -> None``
* Type stubs provide IDE autocomplete and mypy validation
* Works with both ``@service`` and ``@adapter.for_()`` decorators

Async Context Manager
~~~~~~~~~~~~~~~~~~~~~

The recommended way to use lifecycle:

.. code-block:: python

   async with container:
       # All @lifecycle components initialized
       app = container.resolve(Application)
       await app.run()
   # All @lifecycle components disposed

**Guarantees**:

* Initialization happens before any resolves
* Disposal happens even if exceptions occur
* Correct dependency order maintained

Dependency Order
~~~~~~~~~~~~~~~~

dioxide uses Kahn's algorithm to determine initialization order:

1. **Build dependency graph** from type hints
2. **Topological sort** to find valid order
3. **Initialize in order** (dependencies first)
4. **Dispose in reverse order** (dependents first)

**Example**:

.. code-block:: text

   Database → Cache → Repository → Service

   Initialize: Database → Cache → Repository → Service
   Dispose:    Service → Repository → Cache → Database

Test Fakes Without Lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test fakes typically don't need ``@lifecycle`` because:

* No external resources (in-memory only)
* Instant "initialization" (just create objects)
* No cleanup needed (garbage collected)
* **Faster tests** (no initialization overhead)

.. code-block:: python

   # Production - needs lifecycle
   @adapter.for_(Database, profile=Profile.PRODUCTION)
   @lifecycle
   class PostgresAdapter:
       async def initialize(self):
           self.pool = await create_pool()  # Slow!

   # Test - no lifecycle
   @adapter.for_(Database, profile=Profile.TEST)
   class InMemoryAdapter:
       def __init__(self):
           self.data = {}  # Instant!

Summary
-------

Lifecycle management with dioxide:

* **Opt-in** - Only components that need it use ``@lifecycle``
* **Type-safe** - Type stubs validate method signatures
* **Dependency-aware** - Correct initialization/disposal order
* **Test-friendly** - Fakes don't need lifecycle overhead
* **Async-native** - Built for async Python applications

**When to use**:

* ✅ Database connections
* ✅ HTTP clients
* ✅ Message queues
* ✅ Resource warmup
* ❌ Stateless services
* ❌ Pure domain logic
* ❌ Most test fakes

**How to use**:

.. code-block:: python

   @service
   @lifecycle
   class Database:
       async def initialize(self): ...
       async def dispose(self): ...

   async with container:
       app = container.resolve(Application)
       await app.run()

That's it! You now know how to use lifecycle management in dioxide.

Next Steps
----------

You've completed all four tutorials! You now understand:

1. **Basic Dependency Injection** - ``@service`` and constructor injection
2. **Ports and Adapters** - Hexagonal architecture with profiles
3. **Multi-Tier Applications** - Multiple ports and services
4. **Lifecycle Management** - Resource initialization and cleanup

To learn more:

* **FastAPI Integration**: See ``examples/fastapi/`` for a complete web application
* **Testing Guide**: See ``docs/TESTING_GUIDE.md`` for testing philosophy and patterns
* **API Reference**: Explore the full API documentation
* **MLP Vision**: Read ``docs/MLP_VISION.md`` for dioxide's design philosophy

Happy coding with dioxide!
