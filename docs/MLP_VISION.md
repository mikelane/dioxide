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

### The @component Decorator

The foundation of Dioxide. Marks classes for dependency injection.

```python
from dioxide import component

# Simple component (singleton by default)
@component
class UserRepository:
    def __init__(self, db: Database):
        self.db = db

# Factory scope (new instance each time)
@component.factory
class RequestHandler:
    def __init__(self, service: UserService):
        self.service = service

# Implementing a protocol (for multiple implementations)
from typing import Protocol

class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

@component.implements(EmailProvider)
class SendGridEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Implementation
        pass
```

**Key behaviors:**

1. **Singleton by default** - One instance shared across application
2. **Constructor injection** - Dependencies resolved from type hints
3. **Type-safe** - mypy validates all dependencies exist
4. **Lazy initialization** - Components created on first use

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

### Lifecycle: Protocols Over Decorators

Components can implement lifecycle protocols for initialization and cleanup.

```python
from dioxide import component, Initializable, Disposable

@component
class Database(Initializable, Disposable):
    """Component with lifecycle management."""

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

**Why protocols instead of decorators?**

- Type-checker validates signatures
- IDE provides autocomplete
- Well-known method names (`initialize`, `dispose`)
- Explicit over magical

---

## Profile System

### The Problem

Different environments need different implementations:
- **Production:** PostgreSQL, SendGrid, AWS S3
- **Testing:** In-memory, fake email, local files
- **Development:** SQLite, console email, local storage

### The Solution: Profiles

Tag implementations with profiles. Dioxide activates only matching implementations.

```python
from dioxide import component, profile

# Define a protocol
from typing import Protocol

class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Multiple implementations, different profiles
@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
    """Real email - production only."""
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API call
        pass

@component.implements(EmailProvider)
@profile.test
class FakeEmail:
    """Fast fake - testing only."""
    def __init__(self):
        self.outbox = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject, "body": body})

@component.implements(EmailProvider)
@profile.development
class ConsoleEmail:
    """Dev email - prints to console."""
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"📧 To: {to}\n   Subject: {subject}\n   Body: {body}")
```

**Activation:**

```python
from dioxide import container

# Production
container.scan("app", profile="production")
# Only SendGridEmail is active

# Testing
container.scan("app", profile="test")
# Only FakeEmail is active

# Development
container.scan("app", profile="development")
# Only ConsoleEmail is active
```

### Profile Implementation: Hybrid Approach

The `@profile` marker uses magic `__getattr__` to support any attribute, but pre-defines common ones for IDE autocomplete.

```python
# dioxide/profile.py implementation
class ProfileMarker:
    """
    Magic profile marker supporting any attribute name.
    Common profiles pre-defined for IDE autocomplete.
    """

    # Pre-defined for IDE autocomplete (type hints only)
    production: 'ProfileDecorator'
    test: 'ProfileDecorator'
    development: 'ProfileDecorator'
    staging: 'ProfileDecorator'

    def __init__(self):
        # Pre-populate common profiles
        for name in ['production', 'test', 'development', 'staging']:
            setattr(self, name, self._make_decorator(name))

    def _make_decorator(self, name: str):
        """Create a decorator for a single profile."""
        def decorator(cls):
            profiles = getattr(cls, '__dioxide_profiles__', set())
            cls.__dioxide_profiles__ = profiles | {name}
            return cls
        return decorator

    def __getattr__(self, name: str):
        """Catch-all for custom profiles (infinite flexibility)."""
        return self._make_decorator(name)

    def __call__(self, *names: str):
        """Multiple profiles via function call syntax."""
        def decorator(cls):
            profiles = getattr(cls, '__dioxide_profiles__', set())
            cls.__dioxide_profiles__ = profiles | set(names)
            return cls
        return decorator

profile = ProfileMarker()
```

**Usage patterns:**

```python
# Common profiles (IDE autocomplete works)
@profile.production
@profile.test
@profile.development
@profile.staging

# Custom profiles (infinite flexibility via __getattr__)
@profile.ci
@profile.integration
@profile.my_laptop
@profile.fridays_only

# Multiple profiles (call syntax)
@profile("test", "development")
@profile("production", "staging")
```

**Why hybrid?**

1. **IDE support** - Common profiles have autocomplete
2. **Infinite flexibility** - Any custom profile works via `__getattr__`
3. **Pythonic** - Same pattern as `pytest.mark`
4. **Zero registration** - Just use any name

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

Here's a complete application showing the full dioxide workflow:

```python
# ============================================================================
# config.py - Configuration
# ============================================================================
from pydantic_settings import BaseSettings
from dioxide import component

@component
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
    async def find_by_id(self, user_id: int) -> User | None: ...
    async def save(self, user: User) -> None: ...

class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

class Clock(Protocol):
    def now(self) -> datetime: ...

# ============================================================================
# domain/services.py - Business logic (pure, no I/O)
# ============================================================================
from dioxide import component
from datetime import timedelta

@component
class NotificationService:
    """Pure business logic - testable without I/O."""

    def __init__(self, users: UserRepository, email: EmailProvider, clock: Clock):
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
from dioxide import component, profile, Initializable, Disposable
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

@component
@profile.production
class Database(Initializable, Disposable):
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine: AsyncEngine = None

    async def initialize(self):
        self.engine = create_async_engine(self.config.database_url)

    async def dispose(self):
        await self.engine.dispose()

@component.implements(UserRepository)
@profile.production
class PostgresUserRepository:
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
@component.implements(EmailProvider)
@profile.production
class SendGridEmail:
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
@component.implements(Clock)
@profile.production
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

# ============================================================================
# adapters/memory.py - Fast fakes for testing/dev
# ============================================================================
@component.implements(UserRepository)
@profile("test", "development")  # Multiple profiles
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

@component.implements(EmailProvider)
@profile("test", "development")
class FakeEmail:
    def __init__(self):
        self.outbox = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject, "body": body})
        if hasattr(self, '_print'):  # Dev mode prints
            print(f"📧 {to}: {subject}")

@component.implements(Clock)
@profile.test
class FakeClock:
    def __init__(self):
        self._now = datetime(2024, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def set_time(self, dt: datetime) -> None:
        self._now = dt

# ============================================================================
# main.py - Production entry point
# ============================================================================
from dioxide import container
from fastapi import FastAPI

async def main():
    # Set up container
    container.scan("app", profile="production")

    async with container:
        # Run application
        app = FastAPI()

        @app.post("/notifications")
        async def notify(user_id: int):
            service = NotificationService()
            result = await service.send_welcome_email(user_id)
            return {"success": result}

        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

# ============================================================================
# tests/test_notification.py - Testing
# ============================================================================
import pytest
from dioxide import container

@pytest.fixture(autouse=True)
def setup_container():
    container.scan("app", profile="test")
    yield
    container.reset()

async def test_welcome_email_sent():
    # Arrange
    users = container[UserRepository]
    users.seed(User(id=1, email="alice@example.com", name="Alice"))

    clock = container[Clock]
    clock.set_time(datetime(2024, 1, 1, tzinfo=UTC))

    # Act
    service = NotificationService()
    result = await service.send_welcome_email(1)

    # Assert
    assert result is True
    email = container[EmailProvider]
    assert len(email.outbox) == 1

async def test_throttling():
    # Arrange
    users = container[UserRepository]
    users.seed(User(
        id=1,
        email="alice@example.com",
        last_welcome_sent=datetime(2024, 1, 1, tzinfo=UTC)
    ))

    clock = container[Clock]
    clock.set_time(datetime(2024, 1, 15, tzinfo=UTC))  # 14 days later

    # Act
    service = NotificationService()
    result = await service.send_welcome_email(1)

    # Assert
    assert result is False  # Throttled
    email = container[EmailProvider]
    assert len(email.outbox) == 0

# ============================================================================
# dev.py - Local development
# ============================================================================
async def dev_main():
    container.scan("app", profile="development")

    # Seed with dev data
    users = container[UserRepository]
    users.seed(
        User(id=1, email="dev@example.com", name="Dev User"),
        User(id=2, email="test@example.com", name="Test User"),
    )

    # Run dev server (no Postgres, no SendGrid needed!)
    async with container:
        print("Dev environment ready!")
        # ... run app
```

---

## What We're NOT Building

To maintain focus and ship the MLP, we explicitly exclude:

### ❌ Configuration Management

**Not our job.** Use Pydantic Settings or python-decouple.

```python
# ❌ Don't build this
@component
class AppConfig:
    @value("DATABASE_URL", default="sqlite:///dev.db")
    database_url: str

# ✅ Use existing tools
from pydantic_settings import BaseSettings

@component
class AppConfig(BaseSettings):
    database_url: str = "sqlite:///dev.db"
```

### ❌ Property Injection

**Constructor injection only.** Property injection adds complexity for rare use cases.

```python
# ❌ Don't support this
@component
class UserService:
    repo: UserRepository = inject()  # No property injection

# ✅ Only support this
@component
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
```

### ❌ Method Injection

**Constructor injection only.** Method injection is rarely needed and adds API surface.

```python
# ❌ Don't support this
@component
class UserService:
    @inject
    def process(self, repo: UserRepository):
        pass

# ✅ Inject via constructor
@component
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
```

### ❌ Circular Dependency Resolution

**Circular dependencies are design flaws.** Don't hide them with `Provider[T]` or lazy injection.

```python
# ❌ Don't support this
@component
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
@component
class UserService:
    pass
```

### ❌ Aspect-Oriented Programming

**Not a goal for MLP.** AOP (decorators, interceptors) can be added post-MLP if needed.

```python
# ❌ Don't build this (yet)
@component
@transactional
@logged
class UserService:
    pass
```

### ❌ Request Scoping (MLP)

**Post-MLP feature.** For now, SINGLETON and FACTORY only.

```python
# ❌ Not in MLP
@component.request_scoped  # Wait until post-MLP
class RequestContext:
    pass

# ✅ MLP only supports
@component  # Singleton
@component.factory  # Factory
```

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

- ✅ `@component` decorator (singleton + factory)
- ✅ `@component.implements(Protocol)` for multiple implementations
- ✅ `@profile` system with common + custom profiles
- ✅ Constructor injection (type-hint based)
- ✅ Container scanning with profile selection
- ✅ Lifecycle protocols (`Initializable`, `Disposable`)
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

### Phase 1: Core DI (Weeks 1-2)

- [ ] `@component` decorator (singleton only)
- [ ] Container scanning
- [ ] Constructor injection via type hints
- [ ] Dependency graph validation
- [ ] Circular dependency detection
- [ ] Basic error messages

### Phase 2: Profiles (Week 3)

- [ ] `@profile` marker with hybrid approach
- [ ] Profile-based component activation
- [ ] `@component.implements(Protocol)`
- [ ] Multiple implementations support

### Phase 3: Lifecycle (Week 4)

- [ ] `Initializable` protocol
- [ ] `Disposable` protocol
- [ ] Async context manager support
- [ ] `@component.factory` scope

### Phase 4: Polish (Week 5)

- [ ] Excellent error messages
- [ ] FastAPI integration
- [ ] Documentation
- [ ] Testing guide
- [ ] Examples

### Phase 5: Performance (Week 6)

- [ ] Rust optimization
- [ ] Benchmark suite
- [ ] Performance documentation

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
