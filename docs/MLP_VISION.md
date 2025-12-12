# Dioxide MLP Vision: The Canonical Design

**Version:** 1.0.0 MLP (Minimum Loveable Product)
**Created:** 2025-11-07
**Status:** Canonical - This is the north star for all development decisions

---

## Table of Contents

1. [The North Star](#the-north-star)
2. [Guiding Principles](#guiding-principles)
3. [Core API Design](#core-api-design)
4. [Profile System](#profile-system)
5. [Testing Philosophy](#testing-philosophy)
6. [Framework Integration](#framework-integration)
7. [Complete Example](#complete-example)
8. [What We're NOT Building](#what-were-not-building)
9. [Success Metrics](#success-metrics)

---

## The North Star

### The Problem We Solve

Python makes tight coupling easy and loose coupling tedious. Most codebases evolve into unmaintainable messes because:

1. **Direct dependencies everywhere** - Business logic hardcoded to PostgreSQL, SendGrid, etc.
2. **Testing requires mocks** - Patching, mocking, testing mock behavior instead of real code
3. **Architecture is accidental** - No clear boundaries, everything depends on everything
4. **Change is expensive** - Swapping email provider requires editing 50 files

### Our Mission

**Make the Dependency Inversion Principle feel inevitable.**

More specifically:

> **Make it trivially easy to depend on abstractions (ports) instead of implementations (adapters), so that loose coupling becomes the path of least resistance.**

### The Vision

When someone asks "How do I structure a Python application?", the answer should be:

1. Define your ports (Protocols)
2. Add `@component` to your implementations
3. Tag implementations with `@profile`
4. Let Dioxide handle everything else

**Result:** Clean architecture happens by default, not because developers are disciplined, but because it's the easiest path.

---

## Guiding Principles

These principles guide ALL design decisions for Dioxide:

### 1. Type-Checker is the Source of Truth

**Principle:** If mypy/pyright passes, the wiring is correct.

- Use Python's type system completely
- No magic strings where types would work
- IDE autocomplete guides users

**Example:**
```python
# ✅ Good - type-checked
def __init__(self, repo: UserRepository):
    self.repo = repo

# ❌ Bad - magic string
def __init__(self, repo: "UserRepository"):
    self.repo = repo
```

### 2. Explicit Over Clever

**Principle:** Boring is beautiful. Favor clarity over cleverness.

- No deep magic that requires reading source code to understand
- One obvious way to do things
- Explicit configuration when behavior isn't obvious

**Example:**
```python
# ✅ Good - obvious what this does
container.scan("app", profile="test")

# ❌ Bad - too much magic
container.auto_configure()
```

### 3. Fails Fast

**Principle:** Errors at import/startup, never at resolution time.

- Validate dependency graph at container initialization
- Circular dependencies caught immediately
- Missing dependencies fail before first request

### 4. Zero Ceremony for Common Cases

**Principle:** 95% of use cases should be trivial.

- No manual `.bind()` calls for typical usage
- No manual `.resolve()` calls in application code
- Just use classes normally

### 5. Pythonic

**Principle:** Feel native, not ported from Java/C#.

- Use Python protocols, not Java interfaces
- Use decorators, not XML configuration
- Use type hints, not string lookups

### 6. Testing is Architecture

**Principle:** Good architecture makes testing easy without mocks.

- Encourage ports-and-adapters
- Promote fast fakes over mocks
- Make swapping implementations trivial

### 7. Performance is Not a Tradeoff

**Principle:** Rust makes DI instant.

- Dependency resolution is O(1)
- Singleton caching is free
- No runtime overhead compared to manual DI

---

## Core API Design

### Hexagonal Architecture: Ports and Adapters

Dioxide makes hexagonal architecture explicit through distinct decorators for different architectural layers.

#### The @service Decorator

Marks **core domain logic** - business rules that don't depend on external systems.

```python
from dioxide import service

# Core business logic (singleton by default)
@service
class UserService:
    def __init__(self, email: EmailPort, db: UserRepository):
        self.email = email  # Depends on PORTS, not concrete adapters
        self.db = db

    async def register_user(self, email_addr: str, name: str):
        # Pure business logic - doesn't know about SendGrid or Postgres
        user = await self.db.save({"email": email_addr, "name": name})
        await self.email.send(to=email_addr, subject="Welcome!", body=f"Hello {name}!")
        return user
```

**Key behaviors:**
1. **Always singleton** - One instance shared across application
2. **Constructor injection** - Dependencies resolved from type hints
3. **Depends on ports** - Uses Protocol/ABC types, not concrete implementations
4. **Profile-agnostic** - Same service in all environments

#### The @adapter.for_() Decorator

Marks **boundary implementations** - adapters that connect to external systems.

```python
from typing import Protocol
from dioxide import adapter, Profile

# Port (interface) - defines the seam
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter - real SendGrid
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        pass

# Test adapter - fake for testing
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Development adapter - console logging
@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"📧 To: {to}, Subject: {subject}")
```

**Key behaviors:**
1. **Profile-specific** - Different adapter per environment
2. **Implements a port** - Satisfies Protocol/ABC contract
3. **Singleton by default** - One instance per profile
4. **Type-safe** - Must implement all port methods

#### Architecture Layers

```
┌─────────────────────────────────────┐
│   @service (Core Domain Logic)     │  ← Business rules
│   - UserService                    │  ← Profile-agnostic
│   - OrderService                   │  ← Depends on ports
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Ports (Protocols/ABCs)            │  ← Interfaces/contracts
│   - EmailPort                       │  ← No decorators!
│   - UserRepository                  │  ← Just type definitions
└──────────────┬──────────────────────┘
               │ implemented by
               ▼
┌─────────────────────────────────────┐
│   @adapter.for_(Port, profile=...)  │  ← Boundary implementations
│   - SendGridAdapter                 │  ← Profile-specific
│   - FakeEmailAdapter                │  ← Swappable
└─────────────────────────────────────┘
```

**Type Safety:** Services depend on `EmailPort` (Protocol), container injects `SendGridAdapter` or `FakeEmailAdapter` based on active profile.

### Container: The Global Singleton

The container is a **global singleton**. You never instantiate it.

```python
from dioxide import container

# Scan packages to discover components
container.scan("app", profile="production")

# Use classes directly - they auto-inject
service = NotificationService()  # Dependencies injected automatically!

# Only use container for entry points
async def main():
    async with container:  # Calls initialize() on all components
        app = container[Application]
        await app.run()
    # Calls dispose() on all components
```

**Design decisions:**

1. **Global singleton** - No passing container around
2. **Scan once** - At application startup
3. **Auto-injection** - Just call constructors
4. **Lifecycle management** - Async context manager

### Lifecycle: The `@lifecycle` Decorator

Services and adapters can use the `@lifecycle` decorator to opt into initialization and cleanup.

```python
from dioxide import service, lifecycle

@service
@lifecycle
class Database:
    """Service with lifecycle management."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = None

    async def initialize(self) -> None:
        """Called automatically by container.start() or async with container."""
        self.engine = create_async_engine(self.config.database_url)
        logger.info(f"Connected to {self.config.database_url}")

    async def dispose(self) -> None:
        """Called automatically by container.stop() or async with exit."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
```

**Why `@lifecycle` decorator?**

- **Consistent with dioxide API** - Everything uses decorators (`@adapter.for_()`, `@service`, `@lifecycle`)
- **Explicit** - Clear at a glance which components have lifecycle
- **Type-safe** - Type checkers validate `initialize()` and `dispose()` signatures via stub files
- **Optional** - Only components that need lifecycle use it (test fakes typically don't!)

**Usage:**

```python
from dioxide import Container, Profile

async def main():
    container = Container()
    container.scan(profile=Profile.PRODUCTION)

    async with container:
        # All @lifecycle components initialized here (in dependency order)
        app = container.resolve(Application)
        await app.run()
    # All @lifecycle components disposed here (in reverse order)
```

---

## Profile System

### The Problem

Different environments need different implementations:
- **Production:** PostgreSQL, SendGrid, AWS S3
- **Testing:** In-memory, fake email, local files
- **Development:** SQLite, console email, local storage

### The Solution: Profile Enum

Use the `Profile` enum to specify which adapter implementations are active in each environment.

```python
from typing import Protocol
from dioxide import adapter, service, Profile, container

# Define port (interface)
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter - real SendGrid
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Real email - production only."""
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API call
        pass

# Test adapter - fake for testing
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Fast fake - testing only."""
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Development adapter - console logging
@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    """Dev email - prints to console."""
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"📧 To: {to}\n   Subject: {subject}\n   Body: {body}")

# Service depends on port (works with any adapter)
@service
class UserService:
    def __init__(self, email: EmailPort):
        self.email = email
```

**Activation:**

```python
from dioxide import container, Profile

# Production - activates SendGridAdapter
container.scan(profile=Profile.PRODUCTION)
email = container.resolve(EmailPort)  # Returns SendGridAdapter instance

# Testing - activates FakeEmailAdapter
container.scan(profile=Profile.TEST)
email = container.resolve(EmailPort)  # Returns FakeEmailAdapter instance

# Development - activates ConsoleEmailAdapter
container.scan(profile=Profile.DEVELOPMENT)
email = container.resolve(EmailPort)  # Returns ConsoleEmailAdapter instance
```

### Profile Enum: Type-Safe Profiles

The `Profile` enum provides type-safe, IDE-friendly profile selection:

```python
from dioxide import Profile

# Standard profiles (with IDE autocomplete)
Profile.PRODUCTION   # 'production'
Profile.TEST         # 'test'
Profile.DEVELOPMENT  # 'development'
Profile.STAGING      # 'staging'
Profile.CI           # 'ci'
Profile.ALL          # '*' - matches all profiles

# String-based enum
assert Profile.PRODUCTION.value == 'production'

# Case-insensitive matching (normalized to lowercase)
container.scan(profile='PRODUCTION')  # Works (converted to 'production')
container.scan(profile=Profile.PRODUCTION)  # Preferred (type-safe)
```

**Multiple Profiles:**

```python
# Adapter available in multiple profiles
@adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
class SimpleEmailAdapter:
    """Simple email for both test and dev."""
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"Simple email to {to}")

# Adapter available in ALL profiles
@adapter.for_(CachePort, profile=Profile.ALL)
class InMemoryCacheAdapter:
    """Simple cache available everywhere."""
    pass
```

**Custom Profiles (Strings):**

While `Profile` enum covers common cases, you can use strings for custom profiles:

```python
# Custom profile (not in enum)
@adapter.for_(EmailPort, profile='demo')
class DemoEmailAdapter:
    pass

# Activate custom profile
container.scan(profile='demo')
```

**Why Profile Enum?**

1. **Type safety** - Catch typos at type-check time, not runtime
2. **IDE autocomplete** - Discover available profiles
3. **Explicit** - Clear which profiles exist
4. **Extensible** - Can still use strings for custom profiles
5. **Consistent** - Case-insensitive, normalized matching

---

## Testing Philosophy

### The Problem with Mocks

Traditional testing relies on mocking frameworks:

```python
# ❌ Traditional approach - testing mock behavior
@patch('sendgrid.send')
@patch('database.query')
def test_notification(mock_db, mock_email):
    mock_db.return_value = {"id": 1}
    mock_email.return_value = True
    # Are we testing real code or mock configuration? 🤔
```

**Problems:**

1. Tests mock behavior, not real behavior
2. Mocks can lie (pass when real code would fail)
3. Tight coupling to implementation details
4. Brittle - refactoring breaks tests

### The Dioxide Way: Fakes at the Seams

Use **fast, real implementations** instead of mocks:

```python
# ✅ Dioxide approach - testing real code
async def test_notification(container):
    # Arrange: Set up using REAL fake implementations
    users = container[UserRepository]  # Real InMemoryUserRepository
    users.seed(User(id=1, email="alice@example.com"))

    # Act: Call the REAL service
    service = NotificationService()
    result = await service.send_welcome_email(1)

    # Assert: Check REAL observable outcomes
    assert result is True

    email = container[EmailProvider]  # Real FakeEmail
    assert len(email.outbox) == 1
    assert email.outbox[0]["to"] == "alice@example.com"
```

**Benefits:**

1. **Test real code** - Business logic runs for real
2. **Fast** - In-memory implementations, no I/O
3. **Deterministic** - FakeClock, no flaky tests
4. **Reusable** - Same fakes work for tests, dev, demos
5. **Better architecture** - Forces clear boundaries

### Fakes are First-Class Citizens

Fakes live in **production code**, not test code:

```
app/
  domain/
    services.py           # Business logic (depends on protocols)

  adapters/
    postgres.py           # @profile.production
    sendgrid.py           # @profile.production

    memory_repo.py        # @profile.test @profile.development
    fake_email.py         # @profile.test @profile.development
    fake_clock.py         # @profile.test
```

**Why in production code?**

1. Reusable across tests, dev environment, demos
2. Maintained alongside real implementations
3. Documents the protocol's contract
4. Can be shipped for user testing

### Testing Setup

```python
# conftest.py
import pytest
from dioxide import container

@pytest.fixture(autouse=True)
def setup_container():
    """Set up container with test profile before each test."""
    container.scan("app", profile="test")
    yield
    container.reset()  # Clean state between tests

# test_notification.py
async def test_welcome_email_sent():
    """Example test - just use classes normally."""

    # Arrange
    users = container[UserRepository]
    users.seed(User(id=123, email="alice@example.com", name="Alice"))

    clock = container[Clock]
    clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))

    # Act
    service = NotificationService()
    result = await service.send_welcome_email(123)

    # Assert
    assert result is True

    email = container[EmailProvider]
    assert len(email.outbox) == 1
    assert email.outbox[0]["subject"] == "Welcome!"
```

---

## Framework Integration

### FastAPI

Minimal adapter for dependency injection in routes:

```python
# app/main.py
from fastapi import FastAPI, Depends
from dioxide import container
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Set up container on startup, tear down on shutdown."""
    container.scan("app", profile="production")
    async with container:
        yield

app = FastAPI(lifespan=lifespan)

# Helper for injecting dependencies
def inject(cls: type[T]) -> T:
    """Inject a dioxide component into a FastAPI route."""
    def _get(request: Request) -> T:
        return container[cls]
    return Depends(_get)

# Use in routes
@app.post("/notifications")
async def send_notification(
    user_id: int,
    message: str,
    service: NotificationService = inject(NotificationService),
):
    success = await service.send_welcome_email(user_id)
    return {"success": success}
```

**Alternative (more magical):**

```python
from dioxide.fastapi import configure_dioxide

app = FastAPI()
configure_dioxide(app)  # One-time setup

# Now all type-hinted parameters auto-inject
@app.post("/notifications")
async def send_notification(
    user_id: int,
    service: NotificationService,  # Auto-injected!
):
    await service.send_welcome_email(user_id)
    return {"success": True}
```

### Flask

Similar pattern:

```python
from flask import Flask
from dioxide import container

app = Flask(__name__)

@app.before_request
def setup_container():
    if not container.is_initialized:
        container.scan("app", profile="production")
        container.initialize()

@app.route("/notifications", methods=["POST"])
def send_notification():
    service = container[NotificationService]
    result = service.send_welcome_email(request.json["user_id"])
    return {"success": result}
```

### Django

Integration via middleware:

```python
# middleware.py
from dioxide import container

class DiOxideMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        container.scan("app", profile="production")
        container.initialize()

    def __call__(self, request):
        request.container = container
        return self.get_response(request)

# views.py
def send_notification(request):
    service = request.container[NotificationService]
    result = service.send_welcome_email(request.POST["user_id"])
    return JsonResponse({"success": result})
```

---

## Complete Example

Here's a complete application showing the full dioxide hexagonal architecture workflow:

```python
# ============================================================================
# config.py - Configuration
# ============================================================================
from pydantic_settings import BaseSettings
from dioxide import service

@service
class AppConfig(BaseSettings):
    """Configuration loaded from environment."""
    database_url: str = "sqlite:///dev.db"
    sendgrid_api_key: str = ""

    class Config:
        env_file = ".env"

# ============================================================================
# domain/ports.py - Define protocols (the seams)
# ============================================================================
from typing import Protocol
from datetime import datetime

class UserRepository(Protocol):
    """Port for user data access."""
    async def find_by_id(self, user_id: int) -> User | None: ...
    async def save(self, user: User) -> None: ...

class EmailProvider(Protocol):
    """Port for email sending."""
    async def send(self, to: str, subject: str, body: str) -> None: ...

class Clock(Protocol):
    """Port for time operations."""
    def now(self) -> datetime: ...

# ============================================================================
# domain/services.py - Business logic (pure, no I/O)
# ============================================================================
from dioxide import service
from datetime import timedelta

@service
class NotificationService:
    """Pure business logic - testable without I/O."""

    def __init__(self, users: UserRepository, email: EmailProvider, clock: Clock):
        # Depends on PORTS, not concrete adapters
        self.users = users
        self.email = email
        self.clock = clock

    async def send_welcome_email(self, user_id: int) -> bool:
        """Send welcome email with throttling logic."""
        user = await self.users.find_by_id(user_id)
        if not user:
            return False

        # Throttle: Don't send if sent within 30 days
        if user.last_welcome_sent:
            elapsed = self.clock.now() - user.last_welcome_sent
            if elapsed < timedelta(days=30):
                return False

        # Send email
        await self.email.send(
            to=user.email,
            subject="Welcome!",
            body=f"Hello {user.name}, welcome to our service!"
        )

        # Update user
        user.last_welcome_sent = self.clock.now()
        await self.users.save(user)
        return True

# ============================================================================
# adapters/postgres.py - Production database
# ============================================================================
from dioxide import adapter, Profile, service
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

@service
class Database:
    """Database connection - shared across all repositories."""
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine: AsyncEngine = None

    async def __aenter__(self):
        self.engine = create_async_engine(self.config.database_url)
        return self

    async def __aexit__(self, *args):
        await self.engine.dispose()

@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class PostgresUserRepositoryAdapter:
    """Production user repository using PostgreSQL."""
    def __init__(self, db: Database):
        self.db = db

    async def find_by_id(self, user_id: int) -> User | None:
        async with self.db.engine.begin() as conn:
            row = await conn.execute(
                "SELECT * FROM users WHERE id = ?", user_id
            )
            return User(**row) if row else None

    async def save(self, user: User) -> None:
        async with self.db.engine.begin() as conn:
            await conn.execute(
                "UPDATE users SET last_welcome_sent = ? WHERE id = ?",
                user.last_welcome_sent, user.id
            )

# ============================================================================
# adapters/sendgrid.py - Production email
# ============================================================================
@adapter.for_(EmailProvider, profile=Profile.PRODUCTION)
class SendGridEmailAdapter:
    """Production email using SendGrid API."""
    def __init__(self, config: AppConfig):
        self.api_key = config.sendgrid_api_key

    async def send(self, to: str, subject: str, body: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"to": to, "subject": subject, "body": body}
            )

# ============================================================================
# adapters/system_clock.py - Real time
# ============================================================================
@adapter.for_(Clock, profile=Profile.PRODUCTION)
class SystemClockAdapter:
    """Production clock using system time."""
    def now(self) -> datetime:
        return datetime.now(UTC)

# ============================================================================
# adapters/memory.py - Fast fakes for testing/dev
# ============================================================================
@adapter.for_(UserRepository, profile=[Profile.TEST, Profile.DEVELOPMENT])
class InMemoryUserRepositoryAdapter:
    """In-memory user repository for testing and development."""
    def __init__(self):
        self.users: dict[int, User] = {}

    async def find_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def save(self, user: User) -> None:
        self.users[user.id] = user

    def seed(self, *users: User) -> None:
        """Seed with test data - only available in fakes!"""
        for user in users:
            self.users[user.id] = user

@adapter.for_(EmailProvider, profile=[Profile.TEST, Profile.DEVELOPMENT])
class FakeEmailAdapter:
    """Fake email that captures sends in memory."""
    def __init__(self):
        self.outbox = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject, "body": body})
        # Dev mode can inspect outbox for debugging
        print(f"📧 Fake email to {to}: {subject}")

@adapter.for_(Clock, profile=Profile.TEST)
class FakeClockAdapter:
    """Controllable fake clock for testing time-dependent logic."""
    def __init__(self):
        self._now = datetime(2024, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def set_time(self, dt: datetime) -> None:
        """Set current time - only available in fakes!"""
        self._now = dt

# ============================================================================
# main.py - Production entry point
# ============================================================================
from dioxide import Container, Profile
from fastapi import FastAPI

async def main():
    # Set up container with production profile
    container = Container()
    container.scan(profile=Profile.PRODUCTION)

    # Run application (Database initialized automatically)
    app = FastAPI()

    @app.post("/notifications")
    async def notify(user_id: int):
        service = container.resolve(NotificationService)
        result = await service.send_welcome_email(user_id)
        return {"success": result}

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================================================
# tests/conftest.py - Shared test fixtures
# ============================================================================
import pytest
from dioxide import Container, Profile

@pytest.fixture
def container():
    """Create test container with fakes."""
    c = Container()
    c.scan(profile=Profile.TEST)
    return c

@pytest.fixture
def fake_users(container) -> InMemoryUserRepositoryAdapter:
    """Get the fake user repository adapter."""
    return container.resolve(UserRepository)

@pytest.fixture
def fake_email(container) -> FakeEmailAdapter:
    """Get the fake email adapter."""
    return container.resolve(EmailProvider)

@pytest.fixture
def fake_clock(container) -> FakeClockAdapter:
    """Get the fake clock adapter."""
    return container.resolve(Clock)

@pytest.fixture
def notification_service(container) -> NotificationService:
    """Get the notification service with all fakes injected."""
    return container.resolve(NotificationService)

# ============================================================================
# tests/test_notification.py - Testing
# ============================================================================
import pytest
from datetime import datetime, UTC

async def it_sends_welcome_email(
    notification_service,
    fake_users,
    fake_email,
    fake_clock
):
    """Sends welcome email to new user."""
    # Arrange
    fake_users.seed(User(id=1, email="alice@example.com", name="Alice"))
    fake_clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))

    # Act
    result = await notification_service.send_welcome_email(1)

    # Assert
    assert result is True
    assert len(fake_email.outbox) == 1
    assert fake_email.outbox[0]["to"] == "alice@example.com"
    assert fake_email.outbox[0]["subject"] == "Welcome!"

async def it_throttles_when_already_sent_within_30_days(
    notification_service,
    fake_users,
    fake_email,
    fake_clock
):
    """Does not send welcome email if already sent within 30 days."""
    # Arrange - User already received welcome email
    fake_users.seed(User(
        id=1,
        email="alice@example.com",
        name="Alice",
        last_welcome_sent=datetime(2024, 1, 1, tzinfo=UTC)
    ))
    fake_clock.set_time(datetime(2024, 1, 15, tzinfo=UTC))  # 14 days later

    # Act
    result = await notification_service.send_welcome_email(1)

    # Assert - Throttled, no email sent
    assert result is False
    assert len(fake_email.outbox) == 0

async def it_returns_false_when_user_not_found(notification_service, fake_email):
    """Returns False when user does not exist."""
    # Act
    result = await notification_service.send_welcome_email(999)

    # Assert
    assert result is False
    assert len(fake_email.outbox) == 0

# ============================================================================
# dev.py - Local development
# ============================================================================
async def dev_main():
    # Development mode: in-memory storage, fake email
    container = Container()
    container.scan(profile=Profile.DEVELOPMENT)

    # Seed with dev data
    users = container.resolve(UserRepository)
    users.seed(
        User(id=1, email="dev@example.com", name="Dev User"),
        User(id=2, email="test@example.com", name="Test User"),
    )

    # Run dev server (no Postgres, no SendGrid needed!)
    print("Dev environment ready!")
    print("Using in-memory database and fake email")
    # ... run app
```

---

## What We're NOT Building

To maintain focus and ship the MLP, we explicitly exclude:

### ❌ Configuration Management

**Not our job.** Use Pydantic Settings or python-decouple.

```python
# ❌ Don't build this
@service
class AppConfig:
    @value("DATABASE_URL", default="sqlite:///dev.db")
    database_url: str

# ✅ Use existing tools
from pydantic_settings import BaseSettings

@service
class AppConfig(BaseSettings):
    database_url: str = "sqlite:///dev.db"
```

### ❌ Property Injection

**Constructor injection only.** Property injection adds complexity for rare use cases.

```python
# ❌ Don't support this
@service
class UserService:
    repo: UserRepository = inject()  # No property injection

# ✅ Only support this
@service
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
```

### ❌ Method Injection

**Constructor injection only.** Method injection is rarely needed and adds API surface.

```python
# ❌ Don't support this
@service
class UserService:
    @inject
    def process(self, repo: UserRepository):
        pass

# ✅ Inject via constructor
@service
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
```

### ❌ Circular Dependency Resolution

**Circular dependencies are design flaws.** Don't hide them with `Provider[T]` or lazy injection.

```python
# ❌ Don't support this
@service
class A:
    def __init__(self, b: Provider[B]):  # Lazy resolution
        self.b = b

# ✅ Fix the architecture
# If A and B depend on each other, extract shared logic to C
```

### ❌ XML/YAML Configuration

**Python is configuration.** No external config files.

```python
# ❌ Don't support this
# config.yaml
# components:
#   - class: app.UserService
#     scope: singleton

# ✅ Use Python
@service
class UserService:
    pass
```

### ❌ Aspect-Oriented Programming

**Not a goal for MLP.** AOP (decorators, interceptors) can be added post-MLP if needed.

```python
# ❌ Don't build this (yet)
@service
@transactional
@logged
class UserService:
    pass
```

### ❌ Request Scoping (MLP)

**Post-MLP feature.** For now, all services are SINGLETON (adapters selected by profile).

```python
# ❌ Not in MLP
@service.request_scoped  # Wait until post-MLP
class RequestContext:
    pass

# ✅ MLP only supports
@service  # Singleton (core domain)
@adapter.for_(Port, profile=...)  # Profile-based adapter selection
```

---

## Post-MLP Enhancements

These enhancements improve developer ergonomics while maintaining MLP's core principles. They are **explicitly excluded from MLP** to maintain focus, but represent the natural evolution of Dioxide's API.

### Auto-Detecting Protocol Implementations

**Problem:** `@adapter.for_(EmailProvider, profile=...)` is explicit but verbose when you're already inheriting from the Protocol.

**Solution:** Smart `@adapter` decorator that auto-detects Protocol inheritance.

```python
# Current MLP approach (explicit)
@adapter.for_(EmailProvider, profile=Profile.PRODUCTION)
class SendGridEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass

# Post-MLP enhancement (auto-detect)
@adapter(profile=Profile.PRODUCTION)
class SendGridEmailAdapter(EmailProvider):  # Auto-detects EmailProvider!
    async def send(self, to: str, subject: str, body: str) -> None:
        pass
```

**Implementation:**

```python
from typing import Protocol, get_type_hints

def is_protocol(cls) -> bool:
    """Check if a class is a typing.Protocol."""
    return (
        isinstance(cls, type) and
        issubclass(cls, Protocol) and
        cls is not Protocol  # Exclude Protocol itself
    )

def adapter(profile=None):
    """Auto-register adapter, detecting Protocol implementations."""
    def decorator(cls):
        # Check each base class for Protocols
        for base in cls.__bases__:
            if is_protocol(base):
                container._register_adapter(base, cls, profile)

        return cls
    return decorator
```

**Benefits:**

- ✅ **Minimal boilerplate** - Just `@adapter(profile=...)`
- ✅ **Still explicit** - You must inherit from Protocol
- ✅ **Type-safe** - mypy validates Protocol implementation
- ✅ **No metaclass magic** - Simple decorator inspection
- ✅ **Backward compatible** - `@adapter.for_()` still works

**Why Post-MLP:**
- Adds complexity to `@adapter` decorator
- Need to handle edge cases (multiple Protocols, generic Protocols)
- MLP should prove core value first

### Pydantic-Based Profile Configuration

**Problem:** Profile implementations scattered across codebase. No centralized view of "what gets used in production vs test".

**Solution:** Type-safe Python configuration via Pydantic Settings.

```python
from pydantic import BaseSettings
from typing import Type

class DiOxideSettings(BaseSettings):
    """Centralized, type-safe profile configuration."""

    class Production:
        email: Type[EmailProvider] = SendGridEmail
        db: Type[DatabaseProvider] = PostgresDB
        cache: Type[CacheProvider] = RedisCache

    class Test:
        email: Type[EmailProvider] = FakeEmail
        db: Type[DatabaseProvider] = InMemoryDB
        cache: Type[CacheProvider] = DictCache

    class Development:
        email: Type[EmailProvider] = ConsoleEmail
        db: Type[DatabaseProvider] = SQLiteDB
        cache: Type[CacheProvider] = DictCache

# Usage
container.load_profile(DiOxideSettings.Production)
```

**Benefits:**

- ✅ **Type-safe** - mypy validates all types
- ✅ **Centralized** - See all profile mappings in one place
- ✅ **IDE support** - Autocomplete works
- ✅ **Python-native** - No TOML/YAML hell
- ✅ **Validation** - Pydantic ensures correct types at runtime

**Why Post-MLP:**
- Requires `container.load_profile()` API (new surface)
- Pydantic dependency (MLP should minimize dependencies)
- Need to validate against existing decorator-based approach

### Combined Approach: Auto-Detect + Pydantic

**The full vision:**

```python
# Step 1: Define implementations (auto-registered via decorator)
@component
class SendGridEmail(EmailProvider):
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid implementation
        pass

@component
class FakeEmail(EmailProvider):
    def __init__(self):
        self.outbox = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject, "body": body})

# Step 2: Configure profiles (type-safe, centralized)
class Settings(BaseSettings):
    class Production:
        email: Type[EmailProvider] = SendGridEmail

    class Test:
        email: Type[EmailProvider] = FakeEmail

# Step 3: Activate profile
container.load_profile(Settings.Production)

# Step 4: Use it
service = NotificationService()  # EmailProvider auto-injected!
```

**Result:**
- **Minimal boilerplate** - Just `@component` decorator
- **Centralized configuration** - All profiles in one place
- **Type-safe** - mypy validates everything
- **No YAML/TOML** - Pure Python configuration
- **No metaclass magic** - Simple decorator inspection

### Implementation Notes

**Edge cases to handle:**

```python
# Multiple Protocol inheritance
class EmailAndSMS(EmailProvider, SMSProvider):
    pass  # Should register for both Protocols

# Non-Protocol bases mixed with Protocols
class SendGridEmail(EmailProvider, LoggingMixin):
    pass  # Only register EmailProvider, ignore LoggingMixin

# Generic Protocols
class Repository(Protocol[T]):
    def save(self, item: T) -> None: ...

class UserRepository(Repository[User]):
    pass  # Handle generic Protocol correctly
```

### Backward Compatibility

Both approaches coexist:

```python
# Explicit (MLP) - Always supported
@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
    pass

# Auto-detect + Pydantic (Post-MLP) - Optional sugar
@component
class SendGridEmail(EmailProvider):
    pass

class Settings(BaseSettings):
    class Production:
        email: Type[EmailProvider] = SendGridEmail
```

**Decision:** Support both. Auto-detect + Pydantic is ergonomic sugar on top of MLP foundation.

### Why These Are Post-MLP

1. **MLP must prove core value first**
   - Dependency injection works
   - Profile system works
   - Testing without mocks works

2. **These add complexity**
   - Auto-detection needs edge case handling
   - Pydantic adds dependency
   - `container.load_profile()` is new API surface

3. **These are optimizations**
   - Make existing features more ergonomic
   - Don't fundamentally change the model
   - Can be added without breaking changes

**Timeline:** Consider for v0.2.0 after MLP (v0.1.0) proves market fit.

---

## Success Metrics

How do we know Dioxide MLP is successful?

### Qualitative Metrics

1. **Developer Experience**
   - Can set up DI in < 5 minutes
   - Tests don't require mocking frameworks
   - Swapping implementations takes 1 line of code
   - Error messages are actionable

2. **Architecture Quality**
   - Codebases naturally develop clear boundaries
   - Business logic separated from I/O
   - Protocols define seams
   - Tests are fast (no I/O)

3. **Documentation Quality**
   - Users understand the philosophy
   - Examples are copy-pasteable
   - Common patterns are documented
   - Migration guides exist

### Quantitative Metrics

1. **Performance**
   - Dependency resolution < 1μs
   - Container initialization < 10ms for 100 components
   - Zero runtime overhead vs manual DI

2. **Test Speed**
   - Test suite runs 10x faster than with real I/O
   - Zero flaky tests from timing issues
   - Test coverage > 95%

3. **Adoption Indicators**
   - GitHub stars > 100 in first month
   - At least 5 production users
   - 90%+ positive feedback on design

### Must-Have Features for MLP

Before calling this "loveable", we must have:

- ✅ `@adapter.for_(Port, profile=...)` for hexagonal architecture
- ✅ `@service` decorator for core domain logic
- ✅ `Profile` enum system (PRODUCTION, TEST, DEVELOPMENT, etc.)
- ✅ Constructor injection (type-hint based)
- ✅ Container scanning with profile selection
- ✅ `@lifecycle` decorator for initialization and cleanup
- ✅ Circular dependency detection at startup
- ✅ Missing dependency errors at startup
- ✅ FastAPI integration example
- ✅ Comprehensive documentation
- ✅ Testing guide with fakes > mocks philosophy
- ✅ Type-checked (mypy/pyright passes)
- ✅ Rust-backed performance
- ✅ 95%+ test coverage

---

## Implementation Roadmap

### Phase 1: Core DI (Weeks 1-2) ✅ COMPLETE

- [x] `@service` decorator for core domain logic
- [x] Container scanning
- [x] Constructor injection via type hints
- [x] Dependency graph validation
- [x] Circular dependency detection
- [x] Basic error messages

### Phase 2: Hexagonal Architecture (Week 3) ✅ COMPLETE

- [x] `@adapter.for_(Port, profile=...)` decorator
- [x] `Profile` enum (PRODUCTION, TEST, DEVELOPMENT, etc.)
- [x] Profile-based adapter activation
- [x] Port-based resolution (`container.resolve(Port)`)
- [x] Multiple adapter implementations per port

### Phase 3: Lifecycle (Week 4) ✅ COMPLETE

- [x] `@lifecycle` decorator
- [x] `async def initialize()` support
- [x] `async def dispose()` support
- [x] Async context manager support (`async with container`)
- [x] Initialization in dependency order
- [x] Disposal in reverse dependency order

### Phase 4: Polish (Week 5) ✅ COMPLETE

- [x] Excellent error messages
- [x] FastAPI integration
- [x] Documentation
- [x] Testing guide
- [x] Examples

### Phase 5: Performance (Week 6) ✅ COMPLETE

- [x] Rust optimization
- [x] Benchmark suite
- [x] Performance documentation

---

## Decision Framework

When making implementation decisions, ask:

1. **Does this align with the north star?** (Making DIP inevitable)
2. **Does this follow the guiding principles?** (Type-safe, explicit, Pythonic)
3. **Is this in scope for MLP?** (Check exclusions list)
4. **Will this make testing easier?** (Fakes > mocks)
5. **Can we defer this to post-MLP?** (Simplicity over features)

**When in doubt, choose:**
- Explicit over clever
- Type-safe over flexible
- Simple over complete
- Pythonic over ported patterns

---

## Conclusion

Dioxide exists to make clean architecture feel inevitable. By making the Dependency Inversion Principle trivial to apply, we enable developers to write maintainable, testable code by default.

The MLP focuses ruthlessly on this core mission:
- Type-safe dependency injection
- Profile-based implementation swapping
- Testing without mocks
- Zero ceremony

Everything else is noise. Ship the core, prove the value, then iterate.

**North Star:** Make the right thing (DIP, ports-and-adapters, testable architecture) the path of least resistance.

---

**This document is the canonical reference for all Dioxide MLP development. When in doubt, return to this document.**
