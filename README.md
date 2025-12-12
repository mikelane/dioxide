<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/mikelane/dioxide/main/docs/_static/images/dioxide-logo-light.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/mikelane/dioxide/main/docs/_static/images/dioxide-logo-dark.png">
    <img alt="dioxide logo" src="https://raw.githubusercontent.com/mikelane/dioxide/main/docs/_static/images/dioxide-logo-dark.png" width="200">
  </picture>
</p>

<p align="center">
  <strong>Zero-ceremony dependency injection for Python with built-in hexagonal architecture</strong>
</p>

[![CI](https://github.com/mikelane/dioxide/workflows/CI/badge.svg)](https://github.com/mikelane/dioxide/actions)
[![Release](https://github.com/mikelane/dioxide/actions/workflows/release-automated.yml/badge.svg)](https://github.com/mikelane/dioxide/actions/workflows/release-automated.yml)
[![PyPI version](https://badge.fury.io/py/dioxide.svg)](https://pypi.org/project/dioxide/)
[![Documentation](https://readthedocs.org/projects/dioxide/badge/?version=latest)](https://dioxide.readthedocs.io/en/latest/?badge=latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/dioxide.svg)](https://pypi.org/project/dioxide/)
[![Platform Support](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue)](https://github.com/mikelane/dioxide)
[![Architecture](https://img.shields.io/badge/arch-x86__64%20%7C%20aarch64-green)](https://github.com/mikelane/dioxide)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **[📖 Read the Documentation](https://dioxide.readthedocs.io)** | **[🚀 Quick Start](#quick-start)** | **[💡 Examples](https://dioxide.readthedocs.io/en/latest/examples/)** | **[📋 API Reference](https://dioxide.readthedocs.io/en/latest/api/dioxide/)**

---

## Overview

`dioxide` is a dependency injection framework for Python designed to make clean architecture the path of least resistance:

- **Zero-ceremony API** - Just type hints and decorators, no XML or configuration files
- **Built-in Profile system** - Swap PostgreSQL for in-memory with `profile=Profile.TEST`
- **Hexagonal architecture made easy** - `@adapter.for_(Port)` and `@service` guide you to clean code
- **Type safety** - Full mypy and pyright support; if it type-checks, it wires correctly
- **Rust-backed** - Fast container operations via PyO3 for competitive runtime performance

## Installation

```bash
pip install dioxide
```

### Platform Support

| Platform | x86_64 | ARM64/aarch64 |
|----------|--------|---------------|
| Linux    | ✅     | ✅            |
| macOS    | ✅     | ✅ (M1/M2/M3) |
| Windows  | ✅     | ❌            |

**Python Versions**: 3.11, 3.12, 3.13, 3.14

## Status

**STABLE**: dioxide v1.0.0 is production-ready with a stable, frozen API.

- **Latest Release**: [v1.0.0](https://github.com/mikelane/dioxide/releases/tag/v1.0.0) - Published to PyPI
- **API Status**: Frozen - No breaking changes until v2.0
- **Production Ready**: All MLP features complete, comprehensive test coverage, battle-tested

**Migrating from alpha/beta versions?** See [MIGRATION.md](MIGRATION.md) for the complete migration guide.

See [Issues](https://github.com/mikelane/dioxide/issues) for current work and planned enhancements.

## Why dioxide?

**Make the Dependency Inversion Principle feel inevitable.**

dioxide exists to make clean architecture (ports-and-adapters) the path of least resistance:

| What you get | How dioxide helps |
|--------------|-------------------|
| **Testable code** | Profile system swaps real adapters for fakes with one line |
| **Type-safe wiring** | If mypy passes, your dependencies are correct |
| **Clean boundaries** | `@adapter.for_(Port)` makes seams explicit and visible |
| **Fast tests** | In-memory fakes, not slow mocks or external services |
| **Competitive performance** | Rust-backed container with sub-microsecond resolution |

See [MLP_VISION.md](docs/MLP_VISION.md) for the complete design philosophy and [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for testing patterns.

## Quick Start

dioxide embraces **hexagonal architecture** (ports-and-adapters) to make clean, testable code the path of least resistance.

```python
from typing import Protocol
from dioxide import Container, Profile, adapter, service

# 1. Define port (interface) - your seam
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# 2. Create adapters (implementations) for different environments
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        print(f"📧 Sending via SendGrid to {to}: {subject}")

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        print(f"✅ Fake email sent to {to}")

# 3. Create service (core business logic) - depends on port, not adapter
@service
class UserService:
    def __init__(self, email: EmailPort):
        self.email = email

    async def register_user(self, email_addr: str, name: str):
        # Core logic doesn't know/care which adapter is active
        await self.email.send(
            to=email_addr,
            subject="Welcome!",
            body=f"Hello {name}, thanks for signing up!"
        )

# Production usage
container = Container()
container.scan(profile=Profile.PRODUCTION)
user_service = container.resolve(UserService)
await user_service.register_user("user@example.com", "Alice")
# 📧 Sends real email via SendGrid

# Testing - just change the profile!
test_container = Container()
test_container.scan(profile=Profile.TEST)
test_service = test_container.resolve(UserService)
await test_service.register_user("test@example.com", "Bob")

# Verify in tests (no mocks!)
fake_email = test_container.resolve(EmailPort)
assert len(fake_email.sent_emails) == 1
assert fake_email.sent_emails[0]["to"] == "test@example.com"
```

**Why this is powerful**:
- ✅ **Type-safe**: If mypy passes, your wiring is correct
- ✅ **Testable**: Fast fakes at the seams, not mocks
- ✅ **Clean**: Business logic has zero knowledge of infrastructure
- ✅ **Simple**: One line change to swap implementations (`profile=...`)
- ✅ **Explicit**: Port definitions make boundaries visible

**Key concepts**:
- **Ports** (`Protocol`): Define what operations you need (the seam)
- **Adapters** (`@adapter.for_(Port, profile=...)`): Concrete implementations
- **Services** (`@service`): Core business logic that depends on ports
- **Profiles** (`Profile.PRODUCTION`, `Profile.TEST`): Environment selection
- **Container**: Auto-wires dependencies based on type hints

## Constructor Dependency Injection

When you create an adapter or service with constructor parameters, dioxide **automatically injects dependencies** based on type hints. This is the core mechanism that makes dependency injection "just work".

### How It Works

When you write:

```python
@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class SqliteUserRepository:
    def __init__(self, db: Connection) -> None:  # <-- type hint tells dioxide what to inject
        self.db = db
```

You might ask: "How does dioxide know where to get `db`?"

The answer: **The dependency must be registered in the container.**

dioxide:
1. Reads the type hints from your constructor (`db: Connection`)
2. Looks up `Connection` in the container registry
3. Resolves `Connection` (creating an instance if needed)
4. Passes it to your constructor

### The Dependency Must Be Registered

Constructor dependencies **must** be registered in the container before dioxide can inject them. There are three ways to register a dependency:

#### Option 1: Make it an Adapter for a Port

The most common pattern - create a port and register an adapter:

```python
from typing import Protocol
from dioxide import Container, Profile, adapter, service

# Define a port (interface) for database connections
class DatabaseConnection(Protocol):
    def execute(self, sql: str) -> Any: ...

# Register an adapter for the port
@adapter.for_(DatabaseConnection, profile=Profile.PRODUCTION)
class SqliteConnection:
    def __init__(self) -> None:
        import sqlite3
        self.conn = sqlite3.connect("app.db")

    def execute(self, sql: str) -> Any:
        return self.conn.execute(sql)

# Now other adapters can depend on DatabaseConnection
@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class SqliteUserRepository:
    def __init__(self, db: DatabaseConnection) -> None:  # Auto-injected!
        self.db = db

    async def get_user(self, user_id: str) -> dict | None:
        result = self.db.execute(f"SELECT * FROM users WHERE id = ?", (user_id,))
        # ...
```

#### Option 2: Make it a Service

If the dependency is core domain logic (not infrastructure), use `@service`:

```python
from dioxide import service

@service
class AppConfig:
    """Configuration loaded from environment."""
    def __init__(self) -> None:
        import os
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///dev.db")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")

# Adapters can depend on services
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:  # Auto-injected!
        self.api_key = config.sendgrid_api_key
```

#### Option 3: Manual Registration

For external dependencies or special cases, register manually:

```python
import sqlite3
from dioxide import Container, Profile

container = Container()

# Register a factory that creates the dependency
container.register_singleton(sqlite3.Connection, lambda: sqlite3.connect("app.db"))

# Now scan - adapters depending on sqlite3.Connection will get it injected
container.scan(profile=Profile.PRODUCTION)
```

### Complete Example: Adapters with Dependencies

Here's a complete example showing adapters that depend on other components:

```python
from typing import Protocol
from dioxide import Container, Profile, adapter, service

# --- Ports (interfaces) ---

class ConfigPort(Protocol):
    """Port for configuration access."""
    def get(self, key: str, default: str = "") -> str:
        """Get configuration value by key."""
        ...

class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

class UserRepository(Protocol):
    async def save(self, user: dict) -> dict: ...
    async def get(self, user_id: str) -> dict | None: ...

# --- Configuration adapter ---

@adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
class EnvConfigAdapter:
    """Configuration from environment variables."""
    def get(self, key: str, default: str = "") -> str:
        import os
        return os.environ.get(key, default)

@adapter.for_(ConfigPort, profile=Profile.TEST)
class FakeConfigAdapter:
    """Fake configuration for testing."""
    def __init__(self) -> None:
        self.values = {"SENDGRID_API_KEY": "test-key", "DATABASE_URL": ":memory:"}

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default)

# --- Email adapter (depends on ConfigPort) ---

@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: ConfigPort) -> None:  # ConfigPort auto-injected!
        self.api_key = config.get("SENDGRID_API_KEY")

    async def send(self, to: str, subject: str, body: str) -> None:
        # Use self.api_key to call SendGrid API
        print(f"Sending via SendGrid to {to}: {subject}")

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self) -> None:  # No dependencies needed for test fake
        self.sent_emails: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# --- Service (depends on ports) ---

@service
class UserService:
    def __init__(self, repo: UserRepository, email: EmailPort) -> None:
        self.repo = repo
        self.email = email

    async def register_user(self, name: str, email_addr: str) -> dict:
        user = await self.repo.save({"name": name, "email": email_addr})
        await self.email.send(email_addr, "Welcome!", f"Hello {name}!")
        return user

# --- Usage ---

container = Container()
container.scan(profile=Profile.PRODUCTION)

# When UserService is resolved:
# 1. dioxide sees UserService needs UserRepository and EmailPort
# 2. Resolves UserRepository -> gets SqliteUserRepository (if registered)
# 3. Resolves EmailPort -> gets SendGridAdapter
# 4. SendGridAdapter needs ConfigPort -> gets EnvConfigAdapter
# 5. Everything is wired up automatically!

service = container.resolve(UserService)
```

### Key Points

1. **Type hints are required**: Constructor parameters must have type hints for injection to work
2. **Dependencies must be registered**: Either via `@adapter.for_()`, `@service`, or manual registration
3. **Resolution is recursive**: If your dependency has dependencies, those are resolved too
4. **Circular dependencies are detected**: dioxide fails fast if A depends on B and B depends on A
5. **Test fakes often have no dependencies**: Fakes are typically simpler and don't need injection

### Common Patterns

**Config Adapter Pattern**: Create a `ConfigPort` that adapters depend on for configuration:

```python
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: ConfigPort) -> None:
        self.api_key = config.get("SENDGRID_API_KEY")
```

**Database Connection Pattern**: Wrap database connections in a port for injection:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: ConfigPort) -> None:
        self.url = config.get("DATABASE_URL")
```

**Test Fakes Without Dependencies**: Test adapters are often simple and don't need dependencies:

```python
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self) -> None:  # No dependencies - just in-memory storage
        self.sent_emails = []
```

## Lifecycle Management

Services and adapters can opt into lifecycle management using the `@lifecycle` decorator for components that need initialization and cleanup:

```python
from dioxide import Container, Profile, service, lifecycle, adapter
from typing import Protocol

# Port for cache operations
class CachePort(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str) -> None: ...

# Production adapter with lifecycle
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    """Redis cache with connection lifecycle."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.redis = None

    async def initialize(self) -> None:
        """Called automatically when container starts."""
        self.redis = await aioredis.create_redis_pool(self.config.redis_url)
        print(f"Redis connected: {self.config.redis_url}")

    async def dispose(self) -> None:
        """Called automatically when container stops."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            print("Redis connection closed")

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str) -> None:
        await self.redis.set(key, value)

# Service with lifecycle
@service
@lifecycle
class Database:
    """Database service with connection lifecycle."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = None

    async def initialize(self) -> None:
        """Called automatically when container starts."""
        self.engine = create_async_engine(self.config.database_url)
        print(f"Database connected: {self.config.database_url}")

    async def dispose(self) -> None:
        """Called automatically when container stops."""
        if self.engine:
            await self.engine.dispose()
            print("Database connection closed")

# Use async context manager for automatic lifecycle
container = Container()
container.scan(profile=Profile.PRODUCTION)

async with container:
    # All @lifecycle components initialized here (in dependency order)
    app = container.resolve(Application)
    await app.run()
# All @lifecycle components disposed here (in reverse order)

# Or manually control lifecycle
await container.start()  # Initialize all @lifecycle components
try:
    app = container.resolve(Application)
    await app.run()
finally:
    await container.stop()  # Dispose all @lifecycle components
```

**Why `@lifecycle`?**
- ✅ **Optional**: Only components that need it use lifecycle (test fakes typically don't!)
- ✅ **Validated**: Decorator ensures `initialize()` and `dispose()` methods exist and are async
- ✅ **Consistent**: Matches dioxide's decorator-based API (`@service`, `@adapter.for_()`)
- ✅ **Type-safe**: Type stubs provide IDE autocomplete and mypy validation
- ✅ **Dependency-ordered**: Components initialized/disposed in correct dependency order

**Key Features**:
- **Async context manager**: `async with container:` handles start/stop automatically
- **Manual control**: `await container.start()` and `await container.stop()` for explicit lifecycle
- **Dependency ordering**: Initialization happens in dependency order (dependencies first)
- **Reverse disposal**: Disposal happens in reverse order (dependents disposed before dependencies)
- **Graceful rollback**: If initialization fails, already-initialized components are disposed
- **Error resilience**: Disposal continues even if individual components fail

**Status**: Fully implemented.

## Function Injection

dioxide works with **any callable**, not just classes. You can inject dependencies into standalone functions, route handlers, and background tasks by using default parameters with `container.resolve()`:

### Standalone Functions

```python
from dioxide import Container, Profile, adapter, service
from typing import Protocol

# Define port
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Set up container
container = Container()
container.scan(profile=Profile.PRODUCTION)

# Standalone function with injected dependencies
async def send_welcome_email(
    user_email: str,
    user_name: str,
    email: EmailPort = container.resolve(EmailPort)
) -> None:
    """Send welcome email using injected email service."""
    await email.send(
        to=user_email,
        subject="Welcome!",
        body=f"Thanks for joining, {user_name}!"
    )

# Call like a normal function
await send_welcome_email("alice@example.com", "Alice")
# EmailPort dependency injected automatically
```

### Route Handlers (Web Frameworks)

Perfect for FastAPI, Flask, or any web framework:

```python
from fastapi import FastAPI, Request
from dioxide import Container, Profile

app = FastAPI()
container = Container()
container.scan(profile=Profile.PRODUCTION)

@app.post("/users")
async def create_user(
    request: Request,
    db: DatabasePort = container.resolve(DatabasePort),
    email: EmailPort = container.resolve(EmailPort)
) -> dict:
    """Create user with injected database and email services."""
    # Parse request
    user_data = await request.json()

    # Use injected dependencies
    user = await db.save_user(user_data)
    await email.send(
        to=user_data["email"],
        subject="Welcome!",
        body=f"Hello {user_data['name']}!"
    )

    return {"id": user.id, "status": "created"}
```

### Background Tasks

Great for Celery, RQ, or any background job system:

```python
from dioxide import Container, Profile
from typing import Protocol

# Define ports
class PaymentPort(Protocol):
    async def charge(self, invoice_id: str) -> dict: ...

class InvoiceEmailPort(Protocol):
    """Port for sending invoice-related emails."""
    async def send_receipt(self, email: str, invoice: dict) -> None: ...

class LoggerPort(Protocol):
    """Port for logging."""
    def info(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...

# Set up container
container = Container()
container.scan(profile=Profile.PRODUCTION)

# Background task with injected dependencies
async def process_invoice(
    invoice_id: str,
    payment: PaymentPort = container.resolve(PaymentPort),
    email: InvoiceEmailPort = container.resolve(InvoiceEmailPort),
    logger: LoggerPort = container.resolve(LoggerPort)
) -> None:
    """Process invoice payment and send receipt."""
    try:
        # Charge payment
        result = await payment.charge(invoice_id)

        # Send receipt
        await email.send_receipt(result["customer_email"], result)

        # Log success
        logger.info(f"Invoice {invoice_id} processed successfully")

    except Exception as e:
        logger.error(f"Failed to process invoice {invoice_id}: {e}")
        raise

# Schedule the task (example with Celery)
@celery_app.task
def process_invoice_task(invoice_id: str):
    """Celery task wrapper."""
    import asyncio
    return asyncio.run(process_invoice(invoice_id))
```

### Testing Functions with Injection

Function injection works seamlessly with the profile system for testing:

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
def test_container():
    """Container with test profile."""
    container = Container()
    container.scan(profile=Profile.TEST)
    return container

async def test_send_welcome_email(test_container):
    """Test function injection with fake email adapter."""
    # Function uses test profile automatically
    await send_welcome_email("test@example.com", "TestUser")

    # Verify with fake adapter
    fake_email = test_container.resolve(EmailPort)
    assert len(fake_email.sent_emails) == 1
    assert fake_email.sent_emails[0]["to"] == "test@example.com"
```

**Why function injection?**
- ✅ **Flexible**: Works with any callable (classes, functions, lambdas)
- ✅ **Practical**: Perfect for route handlers, background jobs, utility functions
- ✅ **Testable**: Same profile system works for function injection
- ✅ **No magic**: Just default parameters with `container.resolve()`
- ✅ **Type-safe**: Full mypy support for injected types

## Testing with dioxide

dioxide makes testing easy through **fakes at the seams** instead of mocks. The key pattern is creating a fresh `Container` instance per test for complete isolation.

> **[📖 Full Testing Guide](https://dioxide.readthedocs.io/en/latest/testing/)** - Comprehensive patterns for testing with dioxide

### Fresh Container Per Test (Recommended)

The simplest approach uses the `fresh_container` helper from `dioxide.testing`:

```python
import pytest
from dioxide import Profile
from dioxide.testing import fresh_container

@pytest.fixture
async def container():
    """Fresh container per test - complete test isolation."""
    async with fresh_container(profile=Profile.TEST) as c:
        yield c
    # Cleanup happens automatically
```

Or create the container manually for more control:

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
async def container():
    """Fresh container per test - complete test isolation.

    Each test gets a fresh Container instance with:
    - Clean singleton cache (no state from previous tests)
    - Fresh adapter instances
    - Automatic lifecycle management via async context manager

    This is the RECOMMENDED pattern for test isolation.
    """
    c = Container()
    c.scan(profile=Profile.TEST)
    async with c:
        yield c
    # Cleanup happens automatically
```

**Why this works:**
- **Complete isolation**: Each test starts with a clean slate
- **No state leakage**: Singletons are scoped to the container instance
- **Lifecycle handled**: `@lifecycle` components are properly initialized/disposed
- **Simple**: No need to track or clear fake state

### Typed Fixtures for Fakes

Create typed fixtures to access your fake adapters with IDE support:

```python
from app.adapters.fakes import FakeEmailAdapter, FakeDatabaseAdapter
from app.domain.ports import EmailPort, DatabasePort

@pytest.fixture
def email(container) -> FakeEmailAdapter:
    """Typed access to fake email for assertions."""
    return container.resolve(EmailPort)

@pytest.fixture
def db(container) -> FakeDatabaseAdapter:
    """Typed access to fake db for seeding test data."""
    return container.resolve(DatabasePort)
```

### Complete Test Example

```python
async def test_user_registration_sends_welcome_email(container, email, db):
    """Test that registering a user sends a welcome email."""
    # Arrange: Get the service (dependencies auto-injected)
    service = container.resolve(UserService)

    # Act: Call the real service with real fakes
    await service.register_user("alice@example.com", "Alice")

    # Assert: Check observable outcomes (no mock verification!)
    assert len(email.sent_emails) == 1
    assert email.sent_emails[0]["to"] == "alice@example.com"
    assert "Welcome" in email.sent_emails[0]["subject"]
```

**Benefits over mocking:**
- **Test real behavior**: Business logic actually runs
- **No brittle mocks**: Tests don't break when you refactor
- **Fast**: In-memory fakes, no I/O
- **Deterministic**: Controllable fakes (FakeClock, etc.)

### Alternative: Reset Container Between Tests

If you need a shared container (e.g., for TestClient integration tests), use `container.reset()`:

```python
from dioxide import container, Profile

@pytest.fixture(autouse=True)
def setup_container():
    """Reset container between tests for isolation."""
    container.scan(profile=Profile.TEST)
    yield
    container.reset()  # Clears singleton cache, keeps registrations
```

Or clear fake state manually if you need more control:

```python
@pytest.fixture(autouse=True)
def clear_fakes():
    """Clear fake state before each test."""
    # Clear adapters from global container before test runs
    db = container.resolve(DatabasePort)
    if hasattr(db, "users"):
        db.users.clear()

    email = container.resolve(EmailPort)
    if hasattr(email, "sent_emails"):
        email.sent_emails.clear()
```

**Note**: The fresh container pattern is preferred because it requires no knowledge of fake internals.

For comprehensive testing patterns, see [TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

## Framework Integrations

dioxide provides seamless integration with popular Python web frameworks.

### FastAPI Integration

```python
from fastapi import FastAPI
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION, packages=["myapp"])

@app.get("/users")
async def list_users(service: UserService = Inject(UserService)):
    return await service.list_all()
```

Install with: `pip install dioxide[fastapi]`

**Features**: Single middleware setup, automatic container lifecycle, REQUEST-scoped components, sync/async support.

See the complete [FastAPI example](examples/fastapi/) for a full hexagonal architecture application.

### Django Integration

```python
# settings.py or apps.py
from dioxide import Profile
from dioxide.django import configure_dioxide

configure_dioxide(profile=Profile.PRODUCTION, packages=["myapp"])

# settings.py - add middleware
MIDDLEWARE = [
    ...
    'dioxide.django.DioxideMiddleware',
    ...
]

# views.py
from dioxide.django import inject

def user_list(request):
    service = inject(UserService)
    return JsonResponse({"users": service.list_all()})
```

Install with: `pip install dioxide[django]`

**Features**: Single function setup, request scoping via middleware, thread-safe injection, works with class-based and function-based views.

### Django REST Framework Integration

dioxide works seamlessly with Django REST Framework - just use the same `inject()` function in your APIViews, ViewSets, or `@api_view` decorated functions:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from dioxide.django import inject

@api_view(['GET'])
def user_list(request):
    service = inject(UserService)
    return Response(service.list_all())

class UserViewSet(APIView):
    def get(self, request):
        service = inject(UserService)
        return Response(service.list_all())
```

**Features**: Full DRF compatibility, works with all DRF view types (APIView, ViewSet, @api_view), request scoping through Django middleware.

See [Django Integration Guide](docs/integrations/django.md) for complete documentation including request scoping and lifecycle management.

## Features

### v1.0.0 STABLE - MLP Production Ready

**Core Dependency Injection**:
- [x] `@adapter.for_(Port, profile=...)` decorator for hexagonal architecture
- [x] `@service` decorator for core business logic
- [x] `Profile` enum (PRODUCTION, TEST, DEVELOPMENT, STAGING, CI, ALL)
- [x] Container with `scan(profile=...)` for profile-based activation
- [x] Port-based resolution (`container.resolve(Port)` returns active adapter)
- [x] Constructor dependency injection via type hints
- [x] Type-safe `Container.resolve()` with full mypy support
- [x] Optional `container[Type]` bracket syntax

**Lifecycle Management**:
- [x] `@lifecycle` decorator for opt-in lifecycle management
- [x] `async with container:` context manager support
- [x] Manual `container.start()` / `container.stop()` methods
- [x] Dependency-ordered initialization (Kahn's algorithm)
- [x] Reverse-order disposal with error resilience
- [x] Graceful rollback on initialization failures

**Test Ergonomics**:
- [x] `fresh_container()` helper for isolated test containers
- [x] `container.reset()` to clear singleton cache between tests
- [x] `scope=Scope.FACTORY` on adapters for fresh instances per resolution
- [x] Complete test isolation with fresh Container per test pattern

**Reliability**:
- [x] Circular dependency detection at startup (fail-fast)
- [x] Excellent error messages with actionable suggestions
- [x] Package scanning: `container.scan(package="app.services")`
- [x] High test coverage (~93%, 213+ tests)
- [x] Full CI/CD automation with multi-platform wheels

**Documentation & Examples**:
- [x] **[ReadTheDocs](https://dioxide.readthedocs.io)** - Full documentation with API reference
- [x] Complete FastAPI integration example
- [x] Comprehensive testing guide (fakes > mocks philosophy)
- [x] Performance benchmarks with [honest comparisons](benchmarks/)
- [x] Tutorials, guides, and architectural patterns
- [x] Migration guides for all versions

**Production Ready**:
- [x] API frozen - No breaking changes until v2.0
- [x] Published to PyPI with cross-platform wheels
- [x] Battle-tested in real applications
- [x] Ready for production deployment

### Post-MLP Features (v1.1.0+)

Future enhancements under consideration:
- Request scoping for web frameworks
- Property injection
- Django integration
- Developer tooling (CLI, IDE plugins)

## Development

### Prerequisites

- Python 3.11+
- Rust 1.70+
- [uv](https://github.com/astral-sh/uv) for Python package management
- [maturin](https://github.com/PyO3/maturin) for building Rust extensions

### Setup

```bash
# Clone the repository
git clone https://github.com/mikelane/dioxide.git
cd dioxide

# Install dependencies with uv (uses PEP 735 dependency groups)
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv sync --group dev

# Build the Rust extension
maturin develop

# Run tests
pytest

# Run all quality checks
tox
```

### Development Workflow

```bash
# Format code
tox -e format

# Lint
tox -e lint

# Type check
tox -e type

# Run tests for all Python versions
tox

# Run tests with coverage
tox -e cov

# Mutation testing
tox -e mutate
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pre-commit install
```

## Architecture

```
dioxide/
├── python/dioxide/       # Python API
│   ├── __init__.py
│   ├── container.py       # Main Container class
│   ├── decorators.py      # @component decorator
│   └── scope.py           # Scope enum
├── rust/src/              # Rust core
│   └── lib.rs             # PyO3 bindings and graph logic
├── tests/                 # Python tests
└── pyproject.toml         # Project configuration
```

### Key Design Decisions

1. **Python-first API** - Developers work in pure Python; Rust is an implementation detail
2. **Type hints as the contract** - Leverage Python's type system for DI metadata
3. **Hexagonal architecture by design** - `@adapter.for_(Port)` makes clean architecture obvious
4. **Profile-based testing** - Built-in support for swapping implementations by environment
5. **Rust for container operations** - Memory-efficient singleton caching and graph traversal
6. **Test-driven development** - Every feature starts with failing tests

## Comparison to Other Frameworks

| Feature | dioxide | dependency-injector | injector |
|---------|----------|---------------------|----------|
| Zero-ceremony API | ✅ | ❌ | ✅ |
| Built-in Profile system | ✅ | ❌ | ❌ |
| Hexagonal architecture support | ✅ | ❌ | ❌ |
| Type-based DI | ✅ | ✅ | ✅ |
| Lifecycle management | ✅ | ✅ | ❌ |
| Circular dependency detection | ✅ | ❌ | ❌ |
| Memory efficiency | ✅ | ⚡ | ⚡ |

**Performance notes**: Both dioxide (Rust/PyO3) and dependency-injector (Cython) offer excellent performance for cached singleton resolution. dependency-injector's mature Cython backend is slightly faster for raw lookups; dioxide is more memory-efficient. Both handle concurrent workloads equally well. See [benchmarks/](benchmarks/) for detailed, honest comparisons.

## Contributing

Contributions are welcome! We follow a strict workflow to maintain code quality:

**Quick start for contributors:**
1. **Create or find an issue** - All work must be associated with a GitHub issue
2. **Fork the repository** (external contributors)
3. **Create a feature branch** with issue reference (e.g., `fix/issue-123-description`)
4. **Follow TDD** - Write tests first, then implementation
5. **Submit a Pull Request** - All changes must go through PR review

**Key requirements:**
- ✅ All work must have an associated GitHub issue
- ✅ All changes must go through the Pull Request process
- ✅ Tests and documentation are mandatory
- ✅ Branch protection enforces these requirements on `main`

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Resources:**
- **[📖 Documentation](https://dioxide.readthedocs.io)** - Full documentation with tutorials and API reference
- **[🗺️ Roadmap](ROADMAP.md)** - Complete product roadmap
- **[💡 Design Philosophy](docs/MLP_VISION.md)** - MLP vision and architectural decisions
- **[🧪 Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive testing patterns (fakes > mocks)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Inspired by [dependency-injector](https://github.com/ets-labs/python-dependency-injector) and Spring Framework
- Built with [PyO3](https://github.com/PyO3/pyo3) and [maturin](https://github.com/PyO3/maturin)
- Graph algorithms powered by [petgraph](https://github.com/petgraph/petgraph)

---

**Production Ready**: dioxide v1.0.0 is production-ready with a stable, frozen API. All MLP (Minimum Loveable Product) features are complete, thoroughly tested, and battle-proven.

**API Guarantee**: No breaking changes until v2.0. Your code written against v1.x will continue to work through all v1.x releases.

**What's Next**:
- **v1.1.0+**: Post-MLP enhancements (request scoping, property injection, additional framework integrations)
- **v2.0.0+**: Major enhancements based on community needs

**Get Started**: **[Read the Documentation](https://dioxide.readthedocs.io)** | **[Install from PyPI](https://pypi.org/project/dioxide/)** | **[View on GitHub](https://github.com/mikelane/dioxide)**
