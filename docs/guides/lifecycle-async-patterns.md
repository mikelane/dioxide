# Lifecycle Methods: Async/Sync Patterns

This guide explains how dioxide's lifecycle management works with async initialization
and sync resolution. It covers the design rationale, common resource management patterns,
error handling, framework integration, and troubleshooting.

---

## The Golden Rule

> **`resolve()` is synchronous. `initialize()` and `dispose()` are async.**

This is intentional. Dioxide separates two concerns:

| Operation | Type | Frequency | Purpose |
|-----------|------|-----------|---------|
| `container.resolve()` | **Sync** | Many times (every injection) | Return a cached instance |
| `initialize()` / `dispose()` | **Async** | Once (startup / shutdown) | Acquire / release resources |

Resolution returns an already-initialized singleton. The heavy lifting (connecting to
databases, opening HTTP sessions, warming caches) happens during `start()`, before your
application serves its first request.

---

## When Are Lifecycle Methods Called?

Understanding the execution timeline is crucial:

```
1. container = Container(profile=...)    # Container created (no lifecycle yet)
2. await container.start()               # ALL initialize() methods called NOW
   -- Or: async with container:          # (start() called on context entry)
3. adapter = container.resolve(Port)     # Returns already-initialized instance
4. await container.stop()                # ALL dispose() methods called NOW
   -- Or: context exit                   # (stop() called on context exit)
```

**Key insight**: `resolve()` returns instances that are **already initialized**.
The async initialization happens during `start()`, not during `resolve()`.

---

## Container Lifecycle Patterns

### Pattern 1: Async Context Manager (Recommended)

The cleanest approach uses the async context manager:

```python
from dioxide import Container, Profile

async def main():
    async with Container(profile=Profile.PRODUCTION) as container:
        # All @lifecycle components have been initialized
        # Their initialize() methods have already completed

        service = container.resolve(UserService)
        # service.db (a lifecycle adapter) is ready to use

        await service.do_work()
    # All @lifecycle components disposed (dispose() called)

asyncio.run(main())
```

**Why this works**: The `async with` block calls `await container.start()` on entry
and `await container.stop()` on exit, ensuring all async lifecycle methods complete
before your code runs.

### Pattern 2: Manual Start/Stop

For more control (e.g., signal handling, graceful shutdown):

```python
from dioxide import Container, Profile

async def main():
    container = Container(profile=Profile.PRODUCTION)

    # Start lifecycle - blocks until all initialize() complete
    await container.start()

    try:
        # Your application runs here
        # All @lifecycle components are ready
        app = container.resolve(Application)
        await app.run_forever()
    finally:
        # Stop lifecycle - blocks until all dispose() complete
        await container.stop()
```

### Pattern 3: Framework Integration (FastAPI)

FastAPI's lifespan integrates naturally with dioxide's async lifecycle:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dioxide import Container, Profile
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Container lifecycle tied to FastAPI lifespan."""
    async with Container(profile=Profile.PRODUCTION) as container:
        # All @lifecycle adapters initialized before first request
        app.state.container = container
        yield
    # All @lifecycle adapters disposed after last response


app = FastAPI(lifespan=lifespan)


@app.get("/users")
async def list_users():
    # Container is ready, all adapters initialized
    service = app.state.container.resolve(UserService)
    return await service.list_all()
```

**Alternative**: Use `DioxideMiddleware` for automatic integration:

```python
from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject

app = FastAPI()
app.add_middleware(DioxideMiddleware, profile=Profile.PRODUCTION)


@app.get("/users")
async def list_users(service: UserService = Inject(UserService)):
    # Middleware handles container lifecycle automatically
    return await service.list_all()
```

### Pattern 4: Flask (Sync Framework)

Flask is synchronous, so you need an async event loop for lifecycle methods:

```python
import asyncio
import atexit
from dioxide import Container, Profile
from flask import Flask

container = Container()
_container_started = False


def create_app() -> Flask:
    app = Flask(__name__)

    @app.before_request
    def ensure_container_started():
        global _container_started
        if not _container_started:
            container.scan(profile=Profile.PRODUCTION)
            # Run async start() in a new event loop
            asyncio.run(container.start())
            _container_started = True

    # Register shutdown handler for graceful cleanup
    def shutdown():
        if _container_started:
            asyncio.run(container.stop())

    atexit.register(shutdown)

    @app.route("/users")
    def list_users():
        # Resolve is synchronous - works in sync Flask
        service = container.resolve(UserService)
        # But async service methods need special handling
        return asyncio.run(service.list_all())

    return app
```

**Note**: For Flask apps with async operations, consider using `flask[async]` or Quart.

---

## Common Resource Patterns

The following patterns show how to use `@lifecycle` with real-world infrastructure
components. Each pattern follows the same structure:

1. Define a port (Protocol) for the resource
2. Implement a production adapter with `@lifecycle` for real connections
3. Implement a test adapter **without** `@lifecycle` for fast fakes

### Database Connection Pool (SQLAlchemy)

```python
from typing import Protocol
from dioxide import adapter, lifecycle, Profile


class DatabasePort(Protocol):
    async def execute(self, query: str) -> list[dict]: ...


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class SQLAlchemyAdapter:
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = None

    async def initialize(self) -> None:
        from sqlalchemy.ext.asyncio import create_async_engine

        self.engine = create_async_engine(
            self.config.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        # Verify the connection works at startup
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None

    async def execute(self, query: str) -> list[dict]:
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query))
            return [dict(row._mapping) for row in result]


# Test fake - no lifecycle needed
@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabase:
    def __init__(self):
        self.records: list[dict] = []

    async def execute(self, query: str) -> list[dict]:
        return self.records

    def seed(self, *records: dict) -> None:
        self.records.extend(records)
```

**Key points**:
- `pool_pre_ping=True` detects stale connections automatically
- The `initialize()` method verifies connectivity at startup
- `dispose()` checks `self.engine` before closing (idempotent)
- The test fake has no `@lifecycle` and no async overhead

### HTTP Client Session (aiohttp)

```python
from typing import Protocol
from dioxide import adapter, lifecycle, Profile


class HttpClientPort(Protocol):
    async def get(self, url: str) -> dict: ...
    async def post(self, url: str, data: dict) -> dict: ...


@adapter.for_(HttpClientPort, profile=Profile.PRODUCTION)
@lifecycle
class AiohttpAdapter:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session = None

    async def initialize(self) -> None:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.config.api_token}"},
        )

    async def dispose(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def get(self, url: str) -> dict:
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def post(self, url: str, data: dict) -> dict:
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()


# Test fake - no lifecycle needed
@adapter.for_(HttpClientPort, profile=Profile.TEST)
class FakeHttpClient:
    def __init__(self):
        self.responses: dict[str, dict] = {}

    async def get(self, url: str) -> dict:
        return self.responses.get(url, {})

    async def post(self, url: str, data: dict) -> dict:
        return self.responses.get(url, {})

    def stub(self, url: str, response: dict) -> None:
        self.responses[url] = response
```

**Key points**:
- The `aiohttp.ClientSession` is created once and shared across requests
- Setting `timeout` and `headers` in `initialize()` applies to all requests
- The test fake uses a dictionary to stub responses per URL

### Redis Connection Pool

```python
from typing import Protocol
from dioxide import adapter, lifecycle, Profile


class CachePort(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...
    async def delete(self, key: str) -> None: ...


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    def __init__(self, config: AppConfig):
        self.config = config
        self.redis = None

    async def initialize(self) -> None:
        from redis.asyncio import Redis

        self.redis = Redis.from_url(
            self.config.redis_url,
            decode_responses=True,
        )
        # Verify connection
        await self.redis.ping()

    async def dispose(self) -> None:
        if self.redis:
            await self.redis.aclose()
            self.redis = None

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self.redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)


# Test fake - no lifecycle needed
@adapter.for_(CachePort, profile=Profile.TEST)
class FakeCache:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)
```

### Message Queue Consumer

```python
from typing import Protocol
from dioxide import adapter, lifecycle, Profile


class MessageQueuePort(Protocol):
    async def publish(self, topic: str, message: bytes) -> None: ...


@adapter.for_(MessageQueuePort, profile=Profile.PRODUCTION)
@lifecycle
class RabbitMQAdapter:
    def __init__(self, config: AppConfig):
        self.config = config
        self.connection = None
        self.channel = None

    async def initialize(self) -> None:
        import aio_pika

        self.connection = await aio_pika.connect_robust(
            self.config.rabbitmq_url,
        )
        self.channel = await self.connection.channel()

    async def dispose(self) -> None:
        if self.channel:
            await self.channel.close()
            self.channel = None
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def publish(self, topic: str, message: bytes) -> None:
        exchange = await self.channel.declare_exchange(topic)
        await exchange.publish(
            aio_pika.Message(body=message),
            routing_key=topic,
        )
```

---

## Error Handling Patterns

### Initialization Failure and Rollback

When any component's `initialize()` raises an exception, dioxide automatically rolls
back by disposing all **already-initialized** components:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def initialize(self) -> None:
        self.engine = create_async_engine(self.config.database_url)
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))  # May raise!

    async def dispose(self) -> None:
        if self.engine:
            await self.engine.dispose()


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    async def initialize(self) -> None:
        self.redis = Redis.from_url(self.config.redis_url)
        await self.redis.ping()  # May raise!

    async def dispose(self) -> None:
        if self.redis:
            await self.redis.aclose()
```

If the initialization order is `PostgresAdapter -> RedisAdapter` and Redis fails:

1. `PostgresAdapter.initialize()` succeeds
2. `RedisAdapter.initialize()` raises `ConnectionError`
3. Dioxide calls `PostgresAdapter.dispose()` (rollback)
4. The original `ConnectionError` propagates to your code

```python
try:
    async with Container(profile=Profile.PRODUCTION) as container:
        pass  # Never reached if initialize() fails
except ConnectionError as e:
    # Redis was unreachable
    # PostgresAdapter has already been disposed (no leaked connection)
    print(f"Startup failed: {e}")
```

### Dispose Failure Continuation

If a component's `dispose()` raises an exception, dioxide **continues disposing the
remaining components** and logs the error. It does not re-raise the exception:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def dispose(self) -> None:
        await self.engine.dispose()  # Succeeds


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    async def dispose(self) -> None:
        raise RuntimeError("Redis close failed!")  # Logged, not raised


@adapter.for_(HttpClientPort, profile=Profile.PRODUCTION)
@lifecycle
class HttpAdapter:
    async def dispose(self) -> None:
        await self.session.close()  # Still called despite Redis failure
```

This ensures that one failed cleanup does not prevent other resources from being
released. The error is logged via Python's `logging` module at the `ERROR` level.

**Best practice**: Make `dispose()` idempotent and defensive:

```python
async def dispose(self) -> None:
    if self.engine:
        try:
            await self.engine.dispose()
        except Exception:
            pass  # Best-effort cleanup
        finally:
            self.engine = None
```

---

## Lifecycle and Request Scoping

Lifecycle management and request scoping serve different purposes:

| Concept | Scope | Example |
|---------|-------|---------|
| `@lifecycle` | Application lifetime | Database connection pool |
| `Scope.REQUEST` | Single request | Per-request database session |

They work together naturally. A lifecycle component manages the connection *pool*
(created at startup, closed at shutdown), while a request-scoped component manages
an individual *session* (created per request, closed after response):

```python
from dioxide import adapter, lifecycle, service, Profile, Scope


class SessionPort(Protocol):
    async def execute(self, query: str) -> list[dict]: ...


# Connection pool - lives for the entire application
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresPool:
    async def initialize(self) -> None:
        self.pool = await asyncpg.create_pool(...)

    async def dispose(self) -> None:
        if self.pool:
            await self.pool.close()


# Session - created fresh per request
@adapter.for_(SessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class PostgresSession:
    def __init__(self, pool: DatabasePort):
        self.pool = pool
        self.conn = None

    async def execute(self, query: str) -> list[dict]:
        if not self.conn:
            self.conn = await self.pool.pool.acquire()
        return await self.conn.fetch(query)
```

For more on request scoping, see {doc}`scoping`.

---

## Framework Integration Summary

| Framework | Lifecycle Pattern | Notes |
|-----------|-------------------|-------|
| **FastAPI** | `lifespan` or `DioxideMiddleware` | Native async support |
| **Starlette** | ASGI lifespan events | Same as FastAPI |
| **Flask** | `asyncio.run()` in hooks | Sync framework, needs event loop |
| **Django** | `AppConfig.ready()` | Use `sync_to_async` or event loop |
| **Celery** | Worker signals | See `dioxide.celery` integration |
| **Click CLI** | `asyncio.run()` wrapper | See `dioxide.click` integration |

---

## Frequently Asked Questions

### Why is `initialize()` async but `resolve()` sync?

Resolution is just a dictionary lookup that returns a cached singleton. It happens
many times during your application's lifetime and must be fast and predictable.

Initialization, on the other hand, happens **once** at startup. It connects to
databases, opens HTTP sessions, and warms caches -- operations that inherently
require async I/O.

By separating these concerns:
- `resolve()` = get a component (fast, sync, works everywhere)
- `start()` / `stop()` = manage resources (slow, async, runs once)

This design also means `resolve()` works identically in both sync and async code.

### Why don't test fakes need `@lifecycle`?

Test fakes are in-memory implementations with no external resources. They do not
need to connect to databases, open network connections, or warm caches:

```python
# Production: real database connection -- needs lifecycle
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def initialize(self) -> None:
        self.pool = await asyncpg.create_pool(...)

    async def dispose(self) -> None:
        await self.pool.close()


# Test: in-memory dict -- no lifecycle needed
@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabase:
    def __init__(self):
        self.data: dict[str, dict] = {}

    async def execute(self, query: str) -> list[dict]:
        return list(self.data.values())

    def seed(self, **records: dict) -> None:
        self.data.update(records)
```

Skipping `@lifecycle` on test fakes means:
- **Faster tests**: No async startup/shutdown overhead
- **Simpler setup**: No need for `async with container:` in every test
- **No external dependencies**: Tests run without infrastructure

If your test fake *does* need initialization (e.g., loading fixture files), you can
add `@lifecycle` to it. But this is rare.

### Can lifecycle methods be synchronous?

**No.** The `@lifecycle` decorator validates that both `initialize()` and `dispose()`
are async coroutines:

```python
@service
@lifecycle
class BadService:
    def initialize(self) -> None:  # Not async!
        pass

# Raises TypeError: BadService.initialize() must be async
```

Infrastructure resources (databases, HTTP clients, message queues) require async I/O.
Making lifecycle methods async-only prevents subtle bugs where developers accidentally
block the event loop.

If your initialization is truly synchronous, use an async method anyway:

```python
@service
@lifecycle
class QuickInitService:
    async def initialize(self) -> None:
        # Synchronous work is fine inside async methods
        self.cache = {}
        self.ready = True

    async def dispose(self) -> None:
        self.cache.clear()
```

### Can I call `resolve()` before `start()`?

**Yes, but the component will not be initialized.** Resolution creates the instance,
but lifecycle initialization only happens during `start()`:

```python
container = Container(profile=Profile.PRODUCTION)

# This returns an instance, but initialize() has not been called!
adapter = container.resolve(DatabasePort)  # adapter.engine is None!

# Now initialize() is called on all lifecycle components
await container.start()

# Now the adapter is properly initialized
adapter = container.resolve(DatabasePort)  # adapter.engine is ready
# (Same instance -- it is a singleton)
```

**Recommendation**: Always use `async with container:` or call `start()` before
resolving lifecycle components.

### What happens if `initialize()` fails?

If any component's `initialize()` fails:

1. The exception is raised immediately
2. All **already-initialized** components have their `dispose()` called (rollback)
3. The container is left in a clean state

See [Initialization Failure and Rollback](#initialization-failure-and-rollback)
for details.

---

## Troubleshooting

### "Lifecycle component not initialized"

**Symptom**: Attributes set in `initialize()` are `None` or unset when you use
the component.

**Cause**: You resolved the component before calling `start()` or entering the
`async with container:` block.

**Fix**: Ensure lifecycle is started before resolving:

```python
# Wrong -- resolve before start
container = Container(profile=Profile.PRODUCTION)
db = container.resolve(DatabasePort)
# db.engine is None!

# Correct -- start first
container = Container(profile=Profile.PRODUCTION)
await container.start()
db = container.resolve(DatabasePort)
# db.engine is initialized

# Best -- use context manager
async with Container(profile=Profile.PRODUCTION) as container:
    db = container.resolve(DatabasePort)
    # db.engine is initialized
```

### `TypeError: ... must implement initialize() method`

**Symptom**: Import-time `TypeError` when decorating a class with `@lifecycle`.

**Cause**: The class is missing the `initialize()` method, or the method is not
async.

**Fix**: Add both async methods:

```python
@service
@lifecycle
class MyComponent:
    async def initialize(self) -> None:
        pass  # Required, even if empty

    async def dispose(self) -> None:
        pass  # Required, even if empty
```

### Resources not cleaned up on shutdown

**Symptom**: Database connections, file handles, or other resources leak after
the application stops.

**Possible causes**:

1. **`stop()` was never called**: Use `async with container:` to guarantee cleanup.
2. **`dispose()` has a bug**: Check that `dispose()` actually releases the resource.
3. **`dispose()` raised an exception**: Check logs for `ERROR` messages about disposal failures.
4. **Application crashed before shutdown**: Add signal handlers or use the context manager.

**Fix**: Use the async context manager pattern, which guarantees `stop()` is
called even if exceptions occur:

```python
async with Container(profile=Profile.PRODUCTION) as container:
    # Even if this code raises, dispose() is called
    await run_application(container)
```

### Multiple `start()`/`stop()` cycles

If you need to restart the container (e.g., in a test suite), each `start()` call
re-initializes all lifecycle components and each `stop()` disposes them:

```python
container = Container(profile=Profile.TEST)

# Cycle 1
await container.start()
# ... run tests ...
await container.stop()

# Cycle 2 -- components are re-initialized
await container.start()
# ... run more tests ...
await container.stop()
```

For test suites, consider using `fresh_container` from `dioxide.testing`:

```python
from dioxide.testing import fresh_container

async def test_user_registration():
    async with fresh_container(profile=Profile.TEST) as container:
        service = container.resolve(UserService)
        # Isolated container with lifecycle management
```

---

## Best Practices

1. **Always use the async context manager** when possible:
   ```python
   async with Container(profile=...) as container:
       # Safe: all lifecycle methods complete before this runs
   ```

2. **Do not resolve lifecycle components before `start()`**:
   ```python
   # Bad
   adapter = container.resolve(DatabasePort)
   await container.start()  # Too late!

   # Good
   await container.start()
   adapter = container.resolve(DatabasePort)
   ```

3. **Keep `initialize()` fast**: Establish connections, do not do heavy work:
   ```python
   async def initialize(self) -> None:
       # Good: just create the pool
       self.pool = await asyncpg.create_pool(...)

       # Avoid: loading large datasets at startup
       # self.all_users = await self.pool.fetch("SELECT * FROM users")
   ```

4. **Make `dispose()` idempotent**: Safe to call multiple times:
   ```python
   async def dispose(self) -> None:
       if self.pool:  # Check before closing
           await self.pool.close()
           self.pool = None
   ```

5. **Do not raise in `dispose()`**: Log errors but continue cleanup:
   ```python
   async def dispose(self) -> None:
       try:
           await self.connection.close()
       except Exception:
           pass  # Best-effort cleanup
       finally:
           self.connection = None
   ```

6. **Test fakes usually do not need `@lifecycle`**:
   ```python
   # Production: needs real connection lifecycle
   @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
   @lifecycle
   class PostgresAdapter: ...

   # Test: no real resources, no lifecycle needed
   @adapter.for_(DatabasePort, profile=Profile.TEST)
   class FakeDatabase:
       def __init__(self):
           self.data = {}  # Just a dict, instant "init"
   ```

---

## See Also

- {doc}`../examples/04-lifecycle-management` - Complete working example
- {doc}`../cookbook/fastapi` - FastAPI integration patterns
- {doc}`decorator-order` - Decorator ordering (does not affect behavior)
- {doc}`scoping` - Request scoping for web applications
