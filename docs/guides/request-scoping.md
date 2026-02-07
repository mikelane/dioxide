# Request Scoping

This guide covers **request scoping** in dioxide: how to isolate dependencies per HTTP request, background task, or any bounded execution context. If you are new to scoping in general, read the {doc}`scoping` guide first.

## When to Use REQUEST Scope

Use `Scope.REQUEST` when a component needs:

- **Per-request isolation** -- each HTTP request gets its own instance
- **Shared within a request** -- multiple resolutions in the same request return the same instance
- **Automatic cleanup** -- resources are disposed when the request ends

Common use cases include database sessions, correlation IDs, user context, and request-scoped caches.

### Scope Comparison

| Scope | Created | Shared | Disposed | Use For |
|-------|---------|--------|----------|---------|
| `SINGLETON` | Once per container | Across all requests | When container stops | Config, connection pools, services |
| `FACTORY` | Every resolution | Never | Not managed | Throwaway objects, value types |
| `REQUEST` | Once per scope | Within the same scope | When scope exits | DB sessions, request context, correlation IDs |

### Decision Checklist

Mark a component as `Scope.REQUEST` if **all** of these are true:

1. The component holds state specific to one request (user ID, request ID, DB transaction)
2. Multiple parts of the request handler need the **same** instance
3. The component should be **fresh** for each new request

If only (1) is true but not (2), consider `Scope.FACTORY` instead.

## Quick Start

Three steps to add request scoping to your application:

### Step 1: Mark Components as REQUEST-Scoped

```python
import uuid
from dioxide import adapter, service, lifecycle, Profile, Scope
from typing import Protocol


class RequestContextPort(Protocol):
    request_id: str
    user_id: str | None


@adapter.for_(RequestContextPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.user_id = None
```

### Step 2: Add Framework Middleware

::::{tab-set}

:::{tab-item} FastAPI

```python
from fastapi import FastAPI
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION, packages=["myapp"])


@app.get("/users/me")
async def get_me(ctx: RequestContextPort = Inject(RequestContextPort)):
    return {"request_id": ctx.request_id}
```

:::

:::{tab-item} Flask

```python
from flask import Flask
from dioxide import Profile
from dioxide.flask import configure_dioxide, inject

app = Flask(__name__)
configure_dioxide(app, profile=Profile.PRODUCTION, packages=["myapp"])


@app.route("/users/me")
def get_me():
    ctx = inject(RequestContextPort)
    return {"request_id": ctx.request_id}
```

:::

::::

### Step 3: Inject Normally

REQUEST-scoped components are injected exactly like any other dependency. The middleware handles scope creation and cleanup automatically.

```python
@service
class AuditService:
    def __init__(self, ctx: RequestContextPort):
        self.ctx = ctx

    def log_action(self, action: str) -> None:
        print(f"[{self.ctx.request_id}] {action}")
```

```{important}
`AuditService` above is a `@service` with default `SINGLETON` scope. It depends on a `REQUEST`-scoped `RequestContextPort`. This will raise `CaptiveDependencyError` at scan time.

To fix this, either make `AuditService` REQUEST-scoped too, or resolve the context within methods rather than the constructor. See {ref}`captive-dependencies` below.
```

## Common Patterns

### Correlation IDs

Correlation IDs trace a request across services and log entries:

```python
import uuid
from typing import Protocol
from dioxide import adapter, service, Profile, Scope


class CorrelationPort(Protocol):
    correlation_id: str


@adapter.for_(CorrelationPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class CorrelationIdAdapter:
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())


@adapter.for_(CorrelationPort, profile=Profile.TEST, scope=Scope.REQUEST)
class FakeCorrelationAdapter:
    def __init__(self):
        self.correlation_id = "test-correlation-id"
```

In FastAPI, propagate the correlation ID to response headers:

```python
from fastapi import FastAPI, Response
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION, packages=["myapp"])


@app.get("/orders")
async def list_orders(
    response: Response,
    correlation: CorrelationPort = Inject(CorrelationPort),
):
    response.headers["X-Correlation-ID"] = correlation.correlation_id
    return {"orders": []}
```

### Database Sessions

Acquire a database connection per request and release it when the request ends:

```python
from typing import Protocol
from dioxide import adapter, lifecycle, Profile, Scope


class DatabaseSessionPort(Protocol):
    async def execute(self, query: str, *args) -> list: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...


@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    def __init__(self):
        self.conn = None

    async def initialize(self) -> None:
        import asyncpg

        self.conn = await asyncpg.connect("postgresql://localhost/mydb")

    async def dispose(self) -> None:
        if self.conn:
            await self.conn.close()

    async def execute(self, query: str, *args) -> list:
        return await self.conn.fetch(query, *args)

    async def commit(self) -> None:
        pass  # asyncpg auto-commits; use transactions for explicit control

    async def rollback(self) -> None:
        pass


@adapter.for_(DatabaseSessionPort, profile=Profile.TEST, scope=Scope.REQUEST)
class FakeDatabaseSession:
    def __init__(self):
        self.queries: list[str] = []
        self.committed = False

    async def execute(self, query: str, *args) -> list:
        self.queries.append(query)
        return []

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False
```

The `@lifecycle` decorator ensures `dispose()` is called when the scope exits, releasing the connection back to the pool.

### User Context

Populate user information from the incoming request:

```python
from typing import Protocol
from dioxide import adapter, Profile, Scope


class UserContextPort(Protocol):
    user_id: str | None
    roles: list[str]

    def set_from_token(self, token: str) -> None: ...


@adapter.for_(UserContextPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class UserContext:
    def __init__(self):
        self.user_id: str | None = None
        self.roles: list[str] = []

    def set_from_token(self, token: str) -> None:
        # In production, decode JWT and extract claims
        import jwt

        claims = jwt.decode(token, "secret", algorithms=["HS256"])
        self.user_id = claims["sub"]
        self.roles = claims.get("roles", [])


@adapter.for_(UserContextPort, profile=Profile.TEST, scope=Scope.REQUEST)
class FakeUserContext:
    def __init__(self):
        self.user_id: str | None = "test-user-123"
        self.roles: list[str] = ["admin"]

    def set_from_token(self, token: str) -> None:
        pass  # No-op in tests; pre-populated with test data
```

### Request-Scoped Cache

Cache expensive computations within a single request:

```python
from typing import Protocol
from dioxide import adapter, Profile, Scope


class RequestCachePort(Protocol):
    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object) -> None: ...


@adapter.for_(RequestCachePort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class InMemoryRequestCache:
    def __init__(self):
        self._cache: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._cache.get(key)

    def set(self, key: str, value: object) -> None:
        self._cache[key] = value
```

The cache is automatically discarded when the scope exits, preventing memory leaks across requests.

(captive-dependencies)=
## Captive Dependencies

A **captive dependency** occurs when a `SINGLETON` component depends on a `REQUEST`-scoped component. This is always a bug: the singleton captures the first request's instance and reuses it forever, defeating the purpose of request scoping.

Dioxide detects captive dependencies at scan time and raises `CaptiveDependencyError`:

```python
from dioxide import service, Scope

@service(scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.request_id = "..."


@service  # SINGLETON (default)
class GlobalService:
    def __init__(self, ctx: RequestContext):  # SINGLETON -> REQUEST
        self.ctx = ctx


# CaptiveDependencyError raised during container.scan()!
```

### Valid Scope Dependencies

| Parent Scope | Child Scope | Valid? | Reason |
|-------------|-------------|--------|--------|
| SINGLETON | SINGLETON | Yes | Same lifetime |
| SINGLETON | FACTORY | Yes | Creates new instance each time |
| SINGLETON | **REQUEST** | **No** | Captive dependency |
| REQUEST | SINGLETON | Yes | Shorter-lived uses longer-lived |
| REQUEST | REQUEST | Yes | Same scope |
| REQUEST | FACTORY | Yes | Creates new instance each time |
| FACTORY | Any | Yes | Always creates new parent |

### How to Fix

**Option 1: Make the parent REQUEST-scoped**

If the service genuinely needs per-request state, make it REQUEST-scoped too:

```python
@service(scope=Scope.REQUEST)
class RequestService:
    def __init__(self, ctx: RequestContext):
        self.ctx = ctx  # Both REQUEST-scoped, OK
```

**Option 2: Resolve within methods**

Keep the service as a singleton but resolve the scoped dependency when needed:

```python
@service  # SINGLETON
class GlobalService:
    def __init__(self, container: Container):
        self._container = container

    async def handle(self) -> None:
        async with self._container.create_scope() as scope:
            ctx = scope.resolve(RequestContext)
            # Use ctx within this method only
```

See {doc}`/troubleshooting/captive-dependency` for the complete troubleshooting guide.

(framework-integration-details)=
## Framework Integration Details

### FastAPI: DioxideMiddleware + Inject

The `DioxideMiddleware` handles three responsibilities:

1. **Lifespan management** -- scans components and starts/stops the container with the FastAPI application
2. **Request scoping** -- creates a `ScopedContainer` for each HTTP request
3. **Scope storage** -- stores the scoped container in ASGI state for `Inject()` to find

```python
from fastapi import FastAPI
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()
app.add_middleware(
    DioxideMiddleware,
    profile=Profile.PRODUCTION,
    packages=["myapp.adapters", "myapp.services"],
)


@app.get("/items")
async def list_items(
    db: DatabaseSessionPort = Inject(DatabaseSessionPort),
    ctx: RequestContextPort = Inject(RequestContextPort),
):
    # db and ctx are REQUEST-scoped: fresh per request, shared within request
    items = await db.execute("SELECT * FROM items")
    return {"request_id": ctx.request_id, "items": items}
```

`Inject(Type)` is a thin wrapper around FastAPI's `Depends()` that resolves from the current request's `ScopedContainer`.

**Custom container:**

```python
from dioxide import Container, Profile
from dioxide.fastapi import DioxideMiddleware

my_container = Container()
app.add_middleware(
    DioxideMiddleware,
    container=my_container,
    profile=Profile.PRODUCTION,
)
```

### Flask: configure_dioxide + inject

Flask's integration uses `before_request` and `teardown_request` hooks to manage scope lifecycle:

```python
from flask import Flask
from dioxide import Profile
from dioxide.flask import configure_dioxide, inject

app = Flask(__name__)
configure_dioxide(app, profile=Profile.PRODUCTION, packages=["myapp"])


@app.route("/items")
def list_items():
    db = inject(DatabaseSessionPort)
    ctx = inject(RequestContextPort)
    # db and ctx are REQUEST-scoped
    return {"request_id": ctx.request_id}
```

The scoped container is stored in Flask's `g` object, which is thread-local, ensuring each request gets its own scope even in threaded mode.

**How it works internally:**

1. `configure_dioxide()` scans components and starts the container
2. `before_request` hook calls `container.create_scope()` and stores the scope in `g`
3. Route handlers call `inject(Type)` which resolves from `g.dioxide_scope`
4. `teardown_request` hook disposes the scope (calling `dispose()` on `@lifecycle` components)

### Manual Scope Management

For frameworks without built-in integration, or for background tasks and CLI commands, create scopes manually:

```python
from dioxide import Container, Profile

container = Container(profile=Profile.PRODUCTION)


async def handle_request():
    async with container.create_scope() as scope:
        ctx = scope.resolve(RequestContextPort)
        db = scope.resolve(DatabaseSessionPort)
        # Use ctx and db...
    # scope exits: dispose() called on @lifecycle components
```

## Lifecycle Management in Scopes

REQUEST-scoped components decorated with `@lifecycle` have their `initialize()` called when first resolved within a scope, and `dispose()` called when the scope exits.

```python
from dioxide import adapter, lifecycle, Profile, Scope


@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    async def initialize(self) -> None:
        self.conn = await pool.acquire()

    async def dispose(self) -> None:
        await self.conn.release()
```

**Lifecycle guarantees:**

- `initialize()` is called once per scope, when the component is first resolved
- `dispose()` is called when the scope exits, even if an exception occurred
- Disposal happens in reverse creation order (last created, first disposed)
- If `dispose()` raises an exception, remaining disposals still proceed

## Testing REQUEST-Scoped Components

### Fixture with Scope

```python
import pytest
from dioxide import Container, Profile


@pytest.fixture
async def scope():
    container = Container(profile=Profile.TEST)
    async with container.create_scope() as test_scope:
        yield test_scope


async def test_request_context_has_unique_id(scope):
    ctx1 = scope.resolve(RequestContextPort)
    ctx2 = scope.resolve(RequestContextPort)

    # Same scope returns same instance
    assert ctx1 is ctx2
    assert ctx1.request_id == ctx2.request_id


async def test_different_scopes_have_different_ids():
    container = Container(profile=Profile.TEST)

    async with container.create_scope() as scope1:
        ctx1 = scope1.resolve(RequestContextPort)

    async with container.create_scope() as scope2:
        ctx2 = scope2.resolve(RequestContextPort)

    # Different scopes return different instances
    assert ctx1.request_id != ctx2.request_id
```

### Testing with FastAPI TestClient

```python
import pytest
from fastapi.testclient import TestClient
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware

from myapp.main import app


@pytest.fixture
def client():
    # Override middleware with test profile
    app.add_middleware(DioxideMiddleware, profile=Profile.TEST, packages=["myapp"])
    return TestClient(app)


def test_each_request_gets_unique_id(client):
    response1 = client.get("/users/me")
    response2 = client.get("/users/me")

    assert response1.json()["request_id"] != response2.json()["request_id"]
```

### Testing with Flask Test Client

```python
import pytest
from dioxide import Profile
from dioxide.flask import configure_dioxide

from myapp.main import create_app


@pytest.fixture
def client():
    app = create_app(profile=Profile.TEST)
    return app.test_client()


def test_each_request_gets_unique_id(client):
    response1 = client.get("/users/me")
    response2 = client.get("/users/me")

    assert response1.get_json()["request_id"] != response2.get_json()["request_id"]
```

## Migration Guide: SINGLETON to REQUEST

If you have components that should be request-scoped but are currently singletons, follow these steps:

### Step 1: Identify Candidates

Components that hold request-specific state are candidates for `Scope.REQUEST`:

```python
# BEFORE: Singleton with mutable request state (bug!)
@adapter.for_(RequestContextPort, profile=Profile.PRODUCTION)
class RequestContext:
    def __init__(self):
        self.user_id = None  # Shared across ALL requests!
        self.request_id = None
```

### Step 2: Add scope=Scope.REQUEST

```python
# AFTER: Request-scoped, fresh per request
@adapter.for_(RequestContextPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.user_id = None  # Fresh per request
        self.request_id = str(uuid.uuid4())
```

### Step 3: Add Middleware

If you haven't already, add the framework middleware to create scopes per request:

```python
# FastAPI
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)

# Flask
configure_dioxide(app, profile=Profile.PRODUCTION)
```

### Step 4: Fix Captive Dependencies

After changing a component to `Scope.REQUEST`, any `SINGLETON` that depends on it will raise `CaptiveDependencyError`. Review the dependency graph and either:

- Change dependent singletons to `Scope.REQUEST`
- Restructure to resolve within methods instead of constructors

### Step 5: Update Tests

Ensure tests create scopes for REQUEST-scoped components:

```python
# BEFORE: Direct resolution (works for SINGLETON)
container = Container(profile=Profile.TEST)
ctx = container.resolve(RequestContextPort)

# AFTER: Resolution within scope (required for REQUEST)
async with container.create_scope() as scope:
    ctx = scope.resolve(RequestContextPort)
```

## Troubleshooting

### ScopeError: REQUEST-scoped component resolved outside scope

```
ScopeError: Cannot resolve RequestContext: REQUEST-scoped, requires active scope
```

**Cause:** You are resolving a REQUEST-scoped component directly from the container without creating a scope first.

**Fix:** Wrap the resolution in `container.create_scope()`:

```python
# Wrong
ctx = container.resolve(RequestContext)

# Right
async with container.create_scope() as scope:
    ctx = scope.resolve(RequestContext)
```

For web frameworks, ensure middleware is configured (see {ref}`framework-integration-details`).

### CaptiveDependencyError: SINGLETON depends on REQUEST

```
CaptiveDependencyError: GlobalService (SINGLETON) -> RequestContext (REQUEST)
```

**Cause:** A singleton component has a REQUEST-scoped dependency in its constructor.

**Fix:** See {ref}`captive-dependencies` above.

### REQUEST-scoped component not fresh per request

**Cause:** The framework middleware is not configured, so no scope is created per request. Without a scope, REQUEST-scoped components fall back to FACTORY behavior (new instance every resolution, no sharing within request).

**Fix:** Add the framework middleware:

```python
# FastAPI
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)

# Flask
configure_dioxide(app, profile=Profile.PRODUCTION)
```

### Lifecycle dispose() not called

**Cause:** The scope is not being exited properly. This can happen if you resolve outside the `async with` block or if an exception prevents scope cleanup.

**Fix:** Always use the async context manager pattern:

```python
async with container.create_scope() as scope:
    db = scope.resolve(DatabaseSessionPort)
    # dispose() guaranteed to be called when exiting this block
```

## API Reference

| Symbol | Module | Description |
|--------|--------|-------------|
| {class}`~dioxide.scope.Scope.REQUEST` | `dioxide.scope` | Scope enum value for request-scoped components |
| {class}`~dioxide.container.ScopedContainer` | `dioxide.container` | Container that caches REQUEST-scoped instances |
| {meth}`~dioxide.container.Container.create_scope` | `dioxide.container` | Create a new scope (returns async context manager) |
| {class}`~dioxide.exceptions.ScopeError` | `dioxide.exceptions` | Raised when resolving REQUEST-scoped outside a scope |
| {class}`~dioxide.exceptions.CaptiveDependencyError` | `dioxide.exceptions` | Raised when SINGLETON depends on REQUEST |
| {class}`~dioxide.fastapi.DioxideMiddleware` | `dioxide.fastapi` | ASGI middleware for FastAPI request scoping |
| {func}`~dioxide.fastapi.Inject` | `dioxide.fastapi` | FastAPI dependency wrapper for dioxide injection |
| {func}`~dioxide.flask.configure_dioxide` | `dioxide.flask` | Flask integration setup function |
| {func}`~dioxide.flask.inject` | `dioxide.flask` | Flask dependency resolution helper |
