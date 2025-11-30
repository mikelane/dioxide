# Celery + dioxide: Background Task Scoping Example

This example demonstrates how to use **dioxide** for dependency injection with Celery background tasks, implementing the hexagonal architecture pattern.

## What This Example Demonstrates

1. **Task-Scoped DI**: Fresh dependencies per task execution
2. **Profile-Based Configuration**: Different adapters for production vs testing
3. **Lifecycle Management**: Proper initialization and cleanup of resources
4. **Testing with Fakes**: Fast, deterministic tests using eager mode
5. **Celery Integration**: Container lifecycle integrated with Celery app

## Quick Start

### Installation

```bash
# Clone the repository
cd examples/celery

# Install dependencies
pip install -r requirements-dev.txt

# Or using uv (faster)
uv pip install -r requirements-dev.txt
```

### Running the Worker

```bash
# Start Redis (required as broker)
docker run -d -p 6379:6379 redis:alpine

# Development mode (logging adapters)
PROFILE=development celery -A app.main:celery_app worker --loglevel=info

# Production mode (real adapters)
PROFILE=production DATABASE_URL=postgresql://... celery -A app.main:celery_app worker --loglevel=info
```

### Running Tasks

```python
# In another terminal or application
from app.main import process_order, send_notification

# Queue a task
result = process_order.delay("order-123")
print(result.get())  # Wait for result

# Fire and forget
send_notification.delay("user-456", "Your order shipped!")
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_tasks.py::DescribeOrderProcessing -v
```

## Architecture Overview

### Directory Structure

```
app/
├── main.py              # Celery app + container setup + tasks
├── domain/
│   ├── ports.py         # Port definitions (Protocols)
│   └── services.py      # Business logic (@service)
└── adapters/
    ├── logging.py       # Development adapters (@adapter)
    └── fakes.py         # Test adapters (@adapter)

tests/
├── conftest.py          # Pytest configuration + fixtures
└── test_tasks.py        # Fast tests using eager mode
```

## How It Works

### 1. Define Ports (Interfaces)

```python
# app/domain/ports.py
from typing import Protocol

class OrderPort(Protocol):
    def get_order(self, order_id: str) -> dict: ...
    def update_status(self, order_id: str, status: str) -> None: ...

class NotificationPort(Protocol):
    def send(self, user_id: str, message: str) -> None: ...
```

### 2. Implement Domain Services

```python
# app/domain/services.py
from dioxide import service, Scope

@service
class OrderService:
    def __init__(self, orders: OrderPort, notifications: NotificationPort):
        self.orders = orders
        self.notifications = notifications

    def process(self, order_id: str) -> dict:
        order = self.orders.get_order(order_id)
        self.orders.update_status(order_id, "processing")
        self.notifications.send(order["user_id"], f"Order {order_id} is processing")
        return order
```

### 3. Create Adapters for Each Profile

```python
# Test adapter (fake)
from dioxide import adapter, Profile

@adapter.for_(OrderPort, profile=Profile.TEST)
class FakeOrderAdapter:
    def __init__(self):
        self.orders = {"order-123": {"id": "order-123", "user_id": "user-1", "status": "new"}}

    def get_order(self, order_id: str) -> dict:
        return self.orders[order_id]

    def update_status(self, order_id: str, status: str) -> None:
        self.orders[order_id]["status"] = status
```

### 4. Set Up Celery with dioxide.celery Integration

```python
# app/main.py
from celery import Celery
from dioxide import Profile
from dioxide.celery import configure_dioxide, scoped_task

celery_app = Celery("tasks", broker="redis://localhost:6379/0")

# Get profile from environment
profile = Profile(os.getenv("PROFILE", "development"))
configure_dioxide(celery_app, profile=profile, packages=["app"])

@scoped_task(celery_app)
def process_order(scope, order_id: str) -> dict:
    service = scope.resolve(OrderService)
    return service.process(order_id)
```

## Key Concepts

### Task Scoping

Each task execution gets its own `ScopedContainer`, ensuring:

- **REQUEST-scoped** components are fresh per task
- **SINGLETON-scoped** components are shared across tasks in the same worker
- **Lifecycle** components are properly initialized/disposed

```python
@scoped_task(celery_app)
def my_task(scope, data: str) -> str:
    # scope is a ScopedContainer - fresh for each task execution
    ctx = scope.resolve(TaskContext)  # REQUEST-scoped: unique per task
    svc = scope.resolve(SharedService)  # SINGLETON: shared in worker
    return ctx.process(data)
```

### Async Tasks

The integration works with both sync and async tasks:

```python
@scoped_task(celery_app)
async def async_task(scope) -> str:
    # Async task with scoped dependencies
    client = scope.resolve(AsyncHttpClient)
    return await client.fetch("https://api.example.com")
```

### Error Handling

Scope cleanup happens even on task failure:

```python
@scoped_task(celery_app)
def risky_task(scope) -> None:
    resource = scope.resolve(ExpensiveResource)
    try:
        resource.process()
    except Exception:
        # Resource still gets cleaned up by scope context manager
        raise
```

## Testing with Eager Mode

Tests use Celery's eager mode for synchronous execution:

```python
# conftest.py
@pytest.fixture
def celery_app():
    app = Celery("test")
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    return app

# test_tasks.py
def test_process_order(celery_app, order_adapter, notification_adapter):
    result = process_order.delay("order-123")

    # Task executes synchronously in eager mode
    assert result.get()["id"] == "order-123"
    assert notification_adapter.sent[-1]["message"].startswith("Order order-123")
```

## Key Differences from Flask/FastAPI Integration

| Feature | Flask/FastAPI | Celery |
|---------|---------------|--------|
| Scope creation | Per HTTP request | Per task execution |
| Injection | `inject(Type)` or `Inject(Type)` | `scope.resolve(Type)` |
| Scope access | Via request context (`g`/middleware) | Via first argument |
| Concurrency | Request threads | Worker processes/threads |

## API Reference

### `configure_dioxide(app, profile, container, packages)`

Set up dioxide with a Celery application.

- `app`: Celery application instance
- `profile`: Profile enum or string (e.g., `Profile.PRODUCTION`)
- `container`: Optional custom Container (defaults to global)
- `packages`: Optional list of packages to scan

### `scoped_task(app, **task_options)`

Decorator to create a scoped Celery task.

- `app`: Celery application instance
- `**task_options`: Standard Celery task options (name, queue, etc.)

Returns a decorator that:
1. Injects `ScopedContainer` as first argument
2. Creates fresh scope per task execution
3. Disposes scope after task completes

## Learn More

- [dioxide Documentation](https://github.com/mikelane/dioxide)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
