# Request Scope Ergonomics Design Analysis

**Issue:** #181 (async scope context manager API)
**Epic:** #178 (Request Scoping)
**Author:** Claude (Solution Architect)
**Date:** 2025-11-29
**Status:** Design Proposal

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Competitive Analysis](#competitive-analysis)
3. [Design Principles](#design-principles)
4. [Recommended API Design](#recommended-api-design)
5. [Declaration Ergonomics](#declaration-ergonomics)
6. [Usage Ergonomics](#usage-ergonomics)
7. [Error Messages](#error-messages)
8. [Testing Ergonomics](#testing-ergonomics)
9. [Framework Integration](#framework-integration)
10. [Advanced Patterns](#advanced-patterns)
11. [Trade-offs and Rejected Alternatives](#trade-offs-and-rejected-alternatives)
12. [Migration Path](#migration-path)
13. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

This document analyzes ergonomics for `Scope.REQUEST` in dioxide and recommends an API design that:

1. **Maintains consistency** with existing dioxide patterns (`@adapter.for_()`, `@service`, `@lifecycle`)
2. **Follows the "explicit over clever" principle** from MLP_VISION.md
3. **Provides world-class framework integration** (FastAPI, Flask)
4. **Enables friction-free testing** with pytest fixtures
5. **Fails fast** with clear, actionable error messages

**Key Design Decision:** Use a **scoped container pattern** where `container.create_scope()` returns a `ScopedContainer` that enforces scope rules and provides clear semantics.

---

## Competitive Analysis

### FastAPI's `Depends()` with `yield`

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    ...
```

**Pros:**
- Simple, generator-based, familiar Python pattern
- Framework handles lifecycle automatically
- Type hints provide IDE support

**Cons:**
- Not really DI - more like factory pattern
- No container concept - each dependency is independent
- Difficult to share instances across multiple dependencies in same request
- Manual wiring for complex dependency graphs

### .NET's `IServiceScope` / `CreateScope()`

```csharp
using (var scope = serviceProvider.CreateScope())
{
    var service = scope.ServiceProvider.GetService<IMyService>();
    // All scoped services share this scope
}
// Disposed when scope exits
```

**Pros:**
- Explicit scope boundary
- Clear lifecycle semantics
- Scoped container enforces rules
- Proven pattern at scale

**Cons:**
- Must resolve from scoped container, not parent
- Verbose without middleware

### Spring's `@RequestScope`

```java
@Component
@RequestScope
public class RequestContext {
    private UUID requestId = UUID.randomUUID();
}
```

**Pros:**
- Declarative - just add annotation
- Framework handles everything
- Familiar to enterprise developers

**Cons:**
- Magic/implicit - hard to understand lifecycle
- Thread-local based - doesn't work with async
- Testing requires special infrastructure
- Scope violations silent or confusing

### Python dependency-injector's `ThreadLocalSingleton`

```python
class Container(containers.DeclarativeContainer):
    session = providers.ThreadLocalSingleton(Session)
```

**Pros:**
- Works with threading
- Clear provider type

**Cons:**
- Thread-based, not request-based
- Doesn't work well with async/await
- No automatic cleanup
- Manual wiring required

### Analysis Summary

| Framework | Explicit | Type-Safe | Async | Auto-Cleanup | Testing |
|-----------|----------|-----------|-------|--------------|---------|
| FastAPI Depends | Partial | Yes | Yes | Yes | Good |
| .NET CreateScope | Yes | Yes | Yes | Yes | Good |
| Spring @RequestScope | No | Partial | No | Yes | Poor |
| dependency-injector | Partial | Yes | Poor | No | Fair |

**Conclusion:** .NET's `CreateScope()` pattern provides the best foundation, adapted for Python's async-first nature and dioxide's decorator-based API.

---

## Design Principles

Based on dioxide's MLP_VISION.md, this design follows:

1. **Type-Checker is the Source of Truth**
   - Full mypy support for scoped containers
   - IDE autocomplete for scope methods
   - Type errors catch scope violations

2. **Explicit Over Clever**
   - Users explicitly create scope contexts
   - Scope boundaries are visible in code
   - No hidden thread-local magic

3. **Fails Fast**
   - Resolving REQUEST component outside scope raises immediately
   - SINGLETON depending on REQUEST detected at scan time
   - Clear error messages with resolution hints

4. **Zero Ceremony for Common Cases**
   - Framework integration handles scope automatically
   - pytest fixtures eliminate boilerplate
   - One decorator parameter for scope

5. **Pythonic**
   - Async context managers for scope lifecycle
   - Decorators for declaration
   - Type hints for dependencies

---

## Recommended API Design

### Core API Overview

```python
from dioxide import Container, adapter, service, Scope, Profile, lifecycle

# 1. DECLARATION: Mark component as request-scoped
@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    async def initialize(self) -> None:
        self.conn = await asyncpg.connect(...)

    async def dispose(self) -> None:
        await self.conn.close()

# 2. USAGE: Create scope and resolve
container = Container(profile=Profile.PRODUCTION)

async with container.create_scope() as scope:
    # Resolve from scope - REQUEST instances cached here
    session = scope.resolve(DatabaseSessionPort)
    user_service = scope.resolve(UserService)

    # SINGLETON instances work too (from parent container)
    config = scope.resolve(AppConfig)

    # Use services...
    await user_service.create_user("alice@example.com")
# session.dispose() called automatically

# 3. ERROR: Resolving REQUEST outside scope
try:
    session = container.resolve(DatabaseSessionPort)  # No scope!
except ScopeError as e:
    print(e)  # Clear error with fix instructions
```

### Type Definitions

```python
from typing import TypeVar, Protocol
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

T = TypeVar('T')

class ScopedContainer(Protocol):
    """Container bound to a request scope."""

    def resolve(self, component_type: type[T]) -> T:
        """Resolve component within this scope."""
        ...

    def __getitem__(self, component_type: type[T]) -> T:
        """Bracket syntax for resolve."""
        ...

class Container:
    @asynccontextmanager
    async def create_scope(self) -> AsyncIterator[ScopedContainer]:
        """Create a request scope for REQUEST-scoped components."""
        ...
```

---

## Declaration Ergonomics

### Recommended: Extend `scope` Parameter

Use the existing `scope` parameter on decorators, adding `Scope.REQUEST`:

```python
from dioxide import adapter, service, Scope, Profile

# Adapter with REQUEST scope
@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    async def initialize(self) -> None:
        self.conn = await asyncpg.connect(...)

    async def dispose(self) -> None:
        await self.conn.close()

# Service with REQUEST scope (less common, but supported)
@service(scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()
```

### Why This Approach

**Consistency:** Follows existing pattern where `scope` is a parameter:
```python
@adapter.for_(Port, profile=..., scope=Scope.SINGLETON)  # Existing
@adapter.for_(Port, profile=..., scope=Scope.REQUEST)    # New
```

**Minimal API Surface:** No new decorators to learn.

**Type Safety:** `Scope` enum provides IDE autocomplete and type checking.

### Service Decorator Extension

The `@service` decorator currently doesn't accept parameters. We need to extend it:

```python
# Current (no parameters)
@service
class UserService:
    pass

# Extended (optional scope parameter)
@service(scope=Scope.REQUEST)
class RequestContext:
    pass

# Backward compatible - default is SINGLETON
@service  # Same as @service(scope=Scope.SINGLETON)
class UserService:
    pass
```

**Implementation:** Make `service` a class with `__call__` that handles both forms:

```python
class ServiceDecorator:
    def __call__(self, cls_or_scope=None, *, scope=Scope.SINGLETON):
        # Handle both @service and @service(scope=...)
        if cls_or_scope is None or isinstance(cls_or_scope, Scope):
            # Called as @service(scope=...) - return decorator
            actual_scope = cls_or_scope if isinstance(cls_or_scope, Scope) else scope
            def decorator(cls):
                return self._apply(cls, actual_scope)
            return decorator
        else:
            # Called as @service - apply immediately
            return self._apply(cls_or_scope, scope)

    def _apply(self, cls, scope):
        cls.__dioxide_scope__ = scope
        cls.__dioxide_profiles__ = frozenset(['*'])
        _component_registry.add(cls)
        return cls

service = ServiceDecorator()
```

### Lifecycle Implications

**REQUEST scope implies lifecycle management:**
- The whole point of REQUEST scope is cleanup when request ends
- Components without `dispose()` are allowed (no-op cleanup)
- Validation: Warn if REQUEST-scoped component lacks `@lifecycle`

```python
# Good: REQUEST scope with lifecycle
@adapter.for_(SessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class DatabaseSession:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...

# Allowed: REQUEST scope without lifecycle (just identity/caching)
@service(scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.request_id = uuid.uuid4()
    # No dispose needed - just identity tracking

# Warning logged at scan time:
# "RequestContext has scope=REQUEST but no @lifecycle.
#  Consider adding @lifecycle if cleanup is needed."
```

---

## Usage Ergonomics

### Primary Pattern: Scoped Container

```python
from dioxide import Container, Profile

container = Container(profile=Profile.PRODUCTION)

# Async context manager creates scope
async with container.create_scope() as scope:
    # Resolve from scope - not from container!
    session = scope.resolve(DatabaseSessionPort)
    service = scope.resolve(UserService)

    # Use services...
    await service.create_user("alice@example.com")
# Automatic cleanup on exit
```

### Why Scoped Container (Not Scope ID)

The issue #181 proposes:
```python
async with container.scope() as scope_id:
    service = container.resolve(RequestScopedService)  # Uses container, not scope
```

**Problems with this approach:**

1. **Confusing semantics:** User resolves from `container`, not `scope_id`
2. **Implicit state:** Container must track "current scope" - thread-local magic
3. **Error-prone:** Easy to resolve from wrong container
4. **Not async-safe:** Context vars needed for async, adds complexity

**Scoped Container is better:**

```python
async with container.create_scope() as scope:
    service = scope.resolve(UserService)  # Clear: resolve from scope
```

1. **Explicit:** User resolves from `scope`, which enforces rules
2. **Type-safe:** `ScopedContainer` has different type than `Container`
3. **No hidden state:** Each scope is independent
4. **Async-safe:** No context vars needed

### Manual Scope Control

For cases where async context manager doesn't fit:

```python
scope = await container.enter_scope()
try:
    session = scope.resolve(DatabaseSession)
    await do_work(session)
finally:
    await scope.dispose()
```

**Note:** `enter_scope()` returns `ScopedContainer`, not scope ID.

### Resolving Different Scope Types

```python
async with container.create_scope() as scope:
    # REQUEST: Cached in this scope, new per scope
    session = scope.resolve(DatabaseSession)

    # SINGLETON: From parent container, shared globally
    config = scope.resolve(AppConfig)

    # FACTORY: New instance every resolve
    handler = scope.resolve(RequestHandler)

    # Verify
    assert scope.resolve(DatabaseSession) is session  # Same instance
    assert scope.resolve(AppConfig) is container.resolve(AppConfig)  # Same
    assert scope.resolve(RequestHandler) is not handler  # Different
```

### Preventing Scope Violations at Scan Time

SINGLETON cannot depend on REQUEST (would capture one request's state):

```python
@service  # SINGLETON
class UserService:
    def __init__(self, session: DatabaseSessionPort):  # REQUEST
        self.session = session  # BUG: Which request's session?

# Detected at scan() time:
container.scan()  # Raises DependencyError
```

Valid dependency directions:
- SINGLETON can depend on: SINGLETON, FACTORY
- REQUEST can depend on: SINGLETON, REQUEST, FACTORY
- FACTORY can depend on: SINGLETON, REQUEST (if in scope), FACTORY

---

## Error Messages

### E1: Resolving REQUEST Component Outside Scope

```python
session = container.resolve(DatabaseSession)  # No scope!
```

**Error:**
```
dioxide.exceptions.ScopeError: Cannot resolve 'DatabaseSession' (scope=REQUEST) outside of a request scope.

'DatabaseSession' requires a request scope because it has scope=Scope.REQUEST.
REQUEST-scoped components are created fresh for each request and disposed when the request ends.

To fix this, wrap your resolution in a scope context:

    async with container.create_scope() as scope:
        session = scope.resolve(DatabaseSession)
        # Use session within this scope
    # session.dispose() called automatically

If using FastAPI, ensure DioxideMiddleware is installed:

    from dioxide.fastapi import DioxideMiddleware
    app.add_middleware(DioxideMiddleware, container=container)
```

### E2: SINGLETON Depending on REQUEST

```python
@service  # SINGLETON
class UserService:
    def __init__(self, session: DatabaseSessionPort):  # REQUEST
        ...

container.scan()  # Error!
```

**Error:**
```
dioxide.exceptions.DependencyError: Invalid dependency: 'UserService' (SINGLETON) depends on 'DatabaseSessionPort' (REQUEST).

SINGLETON-scoped components cannot depend on REQUEST-scoped components because:
- SINGLETON lives for the entire application lifetime
- REQUEST lives only for a single request
- The singleton would capture one request's instance and reuse it for all requests

This is almost always a bug. Common fixes:

1. Change 'UserService' to scope=Scope.REQUEST:

   @service(scope=Scope.REQUEST)
   class UserService:
       def __init__(self, session: DatabaseSessionPort):
           ...

2. Use a factory pattern - inject a session factory instead:

   @service
   class UserService:
       def __init__(self, session_factory: Callable[[], DatabaseSessionPort]):
           self.session_factory = session_factory

       async def do_work(self):
           session = self.session_factory()  # Get fresh session
           ...

3. If 'DatabaseSessionPort' is truly stateless, change it to SINGLETON.
```

### E3: Nested Scopes (Not Supported in v0.3.0)

```python
async with container.create_scope() as outer:
    async with container.create_scope() as inner:  # Error!
        ...
```

**Error:**
```
dioxide.exceptions.ScopeError: Nested scopes are not supported in dioxide v0.3.0.

You attempted to create a scope while already inside a scope.
Nested scopes may be supported in a future release.

Current workarounds:

1. If you need isolated state for a sub-operation, use FACTORY scope:

   @service(scope=Scope.FACTORY)
   class SubOperationContext:
       ...

2. If you need a completely independent scope, exit the current scope first:

   async with container.create_scope() as scope1:
       # First operation
       ...

   async with container.create_scope() as scope2:
       # Second operation (independent)
       ...

3. If you have a legitimate use case for nested scopes, please open an issue:
   https://github.com/mikelane/dioxide/issues
```

### E4: Lifecycle Failure During Scope Cleanup

```python
@adapter.for_(DatabaseSessionPort, scope=Scope.REQUEST)
@lifecycle
class BrokenSession:
    async def dispose(self) -> None:
        raise ConnectionError("Lost connection")

async with container.create_scope() as scope:
    session = scope.resolve(DatabaseSessionPort)
# dispose() fails!
```

**Error (logged, not raised):**
```
ERROR dioxide.lifecycle: Failed to dispose 'BrokenSession' during scope cleanup.

Original error: ConnectionError: Lost connection to database

Note:
- Other REQUEST-scoped components were successfully disposed
- The scope has exited despite this error
- Consider adding error handling in your dispose() method:

    async def dispose(self) -> None:
        try:
            await self.conn.close()
        except ConnectionError:
            logger.warning("Connection already closed")
```

**Design Decision:** Log lifecycle errors but don't raise - ensures all components get disposal attempt.

---

## Testing Ergonomics

### Pattern 1: pytest Fixture (Recommended)

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
async def scope():
    """Provide a request scope for each test."""
    container = Container(profile=Profile.TEST)
    async with container.create_scope() as scope:
        yield scope
    # Cleanup automatic

class DescribeUserService:
    async def it_creates_users(self, scope) -> None:
        service = scope.resolve(UserService)
        session = scope.resolve(DatabaseSessionPort)  # FakeSession

        user = await service.create_user("alice@example.com")

        assert user.email == "alice@example.com"
        assert len(session.saved_users) == 1
```

### Pattern 2: Multiple Scopes in One Test

```python
async def it_isolates_request_state(self) -> None:
    """Each scope gets fresh REQUEST instances."""
    container = Container(profile=Profile.TEST)

    async with container.create_scope() as scope1:
        ctx1 = scope1.resolve(RequestContext)
        ctx1.user_id = 123

    async with container.create_scope() as scope2:
        ctx2 = scope2.resolve(RequestContext)
        # Fresh instance - not polluted by scope1
        assert not hasattr(ctx2, 'user_id') or ctx2.user_id != 123

    # Verify they were different instances
    assert ctx1.request_id != ctx2.request_id
```

### Pattern 3: Container-Level Fixture (Full Lifecycle)

```python
@pytest.fixture
async def container():
    """Container with full lifecycle for integration tests."""
    container = Container(profile=Profile.TEST)
    await container.start()  # Initialize SINGLETON @lifecycle components
    yield container
    await container.stop()   # Dispose SINGLETON @lifecycle components

@pytest.fixture
async def scope(container):
    """Request scope within container lifecycle."""
    async with container.create_scope() as scope:
        yield scope

async def it_runs_full_lifecycle(self, scope) -> None:
    # SINGLETON components initialized, REQUEST scope active
    service = scope.resolve(UserService)
    ...
```

### Pattern 4: Accessing Fakes

```python
@pytest.fixture
async def scope():
    container = Container(profile=Profile.TEST)
    async with container.create_scope() as scope:
        yield scope

@pytest.fixture
def fake_email(scope) -> FakeEmailAdapter:
    """Type-safe access to fake email adapter."""
    return scope.resolve(EmailPort)

@pytest.fixture
def fake_db(scope) -> InMemoryDatabase:
    """Type-safe access to fake database."""
    return scope.resolve(DatabasePort)

async def it_sends_welcome_email(self, scope, fake_email) -> None:
    service = scope.resolve(UserService)

    await service.register("alice@example.com", "Alice")

    assert len(fake_email.sent_emails) == 1
    assert fake_email.sent_emails[0]["to"] == "alice@example.com"
```

---

## Framework Integration

### FastAPI Integration

#### Zero-Boilerplate Pattern (Recommended)

```python
# app/main.py
from fastapi import FastAPI
from dioxide import Container, Profile
from dioxide.fastapi import DioxideMiddleware, Resolve

# Create container
container = Container(profile=Profile.PRODUCTION)

# Create app with middleware
app = FastAPI()
app.add_middleware(DioxideMiddleware, container=container)

# Routes - dependencies auto-resolved from request scope
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Resolve(),  # Auto-injected from scope
    ctx: RequestContext = Resolve(),   # REQUEST-scoped, fresh per request
):
    return await service.get_user(user_id)
```

#### How `Resolve()` Works

```python
# dioxide/fastapi.py
from fastapi import Request, Depends
from typing import TypeVar, get_type_hints

T = TypeVar('T')

def Resolve() -> Any:
    """Marker for dioxide-resolved dependencies."""
    # Returns a Depends() that extracts from request scope
    def get_dependency(request: Request) -> Any:
        # Type is inferred from parameter annotation
        # See _inject_dependencies middleware hook
        ...
    return Depends(get_dependency)

class DioxideMiddleware:
    def __init__(self, app, container: Container):
        self.app = app
        self.container = container

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            async with self.container.create_scope() as request_scope:
                # Attach scope to request state
                scope["state"]["dioxide_scope"] = request_scope
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)
```

#### Explicit Pattern (More Control)

```python
from fastapi import FastAPI, Request, Depends
from dioxide import Container, Profile

container = Container(profile=Profile.PRODUCTION)

def get_scope(request: Request):
    """Get the dioxide scope from request state."""
    return request.state.dioxide_scope

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
):
    scope = request.state.dioxide_scope
    service = scope.resolve(UserService)
    return await service.get_user(user_id)
```

#### FastAPI Lifespan Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dioxide import Container, Profile
from dioxide.fastapi import DioxideMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage container lifecycle with FastAPI lifespan."""
    container = Container(profile=Profile.PRODUCTION)
    await container.start()  # Initialize SINGLETON @lifecycle components
    app.state.container = container
    yield
    await container.stop()   # Dispose SINGLETON @lifecycle components

app = FastAPI(lifespan=lifespan)
app.add_middleware(DioxideMiddleware)  # Uses app.state.container
```

### Flask Integration

```python
# app/__init__.py
from flask import Flask, g, request
from dioxide import Container, Profile

container = Container(profile=Profile.PRODUCTION)

def create_app():
    app = Flask(__name__)

    @app.before_request
    async def create_scope():
        """Create request scope before each request."""
        g.dioxide_scope = await container.enter_scope()

    @app.teardown_request
    async def dispose_scope(exception=None):
        """Dispose scope after each request."""
        if hasattr(g, 'dioxide_scope'):
            await g.dioxide_scope.dispose()

    return app

# routes.py
from flask import g

@app.route("/users/<int:user_id>")
async def get_user(user_id: int):
    scope = g.dioxide_scope
    service = scope.resolve(UserService)
    return await service.get_user(user_id)
```

#### Flask Helper (Optional)

```python
# dioxide/flask.py
from flask import g
from functools import wraps

def inject(cls):
    """Decorator to inject dioxide dependencies."""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            instance = g.dioxide_scope.resolve(cls)
            return await f(*args, instance, **kwargs)
        return wrapper
    return decorator

# Usage
@app.route("/users/<int:user_id>")
@inject(UserService)
async def get_user(user_id: int, service: UserService):
    return await service.get_user(user_id)
```

### Starlette Integration (Foundation for FastAPI)

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class DioxideMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, container: Container):
        super().__init__(app)
        self.container = container

    async def dispatch(self, request: Request, call_next):
        async with self.container.create_scope() as scope:
            request.state.dioxide_scope = scope
            response = await call_next(request)
        return response
```

---

## Advanced Patterns

### Future: Nested Scopes (Post v0.3.0)

For v0.3.0, nested scopes raise an error. Future versions may support:

```python
# Future API (v0.4.0+)
async with container.create_scope() as request_scope:
    # REQUEST-scoped instances
    async with request_scope.create_scope(Scope.OPERATION) as op_scope:
        # OPERATION-scoped instances (hypothetical)
        # Inherits from request_scope
        ...
```

### Factory Pattern for Avoiding Scope Issues

When SINGLETON needs REQUEST-scoped behavior:

```python
from typing import Callable

class DatabaseSessionPort(Protocol):
    async def query(self, sql: str) -> list[dict]: ...

@service  # SINGLETON
class UserService:
    def __init__(self, session_factory: Callable[[], DatabaseSessionPort]):
        self.session_factory = session_factory

    async def get_user(self, user_id: int) -> User:
        # Get fresh session for this operation
        session = self.session_factory()
        return await session.query(f"SELECT * FROM users WHERE id = {user_id}")
```

Register the factory:

```python
@adapter.for_(Callable[[], DatabaseSessionPort], profile=Profile.PRODUCTION)
class SessionFactory:
    def __init__(self, config: AppConfig):
        self.config = config

    def __call__(self) -> DatabaseSessionPort:
        return PostgresSession(self.config)
```

### Scope Inheritance (Future Consideration)

Some components should be visible in child scopes:

```python
# Future API
@service(scope=Scope.REQUEST, inherit=True)
class RequestLogger:
    """Logger available in nested scopes."""
    pass
```

### Custom Scope Types (Post-MLP)

For non-HTTP contexts (message queues, batch jobs):

```python
# Future API
class BatchScope(ScopeType):
    name = "batch"
    parent = Scope.SINGLETON

@adapter.for_(BatchContextPort, scope=BatchScope)
class BatchContext:
    ...
```

---

## Trade-offs and Rejected Alternatives

### Rejected: Scope ID Pattern (Issue #181's Original Design)

**Original proposal:**
```python
async with container.scope() as scope_id:
    service = container.resolve(RequestScopedService)
```

**Rejected because:**
1. Implicit state - container tracks "current scope"
2. Resolve from container, not scope - confusing
3. Requires thread-local or context var - complexity
4. Type system can't distinguish scoped vs unscoped resolution

**Chosen instead:** Scoped container pattern where you resolve from `scope`, not `container`.

### Rejected: Separate @request_scoped Decorator

**Alternative:**
```python
@request_scoped
@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION)
class PostgresSession:
    ...
```

**Rejected because:**
1. Inconsistent with existing API where scope is a parameter
2. Adds decorator to learn
3. Order matters (which decorator first?)
4. No benefit over `scope=Scope.REQUEST`

### Rejected: Implicit Scope from Context

**Alternative:**
```python
# Middleware sets up scope in context var
service = container.resolve(UserService)  # Works if in request context
```

**Rejected because:**
1. Too magic - violates "explicit over clever"
2. Hard to debug when scope missing
3. Testing requires mocking context vars
4. Not obvious from reading code that scope is required

### Rejected: Thread-Local Scope (Spring-style)

**Alternative:**
```python
# Scope stored in thread-local
container.set_current_scope(scope)
service = container.resolve(...)  # Uses thread-local scope
```

**Rejected because:**
1. Doesn't work with async/await
2. Hidden state is antipattern
3. Testing is complex
4. Thread-local leaks between requests in async

### Trade-off: Verbosity vs Explicitness

**More verbose:**
```python
async with container.create_scope() as scope:
    service = scope.resolve(UserService)
```

**Less verbose (rejected):**
```python
service = container.resolve(UserService)  # Implicit scope
```

**Decision:** Explicit is worth 1 extra line. Benefits:
- Clear scope boundaries in code
- Type-safe (scope vs container)
- No hidden state
- Easy to test

---

## Migration Path

### From Current API (No Request Scope)

**Before (v0.1.x):**
```python
# No request scope - create new containers per request (workaround)
@app.get("/users")
async def get_users():
    container = Container(profile=Profile.PRODUCTION)
    service = container.resolve(UserService)
    return await service.list()
```

**After (v0.3.0):**
```python
# Shared container, scoped resolution
container = Container(profile=Profile.PRODUCTION)
app.add_middleware(DioxideMiddleware, container=container)

@app.get("/users")
async def get_users(service: UserService = Resolve()):
    return await service.list()
```

### From Manual Session Management

**Before:**
```python
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    service = UserService(db)  # Manual wiring
    return await service.list()
```

**After:**
```python
@adapter.for_(DatabaseSessionPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    ...

@app.get("/users")
async def get_users(service: UserService = Resolve()):
    # Session automatically injected into UserService
    return await service.list()
```

### Backward Compatibility

- `Scope.SINGLETON` and `Scope.FACTORY` unchanged
- Existing `@service` and `@adapter.for_()` work identically
- `container.resolve()` behavior unchanged for non-REQUEST scopes
- New behavior only when `scope=Scope.REQUEST` used

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Issue #179, #180)

1. Add `Scope.REQUEST` enum value (already done per `scope.py`)
2. Implement scoped instance caching in Rust container
3. Add scope validation in dependency graph analysis

### Phase 2: Python API (Issue #181)

1. Implement `ScopedContainer` class
2. Add `Container.create_scope()` async context manager
3. Add `Container.enter_scope()` / `ScopedContainer.dispose()` manual API
4. Add scope-aware resolution logic
5. Implement lifecycle management for scoped instances
6. Add error messages for scope violations

### Phase 3: FastAPI Integration (Issue #182)

1. Create `dioxide.fastapi` package
2. Implement `DioxideMiddleware`
3. Implement `Resolve()` marker
4. Add type stubs for IDE support
5. Write integration tests

### Phase 4: Documentation (Issue #183)

1. Update API documentation
2. Add request scoping guide
3. Add FastAPI integration guide
4. Add testing patterns guide
5. Add migration guide

### Phase 5: Flask Integration (Issue #184, stretch)

1. Create `dioxide.flask` package
2. Implement request hooks integration
3. Add Flask-specific helpers
4. Write Flask examples

---

## Appendix: Type Stubs

```python
# dioxide/container.pyi
from typing import TypeVar, AsyncIterator, overload
from contextlib import asynccontextmanager

T = TypeVar('T')

class ScopedContainer:
    def resolve(self, component_type: type[T]) -> T: ...
    def __getitem__(self, component_type: type[T]) -> T: ...
    async def dispose(self) -> None: ...

class Container:
    @asynccontextmanager
    async def create_scope(self) -> AsyncIterator[ScopedContainer]: ...
    async def enter_scope(self) -> ScopedContainer: ...
    def resolve(self, component_type: type[T]) -> T: ...
    def __getitem__(self, component_type: type[T]) -> T: ...
```

---

## Summary

This design provides:

1. **Consistency** with dioxide's existing decorator-based API
2. **Explicitness** through scoped containers and clear scope boundaries
3. **Type safety** with distinct types for `Container` and `ScopedContainer`
4. **Framework integration** that eliminates boilerplate for FastAPI/Flask
5. **Testing ergonomics** with simple pytest fixture patterns
6. **Clear error messages** that guide users to solutions
7. **Migration path** from existing code with full backward compatibility

The scoped container pattern, adapted from .NET's proven `IServiceScope`, provides the best foundation for Python's async-first ecosystem while maintaining dioxide's principles of explicit, type-safe, and Pythonic design.
