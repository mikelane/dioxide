# Lifecycle Methods: Async/Sync Patterns

This guide explains how dioxide's lifecycle management works with async initialization
and sync resolution, and provides recommended patterns for different contexts.

---

## The Core Asymmetry

Dioxide has an intentional design asymmetry:

| Operation | Type | Why |
|-----------|------|-----|
| `container.resolve()` | **Synchronous** | Fast, predictable, works everywhere |
| `initialize()` / `dispose()` | **Async** | Resources need async I/O (database, HTTP, etc.) |

This design reflects real-world constraints:

- **Resolution** happens frequently (every dependency injection)
- **Lifecycle methods** run once at startup/shutdown
- Infrastructure resources (databases, caches, HTTP clients) require async operations

---

## When Are Lifecycle Methods Called?

Understanding the execution timeline is crucial:

```
1. container = Container()              # Container created (no lifecycle yet)
2. container.scan(profile=...)          # Components discovered (no lifecycle yet)
3. await container.start()              # ALL initialize() methods called NOW
   └── Or: async with container:        # (start() called on context entry)
4. adapter = container.resolve(Port)    # Returns already-initialized instance
5. await container.stop()               # ALL dispose() methods called NOW
   └── Or: context exit                 # (stop() called on context exit)
```

**Key insight**: `resolve()` returns instances that are **already initialized**.
The async initialization happens during `start()`, not during `resolve()`.

---

## Recommended Patterns

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
import signal

async def main():
    container = Container()
    container.scan(profile=Profile.PRODUCTION)

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

## Common Questions

### Q: Can I call resolve() before start()?

**Yes, but the component won't be initialized.** Resolution creates the instance,
but lifecycle initialization only happens during `start()`.

```python
container = Container()
container.scan(profile=Profile.PRODUCTION)

# This returns an instance, but initialize() hasn't been called!
adapter = container.resolve(DatabasePort)  # adapter.engine is None!

# Now initialize() is called on all lifecycle components
await container.start()

# Now the adapter is properly initialized
adapter = container.resolve(DatabasePort)  # adapter.engine is ready
# (Same instance - it's a singleton)
```

**Recommendation**: Always use `async with container:` or call `start()` before
resolving lifecycle components.

### Q: What happens if initialize() fails?

If any component's `initialize()` fails:

1. The exception is raised immediately
2. All **already-initialized** components have their `dispose()` called (rollback)
3. The container is left in a clean state

```python
async with Container(profile=Profile.PRODUCTION) as container:
    # If Database.initialize() fails:
    # - Any already-initialized components are disposed
    # - Exception propagates to your code
    pass
```

### Q: Why not have an async resolve()?

We considered `resolve_async()` but decided against it:

1. **Resolution should be fast**: Just returning a cached instance
2. **Initialization is rare**: Only at startup, not per-request
3. **Simpler mental model**: Resolve always returns immediately
4. **Sync compatibility**: Works in both sync and async code

The current design separates concerns:
- `resolve()` = get a component (fast, sync)
- `start()`/`stop()` = manage lifecycle (slow, async)

### Q: Can lifecycle methods be synchronous?

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

**Why?** Infrastructure resources (databases, HTTP clients, message queues) require
async I/O. Making lifecycle methods async-only prevents subtle bugs where developers
accidentally block the event loop.

If your initialization is truly synchronous, wrap it:

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

## Best Practices

1. **Always use async context manager** when possible:
   ```python
   async with Container(profile=...) as container:
       # Safe: all lifecycle methods complete before this runs
   ```

2. **Don't resolve lifecycle components before start()**:
   ```python
   # Bad
   adapter = container.resolve(DatabasePort)
   await container.start()  # Too late!

   # Good
   await container.start()
   adapter = container.resolve(DatabasePort)
   ```

3. **Keep initialize() fast**: Establish connections, don't do heavy work:
   ```python
   async def initialize(self) -> None:
       # Good: just create the pool
       self.pool = await asyncpg.create_pool(...)

       # Avoid: loading tons of data at startup
       # self.all_users = await self.pool.fetch("SELECT * FROM users")
   ```

4. **Make dispose() idempotent**: Safe to call multiple times:
   ```python
   async def dispose(self) -> None:
       if self.pool:  # Check before closing
           await self.pool.close()
           self.pool = None
   ```

5. **Test fakes usually don't need @lifecycle**:
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
- {doc}`decorator-order` - Decorator ordering (doesn't affect behavior)
- {doc}`scoping` - Request scoping for web applications
