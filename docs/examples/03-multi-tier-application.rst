Tutorial 3: Multi-Tier Application
====================================

This tutorial demonstrates a realistic multi-tier application with multiple ports, adapters, and services working together.

Real-World Application Structure
---------------------------------

Most applications need multiple infrastructure dependencies:

* **Database** - PostgreSQL in production, in-memory in tests
* **Cache** - Redis in production, dict in tests
* **Email** - SendGrid in production, fake in tests
* **External APIs** - Real HTTP calls in production, fakes in tests

We'll build a **notification system** that demonstrates these patterns.

Application Architecture
------------------------

Our notification system has three layers:

1. **Ports** - Interfaces defining what we need
2. **Adapters** - Implementations for different environments
3. **Services** - Business logic orchestrating ports

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │      NotificationService (Core)         │  ← Business Logic
   │   - Orchestrates multiple ports         │
   └──────────────┬──────────────────────────┘
                  │ depends on
                  ▼
   ┌─────────────────────────────────────────┐
   │  Ports (Protocols - Interfaces)         │
   │  - UserRepository                       │
   │  - CachePort                            │
   │  - EmailPort                            │
   └──────────────┬──────────────────────────┘
                  │ implemented by
                  ▼
   ┌─────────────────────────────────────────┐
   │  Adapters (Profile-specific)            │
   │  Production: Postgres, Redis, SendGrid  │
   │  Test: InMemory, Dict, Fake             │
   └─────────────────────────────────────────┘

Step 1: Define Ports
--------------------

Create interfaces for all infrastructure needs:

.. code-block:: python

   from typing import Protocol
   from dataclasses import dataclass
   from datetime import datetime

   @dataclass
   class User:
       """User domain model."""
       id: int
       email: str
       name: str
       last_notified_at: datetime | None = None

   class UserRepository(Protocol):
       """Port for user data access."""

       async def find_by_id(self, user_id: int) -> User | None:
           """Find user by ID."""
           ...

       async def save(self, user: User) -> None:
           """Save or update user."""
           ...

   class CachePort(Protocol):
       """Port for caching."""

       async def get(self, key: str) -> str | None:
           """Get cached value."""
           ...

       async def set(self, key: str, value: str, ttl_seconds: int) -> None:
           """Set cached value with TTL."""
           ...

   class EmailPort(Protocol):
       """Port for email sending."""

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send email."""
           ...

Step 2: Create Production Adapters
-----------------------------------

PostgreSQL User Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dioxide import adapter, Profile, service
   from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

   @service
   class Database:
       """Database connection - shared across repositories."""

       def __init__(self, config: AppConfig):
           self.engine: AsyncEngine | None = None
           self.database_url = config.database_url

       async def initialize(self) -> None:
           """Initialize connection (lifecycle method)."""
           self.engine = create_async_engine(self.database_url)

       async def dispose(self) -> None:
           """Close connection (lifecycle method)."""
           if self.engine:
               await self.engine.dispose()

   @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   class PostgresUserRepository:
       """Production user repository using PostgreSQL."""

       def __init__(self, db: Database):
           self.db = db

       async def find_by_id(self, user_id: int) -> User | None:
           """Find user in PostgreSQL."""
           async with self.db.engine.begin() as conn:
               result = await conn.execute(
                   "SELECT id, email, name, last_notified_at FROM users WHERE id = :id",
                   {"id": user_id}
               )
               row = result.fetchone()
               if row:
                   return User(
                       id=row.id,
                       email=row.email,
                       name=row.name,
                       last_notified_at=row.last_notified_at
                   )
               return None

       async def save(self, user: User) -> None:
           """Save user to PostgreSQL."""
           async with self.db.engine.begin() as conn:
               await conn.execute(
                   """
                   INSERT INTO users (id, email, name, last_notified_at)
                   VALUES (:id, :email, :name, :last_notified_at)
                   ON CONFLICT (id) DO UPDATE SET
                       email = EXCLUDED.email,
                       name = EXCLUDED.name,
                       last_notified_at = EXCLUDED.last_notified_at
                   """,
                   {
                       "id": user.id,
                       "email": user.email,
                       "name": user.name,
                       "last_notified_at": user.last_notified_at
                   }
               )

Redis Cache Adapter
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import redis.asyncio as redis

   @adapter.for_(CachePort, profile=Profile.PRODUCTION)
   class RedisAdapter:
       """Production cache using Redis."""

       def __init__(self, config: AppConfig):
           self.redis: redis.Redis | None = None
           self.redis_url = config.redis_url

       async def initialize(self) -> None:
           """Connect to Redis (lifecycle method)."""
           self.redis = await redis.from_url(self.redis_url)

       async def dispose(self) -> None:
           """Close Redis connection (lifecycle method)."""
           if self.redis:
               await self.redis.close()

       async def get(self, key: str) -> str | None:
           """Get from Redis."""
           value = await self.redis.get(key)
           return value.decode() if value else None

       async def set(self, key: str, value: str, ttl_seconds: int) -> None:
           """Set in Redis with TTL."""
           await self.redis.setex(key, ttl_seconds, value)

SendGrid Email Adapter
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import httpx

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       """Production email using SendGrid."""

       def __init__(self, config: AppConfig):
           self.api_key = config.sendgrid_api_key

       async def send(self, to: str, subject: str, body: str) -> None:
           """Send email via SendGrid API."""
           async with httpx.AsyncClient() as client:
               await client.post(
                   "https://api.sendgrid.com/v3/mail/send",
                   headers={"Authorization": f"Bearer {self.api_key}"},
                   json={
                       "personalizations": [{"to": [{"email": to}]}],
                       "from": {"email": "noreply@example.com"},
                       "subject": subject,
                       "content": [{"type": "text/plain", "value": body}]
                   }
               )

Step 3: Create Test Adapters (Fakes)
-------------------------------------

In-Memory User Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class InMemoryUserRepository:
       """Fast fake for testing - no database required."""

       def __init__(self):
           self.users: dict[int, User] = {}

       async def find_by_id(self, user_id: int) -> User | None:
           """Find user in memory."""
           return self.users.get(user_id)

       async def save(self, user: User) -> None:
           """Save user to memory."""
           self.users[user.id] = user

       def seed(self, *users: User) -> None:
           """Seed test data - only available in fakes!"""
           for user in users:
               self.users[user.id] = user

Dict Cache Adapter
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @adapter.for_(CachePort, profile=Profile.TEST)
   class DictCacheAdapter:
       """Fast fake cache using dict - no Redis required."""

       def __init__(self):
           self.cache: dict[str, str] = {}

       async def get(self, key: str) -> str | None:
           """Get from dict."""
           return self.cache.get(key)

       async def set(self, key: str, value: str, ttl_seconds: int) -> None:
           """Set in dict (TTL not enforced in tests)."""
           self.cache[key] = value

Fake Email Adapter
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       """Fast fake email - no network calls."""

       def __init__(self):
           self.sent_emails: list[dict] = []

       async def send(self, to: str, subject: str, body: str) -> None:
           """Record email instead of sending."""
           self.sent_emails.append({
               "to": to,
               "subject": subject,
               "body": body
           })

Step 4: Implement Service Layer
--------------------------------

The service layer orchestrates multiple ports:

.. code-block:: python

   from dioxide import service
   from datetime import datetime, timedelta, UTC

   @service
   class NotificationService:
       """Core business logic - orchestrates multiple ports."""

       def __init__(
           self,
           users: UserRepository,
           cache: CachePort,
           email: EmailPort
       ):
           """All dependencies injected via constructor."""
           self.users = users
           self.cache = cache
           self.email = email

       async def send_notification(self, user_id: int, message: str) -> bool:
           """Send notification with throttling and caching.

           Business rules:
           1. Don't send if user doesn't exist
           2. Don't send more than once per hour (throttling)
           3. Cache notification status for 5 minutes
           """
           # Check cache first
           cache_key = f"notification:{user_id}"
           cached = await self.cache.get(cache_key)
           if cached:
               print(f"⚡ Notification cached, skipping send")
               return False

           # Get user
           user = await self.users.find_by_id(user_id)
           if not user:
               print(f"❌ User {user_id} not found")
               return False

           # Throttle: Don't send if sent within past hour
           if user.last_notified_at:
               elapsed = datetime.now(UTC) - user.last_notified_at
               if elapsed < timedelta(hours=1):
                   print(f"⏱️  Throttled: Last notified {elapsed.total_seconds():.0f}s ago")
                   return False

           # Send notification
           await self.email.send(
               to=user.email,
               subject="New Notification",
               body=message
           )

           # Update user
           user.last_notified_at = datetime.now(UTC)
           await self.users.save(user)

           # Cache for 5 minutes
           await self.cache.set(cache_key, "sent", ttl_seconds=300)

           print(f"✅ Notification sent to {user.email}")
           return True

Complete Example
----------------

Here's a complete, runnable example:

.. code-block:: python

   """
   Multi-Tier Application Example

   This example demonstrates:
   - Multiple ports (database, cache, email)
   - Multiple adapters per port (production, test)
   - Service orchestrating multiple dependencies
   - Testing with all fakes (no I/O)
   """
   import asyncio
   from typing import Protocol
   from dataclasses import dataclass
   from datetime import datetime, timedelta, UTC
   from dioxide import adapter, service, Container, Profile

   # ===== DOMAIN MODEL =====
   @dataclass
   class User:
       id: int
       email: str
       name: str
       last_notified_at: datetime | None = None

   # ===== PORTS =====
   class UserRepository(Protocol):
       async def find_by_id(self, user_id: int) -> User | None: ...
       async def save(self, user: User) -> None: ...

   class CachePort(Protocol):
       async def get(self, key: str) -> str | None: ...
       async def set(self, key: str, value: str, ttl_seconds: int) -> None: ...

   class EmailPort(Protocol):
       async def send(self, to: str, subject: str, body: str) -> None: ...

   # ===== PRODUCTION ADAPTERS =====
   @adapter.for_(UserRepository, profile=Profile.PRODUCTION)
   class PostgresUserRepository:
       async def find_by_id(self, user_id: int) -> User | None:
           print(f"💾 [Postgres] Looking up user {user_id}")
           # Simulate database query
           return User(id=user_id, email=f"user{user_id}@example.com", name=f"User {user_id}")

       async def save(self, user: User) -> None:
           print(f"💾 [Postgres] Saving user {user.id}")

   @adapter.for_(CachePort, profile=Profile.PRODUCTION)
   class RedisAdapter:
       def __init__(self):
           self.cache = {}

       async def get(self, key: str) -> str | None:
           print(f"🔴 [Redis] GET {key}")
           return self.cache.get(key)

       async def set(self, key: str, value: str, ttl_seconds: int) -> None:
           print(f"🔴 [Redis] SET {key} (TTL: {ttl_seconds}s)")
           self.cache[key] = value

   @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
   class SendGridAdapter:
       async def send(self, to: str, subject: str, body: str) -> None:
           print(f"📧 [SendGrid] Sending to {to}: {subject}")

   # ===== TEST ADAPTERS (FAKES) =====
   @adapter.for_(UserRepository, profile=Profile.TEST)
   class InMemoryUserRepository:
       def __init__(self):
           self.users: dict[int, User] = {}

       async def find_by_id(self, user_id: int) -> User | None:
           return self.users.get(user_id)

       async def save(self, user: User) -> None:
           self.users[user.id] = user

       def seed(self, *users: User) -> None:
           for user in users:
               self.users[user.id] = user

   @adapter.for_(CachePort, profile=Profile.TEST)
   class DictCacheAdapter:
       def __init__(self):
           self.cache: dict[str, str] = {}

       async def get(self, key: str) -> str | None:
           return self.cache.get(key)

       async def set(self, key: str, value: str, ttl_seconds: int) -> None:
           self.cache[key] = value

   @adapter.for_(EmailPort, profile=Profile.TEST)
   class FakeEmailAdapter:
       def __init__(self):
           self.sent_emails: list[dict] = []

       async def send(self, to: str, subject: str, body: str) -> None:
           self.sent_emails.append({"to": to, "subject": subject, "body": body})

   # ===== SERVICE =====
   @service
   class NotificationService:
       def __init__(self, users: UserRepository, cache: CachePort, email: EmailPort):
           self.users = users
           self.cache = cache
           self.email = email

       async def send_notification(self, user_id: int, message: str) -> bool:
           # Check cache
           cache_key = f"notification:{user_id}"
           if await self.cache.get(cache_key):
               print(f"⚡ Cached, skipping")
               return False

           # Get user
           user = await self.users.find_by_id(user_id)
           if not user:
               print(f"❌ User not found")
               return False

           # Throttle check
           if user.last_notified_at:
               elapsed = datetime.now(UTC) - user.last_notified_at
               if elapsed < timedelta(hours=1):
                   print(f"⏱️  Throttled")
                   return False

           # Send
           await self.email.send(user.email, "Notification", message)
           user.last_notified_at = datetime.now(UTC)
           await self.users.save(user)
           await self.cache.set(cache_key, "sent", 300)
           return True

   # ===== USAGE =====
   async def main():
       print("=" * 70)
       print("MULTI-TIER APPLICATION EXAMPLE")
       print("=" * 70)

       # Production
       print("\n🏭 PRODUCTION - PostgreSQL + Redis + SendGrid")
       print("-" * 70)
       prod_container = Container()
       prod_container.scan(__name__, profile=Profile.PRODUCTION)
       prod_service = prod_container.resolve(NotificationService)
       await prod_service.send_notification(1, "Hello from production!")

       # Test
       print("\n🧪 TEST - In-Memory + Dict + Fake")
       print("-" * 70)
       test_container = Container()
       test_container.scan(__name__, profile=Profile.TEST)

       # Seed test data
       users = test_container.resolve(UserRepository)
       users.seed(User(id=1, email="alice@test.com", name="Alice"))

       test_service = test_container.resolve(NotificationService)
       result = await test_service.send_notification(1, "Test message")
       print(f"Result: {result}")

       # Verify
       fake_email = test_container.resolve(EmailPort)
       assert len(fake_email.sent_emails) == 1
       print("✅ Test passed: Email was sent")

       print("\n" + "=" * 70)
       print("KEY TAKEAWAYS:")
       print("✅ Service orchestrates multiple ports")
       print("✅ All dependencies auto-injected")
       print("✅ Profile switches all adapters at once")
       print("✅ Test fakes are fast and deterministic")
       print("=" * 70)

   if __name__ == "__main__":
       asyncio.run(main())

Testing the Multi-Tier Application
-----------------------------------

With fakes, testing is straightforward:

.. code-block:: python

   import pytest
   from dioxide import Container, Profile

   @pytest.fixture
   def container():
       c = Container()
       c.scan("myapp", profile=Profile.TEST)
       return c

   @pytest.fixture
   def notification_service(container):
       return container.resolve(NotificationService)

   @pytest.fixture
   def user_repo(container):
       return container.resolve(UserRepository)

   @pytest.fixture
   def fake_email(container):
       return container.resolve(EmailPort)

   @pytest.mark.asyncio
   async def test_sends_notification_to_existing_user(
       notification_service, user_repo, fake_email
   ):
       """Sends notification when user exists and not throttled."""
       # Arrange
       user_repo.seed(User(id=1, email="alice@test.com", name="Alice"))

       # Act
       result = await notification_service.send_notification(1, "Hello Alice!")

       # Assert
       assert result is True
       assert len(fake_email.sent_emails) == 1
       assert fake_email.sent_emails[0]["to"] == "alice@test.com"

   @pytest.mark.asyncio
   async def test_throttles_duplicate_notifications(
       notification_service, user_repo, fake_email
   ):
       """Does not send duplicate notification within throttle window."""
       # Arrange
       user = User(
           id=1,
           email="alice@test.com",
           name="Alice",
           last_notified_at=datetime.now(UTC)  # Just notified
       )
       user_repo.seed(user)

       # Act
       result = await notification_service.send_notification(1, "Hello again!")

       # Assert
       assert result is False  # Throttled
       assert len(fake_email.sent_emails) == 0  # No email sent

**No mocks, no patches, no async magic** - just fast, deterministic tests!

Key Concepts
------------

Multiple Ports
~~~~~~~~~~~~~~

Applications typically need multiple ports:

* **Data access** - UserRepository, ProductRepository, etc.
* **Caching** - CachePort
* **External services** - EmailPort, PaymentPort, etc.
* **Time** - ClockPort (for testable time-dependent logic)

Service Orchestration
~~~~~~~~~~~~~~~~~~~~~

Services orchestrate multiple ports to implement business logic:

.. code-block:: python

   @service
   class OrderService:
       def __init__(
           self,
           orders: OrderRepository,
           payments: PaymentPort,
           email: EmailPort,
           inventory: InventoryPort
       ):
           # All injected automatically
           pass

       async def place_order(self, order: Order):
           # 1. Reserve inventory
           # 2. Process payment
           # 3. Save order
           # 4. Send confirmation email
           pass

Profile Switching
~~~~~~~~~~~~~~~~~

Changing profile switches **all adapters** at once:

.. code-block:: python

   # Production: PostgreSQL + Redis + SendGrid
   container.scan("myapp", profile=Profile.PRODUCTION)

   # Test: In-Memory + Dict + Fake
   container.scan("myapp", profile=Profile.TEST)

   # Same service, different adapters!
   service = container.resolve(NotificationService)

Test Data Seeding
~~~~~~~~~~~~~~~~~

Fakes can have helper methods for test setup:

.. code-block:: python

   @adapter.for_(UserRepository, profile=Profile.TEST)
   class InMemoryUserRepository:
       def seed(self, *users: User) -> None:
           """Seed test data - only in fakes!"""
           for user in users:
               self.users[user.id] = user

   # In tests
   users = container.resolve(UserRepository)
   users.seed(
       User(id=1, email="alice@test.com", name="Alice"),
       User(id=2, email="bob@test.com", name="Bob")
   )

Next Steps
----------

This tutorial showed a multi-tier application without lifecycle management. In the next tutorial, we'll add:

* ``@lifecycle`` decorator for initialization and cleanup
* Database connections that need startup/shutdown
* Async context manager usage
* Resource leak prevention

Continue to: :doc:`04-lifecycle-management`
