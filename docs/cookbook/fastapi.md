# FastAPI Integration

Recipes for integrating dioxide with FastAPI applications.

---

## Recipe: Basic FastAPI Setup

### Problem

You want to set up a FastAPI application with dioxide dependency injection, ensuring proper initialization and cleanup of resources.

### Solution

Use FastAPI's lifespan context manager to integrate with dioxide's container lifecycle.

### Code

```python
"""FastAPI application with dioxide integration."""
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dioxide import Container, Profile
from fastapi import FastAPI

# Get profile from environment
profile_name = os.getenv("PROFILE", "development")
profile = Profile(profile_name)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize container on startup, cleanup on shutdown."""
    async with Container(profile=profile) as container:
        # All @lifecycle adapters are now initialized
        # Store container for route access
        app.state.container = container
        yield
    # All @lifecycle adapters are now disposed


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "profile": profile.value}
```

### Explanation

1. **Profile from environment**: Read `PROFILE` env var to determine which adapters to use
2. **Container scan**: Discovers all `@adapter` and `@service` decorated classes
3. **Lifespan integration**: The `async with container` pattern ensures `@lifecycle` components are properly initialized and disposed
4. **Clean shutdown**: On SIGTERM, FastAPI's lifespan exits, triggering container cleanup

---

## Recipe: Inject Services into Routes

### Problem

You want to inject dioxide services into FastAPI route handlers using FastAPI's dependency injection.

### Solution

Create a helper function that resolves from the container, then use `Depends()`.

### Code

```python
"""Injecting dioxide services into FastAPI routes."""
from typing import Protocol

from dioxide import Container, Profile, adapter, service
from fastapi import Depends, FastAPI

# Domain port
class EmailPort(Protocol):
    async def send(self, to: str, subject: str) -> None: ...

# Service depending on port
@service
class NotificationService:
    def __init__(self, email: EmailPort) -> None:
        self.email = email

    async def notify_user(self, user_email: str, message: str) -> None:
        await self.email.send(user_email, message)

# Container setup (created during app lifespan, shown here for clarity)
container: Container  # Will be set during lifespan

# Dependency injection helper
def get_notification_service() -> NotificationService:
    """Resolve NotificationService from dioxide container."""
    return container.resolve(NotificationService)

# FastAPI app
app = FastAPI()

@app.post("/notify/{user_email}")
async def notify_user(
    user_email: str,
    message: str,
    service: NotificationService = Depends(get_notification_service),
) -> dict[str, str]:
    """Send notification to user."""
    await service.notify_user(user_email, message)
    return {"status": "sent", "to": user_email}
```

### Explanation

1. **Helper function**: `get_notification_service()` wraps `container.resolve()`
2. **Depends()**: FastAPI's standard dependency injection mechanism
3. **Type hints**: Full type safety - IDE knows `service` is `NotificationService`
4. **Profile determines adapter**: The actual email adapter depends on which profile was scanned

**Alternative: Generic resolver factory**

```python
from typing import TypeVar

T = TypeVar("T")

def inject(cls: type[T]) -> T:
    """Generic resolver for any dioxide component."""
    def _resolve() -> T:
        return container.resolve(cls)
    return Depends(_resolve)

# Usage
@app.post("/notify/{user_email}")
async def notify_user(
    user_email: str,
    service: NotificationService = inject(NotificationService),
) -> dict[str, str]:
    ...
```

---

## Recipe: Testing FastAPI Endpoints

### Problem

You want to test FastAPI endpoints that use dioxide services, with fast fakes instead of real implementations.

### Solution

Set the TEST profile before importing the app, then use FastAPI's TestClient.

### Code

```python
"""Testing FastAPI endpoints with dioxide fakes."""
import os

import pytest
from fastapi.testclient import TestClient

# Set TEST profile BEFORE importing the app
os.environ["PROFILE"] = "test"

from app.main import app, container
from app.domain.ports import EmailPort


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def fake_email():
    """Get fake email adapter for verification."""
    return container.resolve(EmailPort)


@pytest.fixture(autouse=True)
def clear_fakes(fake_email):
    """Clear fake state before each test."""
    fake_email.sent_emails.clear()
    yield


class DescribeNotifyEndpoint:
    """Tests for POST /notify endpoint."""

    def it_sends_notification_email(self, client, fake_email):
        """Sends email when notification requested."""
        response = client.post(
            "/notify/alice@example.com",
            params={"message": "Hello!"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sent"

        # Verify email was sent via fake
        assert len(fake_email.sent_emails) == 1
        assert fake_email.sent_emails[0]["to"] == "alice@example.com"

    def it_returns_400_for_invalid_email(self, client, fake_email):
        """Returns error for invalid email format."""
        response = client.post(
            "/notify/not-an-email",
            params={"message": "Hello!"},
        )

        assert response.status_code == 400
        assert len(fake_email.sent_emails) == 0
```

### Explanation

1. **Profile before import**: Set `PROFILE=test` before importing app so container scans TEST adapters
2. **TestClient**: FastAPI's test client handles lifespan automatically
3. **Fake verification**: Access fake adapters to verify side effects
4. **Clear state**: Reset fakes between tests for isolation
5. **BDD naming**: Use `Describe*` and `it_*` pattern for clear test names

---

## Recipe: Custom Middleware with dioxide

### Problem

You want to access dioxide services from custom FastAPI middleware.

### Solution

Access the container directly in middleware (it's a module-level singleton).

### Code

```python
"""Custom middleware using dioxide services."""
import time
from typing import Protocol

from dioxide import Container, Profile, adapter, service
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics port
class MetricsPort(Protocol):
    def record_request(self, path: str, duration_ms: float) -> None: ...

# Production metrics adapter
@adapter.for_(MetricsPort, profile=Profile.PRODUCTION)
class DatadogMetricsAdapter:
    def record_request(self, path: str, duration_ms: float) -> None:
        # Send to Datadog
        pass

# Test fake
@adapter.for_(MetricsPort, profile=Profile.TEST)
class FakeMetricsAdapter:
    def __init__(self):
        self.recorded: list[dict] = []

    def record_request(self, path: str, duration_ms: float) -> None:
        self.recorded.append({"path": path, "duration_ms": duration_ms})

# Container (created during app lifespan)
container: Container  # Will be set during lifespan


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that records request metrics."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000

        # Access dioxide service
        metrics = container.resolve(MetricsPort)
        metrics.record_request(request.url.path, duration_ms)

        return response


app = FastAPI()
app.add_middleware(MetricsMiddleware)
```

### Explanation

1. **Module-level container**: Middleware can access the same container instance
2. **Resolve per request**: Each request resolves fresh (though singletons return same instance)
3. **Profile determines implementation**: TEST profile uses fake that captures metrics for testing
4. **Metrics verification in tests**: Access fake to verify metrics were recorded

---

## Recipe: Multiple Routers with Shared Container

### Problem

You have multiple FastAPI routers that all need access to dioxide services.

### Solution

Create routers with dependency injection helpers, then include them in the main app.

### Code

```python
"""Multiple routers sharing dioxide container."""
from dioxide import Container, Profile, service
from fastapi import APIRouter, Depends, FastAPI

# Services
@service
class UserService:
    async def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Alice"}

@service
class OrderService:
    async def get_orders(self, user_id: str) -> list[dict]:
        return [{"id": "1", "user_id": user_id, "total": 99.99}]

# Container (shared, created during app lifespan)
container: Container  # Will be set during lifespan

# Dependency helpers
def get_user_service() -> UserService:
    return container.resolve(UserService)

def get_order_service() -> OrderService:
    return container.resolve(OrderService)

# Users router
users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/{user_id}")
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> dict:
    return await service.get_user(user_id)

# Orders router
orders_router = APIRouter(prefix="/orders", tags=["orders"])

@orders_router.get("/user/{user_id}")
async def get_user_orders(
    user_id: str,
    service: OrderService = Depends(get_order_service),
) -> list[dict]:
    return await service.get_orders(user_id)

# Main app
app = FastAPI()
app.include_router(users_router)
app.include_router(orders_router)
```

### Explanation

1. **Shared container**: All routers use the same container instance
2. **Separate dependency helpers**: Each router can have its own helpers if needed
3. **Router independence**: Routers are self-contained, just need the container
4. **Testability**: Each router can be tested independently with TEST profile

---

## Recipe: Background Tasks with dioxide

### Problem

You want to use dioxide services in FastAPI background tasks.

### Solution

Resolve services within the background task function (container is available).

### Code

```python
"""Background tasks with dioxide services."""
from typing import Protocol

from dioxide import Container, Profile, adapter, service
from fastapi import BackgroundTasks, FastAPI

# Email port
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

@service
class EmailService:
    def __init__(self, email: EmailPort) -> None:
        self.email = email

    async def send_welcome(self, user_email: str, name: str) -> None:
        await self.email.send(
            to=user_email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our service!",
        )

# Container (created during app lifespan)
container: Container  # Will be set during lifespan


async def send_welcome_email_task(user_email: str, name: str) -> None:
    """Background task to send welcome email."""
    # Resolve service inside the task
    email_service = container.resolve(EmailService)
    await email_service.send_welcome(user_email, name)


app = FastAPI()


@app.post("/users")
async def create_user(
    name: str,
    email: str,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Create user and send welcome email in background."""
    # Create user synchronously
    user_id = "123"  # From your database

    # Queue background email
    background_tasks.add_task(send_welcome_email_task, email, name)

    return {"id": user_id, "name": name, "email": email}
```

### Explanation

1. **Resolve in task**: Background tasks run after response, but container is still available
2. **Async task**: Use `async def` for background tasks that use async services
3. **Same container**: Background task uses same container, same singletons
4. **Testing**: With TEST profile, fake email captures what would be sent

---

## See Also

- [Testing Patterns](testing.md) - More testing recipes
- [Configuration](configuration.md) - Environment-specific config
- [examples/fastapi/](https://github.com/mikelane/dioxide/tree/main/examples/fastapi) - Complete working example
