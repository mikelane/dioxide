# Scoping Guide

This guide explains dioxide's scoping system, a powerful primitive for isolating dependencies within bounded contexts. While commonly used for web request handling, scoping is a **universal concept** applicable to any bounded execution context.

## What is Scoping?

**Scoping** creates an isolated dependency context where:

- **Scoped dependencies** get fresh instances per scope
- **Singleton dependencies** remain shared across all scopes
- **Lifecycle boundaries** are respected (resources created in scope are disposed with scope)

Think of a scope as a "mini-container" that inherits from the parent container but has its own instances for scoped components.

```{mermaid}
flowchart TB
    subgraph Container["Container (Application Lifetime)"]
        S1[("UserService<br/>(singleton)")]
        S2[("EmailService<br/>(singleton)")]

        subgraph Scope1["Scope 1 (e.g., Request A)"]
            R1A["RequestContext<br/>(scoped)"]
            R1B["AuditLogger<br/>(scoped)"]
        end

        subgraph Scope2["Scope 2 (e.g., Request B)"]
            R2A["RequestContext<br/>(scoped)"]
            R2B["AuditLogger<br/>(scoped)"]
        end

        S1 --> R1A
        S1 --> R2A
        S2 --> R1A
        S2 --> R2A
    end

    style S1 fill:#e1f5fe
    style S2 fill:#e1f5fe
    style R1A fill:#fff3e0
    style R1B fill:#fff3e0
    style R2A fill:#fff3e0
    style R2B fill:#fff3e0
```

**Key insight**: Singletons are shared; scoped instances are isolated per scope.

## Why You Need Scoping

### The Problem: Shared State Pollution

Without scoping, request-specific state can leak between requests:

```python
# Without scoping - DANGEROUS!
@service
class RequestContext:
    def __init__(self):
        self.user_id = None
        self.request_id = None
        self.start_time = None

# Problem: Same instance shared across all requests!
# Request A sets user_id = "alice"
# Request B reads user_id and sees "alice" instead of "bob"
```

### The Solution: Scoped Isolation

With scoping, each request gets its own context:

```python
from dioxide import adapter, Profile, Scope

class RequestContextPort(Protocol):
    user_id: str | None
    request_id: str
    start_time: datetime

@adapter.for_(RequestContextPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class RequestContext:
    def __init__(self):
        self.user_id = None
        self.request_id = str(uuid.uuid4())
        self.start_time = datetime.now(UTC)

# Now each scope gets a fresh RequestContext!
```

## The Scoping Primitive

Dioxide provides a simple, universal scoping primitive:

```python
from dioxide import Container, Profile

# Create and configure container
container = Container()
container.scan(profile=Profile.PRODUCTION)

# Create a scope for bounded work
async with container.create_scope() as scope:
    # Resolve dependencies within this scope
    context = scope.resolve(RequestContextPort)
    service = scope.resolve(UserService)

    # Use them...
    await service.process_request(context)

# Scope ends - scoped instances disposed
```

### How `create_scope()` Works

```{mermaid}
sequenceDiagram
    participant App as Application
    participant Container as Container
    participant Scope as ScopedContainer
    participant Scoped as Scoped Instance

    App->>Container: create_scope()
    Container->>Scope: Create child scope
    Scope-->>App: ScopedContainer

    App->>Scope: resolve(RequestContext)
    Scope->>Scoped: Create new instance
    Scoped-->>Scope: Instance
    Scope-->>App: RequestContext

    Note over App,Scoped: Do work within scope...

    App->>Scope: Exit scope (async with ends)
    Scope->>Scoped: dispose()
    Scoped-->>Scope: Cleanup complete
    Scope-->>App: Scope closed
```

**Key behaviors:**

1. `create_scope()` returns a `ScopedContainer`
2. Scoped components get fresh instances within the scope
3. Singletons resolve to the same instance as the parent container
4. When the scope exits, all scoped components are disposed (in reverse creation order)

## When to Use REQUEST Scope

### Use Scope.REQUEST For

**Adapters that need per-request isolation:**

```python
# Database connections scoped to request
@adapter.for_(DatabaseSession, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    async def initialize(self):
        self.conn = await pool.acquire()

    async def dispose(self):
        await self.conn.release()

# Request-specific audit logging
@adapter.for_(AuditLogger, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class RequestAuditLogger:
    def __init__(self, context: RequestContextPort):
        self.request_id = context.request_id

    def log(self, event: str):
        logger.info(f"[{self.request_id}] {event}")

# User context per request
@adapter.for_(RequestContextPort, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
class HttpRequestContext:
    def __init__(self):
        self.user_id = None
        self.request_id = str(uuid.uuid4())
```

### Do NOT Use Scope.REQUEST For

**Services (core business logic):**

```python
# WRONG: Services should be singleton!
@service(scope=Scope.REQUEST)  # Never do this!
class UserService:
    pass

# RIGHT: Services are always singleton
@service
class UserService:
    def __init__(self, db: DatabaseSession, audit: AuditLogger):
        self.db = db
        self.audit = audit
```

**Why?** Services contain business logic that doesn't change per request. They should be singletons that receive request-scoped adapters via dependency injection.

```{mermaid}
flowchart LR
    subgraph Singleton["Singleton (Shared)"]
        US["UserService"]
        ES["EmailService"]
    end

    subgraph Scoped["Request-Scoped (Per Request)"]
        RC["RequestContext"]
        DB["DatabaseSession"]
        AL["AuditLogger"]
    end

    US --> RC
    US --> DB
    US --> AL

    style US fill:#e1f5fe
    style ES fill:#e1f5fe
    style RC fill:#fff3e0
    style DB fill:#fff3e0
    style AL fill:#fff3e0
```

**Rule of thumb:**
- **Adapters**: May use `Scope.REQUEST` when they hold request-specific state
- **Services**: Always `Scope.SINGLETON` (the default)

## Non-Web Use Cases

Scoping is **not just for web requests**. The same primitive works for any bounded execution context.

### Celery/Background Tasks

Each task gets isolated dependencies:

```python
from celery import Celery
from dioxide import Container, Profile

app = Celery('tasks')
container = Container()
container.scan(profile=Profile.PRODUCTION)

@app.task
async def process_order(order_id: int):
    """Each task invocation gets its own scope."""
    async with container.create_scope() as scope:
        # Fresh instances for this task
        context = scope.resolve(TaskContextPort)
        context.task_id = process_order.request.id

        order_service = scope.resolve(OrderService)
        await order_service.process(order_id)
    # Task-scoped instances disposed
```

### CLI Applications

Each command invocation gets its own scope:

```python
import click
from dioxide import Container, Profile

container = Container()
container.scan(profile=Profile.PRODUCTION)

@click.group()
def cli():
    pass

@cli.command()
@click.argument('user_id')
async def process_user(user_id: str):
    """Each CLI command gets its own scope."""
    async with container.create_scope() as scope:
        context = scope.resolve(CommandContextPort)
        context.command = "process_user"
        context.args = {"user_id": user_id}

        service = scope.resolve(UserService)
        await service.process(user_id)
```

### Batch Processing / Data Pipelines

Each batch gets isolated dependencies:

```python
async def process_batch(items: list[Item]):
    """Each batch gets its own scope."""
    async with container.create_scope() as scope:
        # Fresh database connection for this batch
        db = scope.resolve(DatabaseSession)

        # Batch-specific metrics
        metrics = scope.resolve(BatchMetricsPort)
        metrics.batch_size = len(items)

        processor = scope.resolve(BatchProcessor)
        await processor.process_all(items)
    # Connection released, metrics flushed
```

### Test Isolation

Each test gets a clean scope:

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
async def scope():
    """Fresh scope for each test - complete isolation."""
    container = Container()
    container.scan(profile=Profile.TEST)

    async with container.create_scope() as test_scope:
        yield test_scope
    # All test-scoped instances cleaned up

async def test_user_registration(scope):
    """Test runs in isolated scope."""
    # Fresh instances for this test only
    users = scope.resolve(UserRepository)
    email = scope.resolve(EmailPort)

    service = scope.resolve(UserService)
    await service.register("alice@example.com")

    assert len(email.sent_emails) == 1
    # Next test gets fresh empty fakes!
```

### Scheduled Jobs

Each job run gets its own scope:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)
async def nightly_cleanup():
    """Each scheduled run gets its own scope."""
    async with container.create_scope() as scope:
        context = scope.resolve(JobContextPort)
        context.job_name = "nightly_cleanup"
        context.run_id = str(uuid.uuid4())

        cleanup = scope.resolve(CleanupService)
        await cleanup.run()
```

## Architecture: Scopes and the Dependency Graph

Understanding how scopes interact with the dependency graph is crucial.

### Scope Inheritance

Scopes inherit from their parent container:

```{mermaid}
flowchart TB
    subgraph Parent["Parent Container"]
        direction TB
        PS1["ConfigService<br/>(singleton)"]
        PS2["UserService<br/>(singleton)"]
    end

    subgraph Child["Scoped Container"]
        direction TB
        CS1["DatabaseSession<br/>(scoped)"]
        CS2["RequestContext<br/>(scoped)"]
    end

    Child -->|inherits from| Parent
    CS1 -->|depends on| PS1
    PS2 -->|injected with| CS1

    style PS1 fill:#e1f5fe
    style PS2 fill:#e1f5fe
    style CS1 fill:#fff3e0
    style CS2 fill:#fff3e0
```

**Resolution rules:**
1. When resolving in a scope, check if component is `Scope.REQUEST`
2. If REQUEST: create/return scope-local instance
3. If SINGLETON: delegate to parent container

### Captive Dependencies (Anti-Pattern)

**DANGER**: A singleton must NEVER depend on a scoped component directly.

```python
# WRONG: Captive dependency!
@service  # Singleton
class UserService:
    def __init__(self, session: DatabaseSession):  # REQUEST-scoped!
        self.session = session  # Captured forever!

# This singleton captures the first scope's session and uses it forever,
# even after that scope is disposed. This causes:
# - Stale connections
# - Connection pool exhaustion
# - Data corruption between requests
```

Dioxide **detects captive dependencies** and raises `CaptiveDependencyError` at scan time:

```
CaptiveDependencyError: Singleton 'UserService' cannot depend on request-scoped
'DatabaseSession'. Singletons outlive request scopes, which would capture a
stale instance.

Solutions:
  1. Make UserService request-scoped (if it needs per-request state)
  2. Inject a factory: Callable[[], DatabaseSession] instead
  3. Inject the port and resolve within methods
```

### Correct Pattern: Inject Ports, Resolve in Methods

```python
@service
class UserService:
    def __init__(self, container: Container):
        self._container = container

    async def get_user(self, user_id: int) -> User:
        # Resolve scoped dependency when needed
        async with self._container.create_scope() as scope:
            session = scope.resolve(DatabaseSession)
            return await session.query(User).get(user_id)
```

Or, use the injected scope in web frameworks:

```python
# FastAPI example - scope created per request by middleware
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    scope: ScopedContainer = Depends(get_request_scope)
):
    session = scope.resolve(DatabaseSession)
    service = scope.resolve(UserService)
    return await service.get_user(user_id)
```

## Lifecycle Management in Scopes

Scoped components can use `@lifecycle` for initialization and cleanup:

```python
@adapter.for_(DatabaseSession, profile=Profile.PRODUCTION, scope=Scope.REQUEST)
@lifecycle
class PostgresSession:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.conn = None

    async def initialize(self):
        """Called when scope creates this instance."""
        self.conn = await asyncpg.connect(self.config.database_url)

    async def dispose(self):
        """Called when scope ends."""
        if self.conn:
            await self.conn.close()

    async def query(self, sql: str) -> list:
        return await self.conn.fetch(sql)
```

### Lifecycle Order in Scopes

```{mermaid}
sequenceDiagram
    participant Scope as ScopedContainer
    participant A as Component A
    participant B as Component B (depends on A)

    Note over Scope,B: Scope Creation

    Scope->>A: Create instance
    Scope->>A: initialize()
    A-->>Scope: Ready

    Scope->>B: Create instance (receives A)
    Scope->>B: initialize()
    B-->>Scope: Ready

    Note over Scope,B: Work happens...

    Note over Scope,B: Scope Exit (Reverse Order)

    Scope->>B: dispose()
    B-->>Scope: Cleaned up

    Scope->>A: dispose()
    A-->>Scope: Cleaned up
```

**Guarantees:**
- Initialize in dependency order (dependencies before dependents)
- Dispose in reverse order (dependents before dependencies)
- Disposal happens even if exceptions occur

## Error Messages and How to Fix Them

### ScopeError: Cannot resolve request-scoped outside scope

```
ScopeError: Cannot resolve 'DatabaseSession' (Scope.REQUEST) outside of a scope.
Request-scoped components can only be resolved within an active scope.

Fix: Use container.create_scope() to create a scope first:

    async with container.create_scope() as scope:
        session = scope.resolve(DatabaseSession)
```

**Cause**: Trying to resolve a REQUEST-scoped component directly from the container.

**Fix**: Create a scope first using `container.create_scope()`.

### CaptiveDependencyError: Singleton depends on scoped

```
CaptiveDependencyError: Singleton 'UserService' cannot depend on request-scoped
'DatabaseSession'. Singletons outlive request scopes, which would capture a
stale instance.
```

**Cause**: A singleton service has a REQUEST-scoped dependency in its constructor.

**Fix options**:
1. Make the service REQUEST-scoped (if appropriate)
2. Don't inject the scoped dependency directly; resolve it within methods
3. Inject a factory function instead

### CircularDependencyError in scopes

Circular dependencies are detected at scan time, before any scopes are created:

```
CircularDependencyError: Circular dependency detected:
  UserService -> AuditLogger -> RequestContext -> UserService
```

**Fix**: Break the cycle by introducing an interface or restructuring dependencies.

## Testing Request-Scoped Components

### Pattern 1: Test-Scoped Fixtures

```python
@pytest.fixture
async def scope():
    """Each test gets a fresh scope."""
    container = Container()
    container.scan(profile=Profile.TEST)

    async with container.create_scope() as test_scope:
        yield test_scope

async def test_database_session(scope):
    session = scope.resolve(DatabaseSession)
    # Session is scoped to this test
    result = await session.query("SELECT 1")
    assert result is not None
```

### Pattern 2: Nested Scopes for Request Simulation

```python
async def test_multiple_requests(container):
    """Simulate multiple requests, each with isolated scope."""
    container.scan(profile=Profile.TEST)

    # Simulate Request 1
    async with container.create_scope() as scope1:
        ctx1 = scope1.resolve(RequestContextPort)
        ctx1.user_id = "alice"
        request_id_1 = ctx1.request_id

    # Simulate Request 2
    async with container.create_scope() as scope2:
        ctx2 = scope2.resolve(RequestContextPort)
        ctx2.user_id = "bob"
        request_id_2 = ctx2.request_id

    # Verify isolation
    assert request_id_1 != request_id_2
```

### Pattern 3: Override Scoped Dependencies

```python
@pytest.fixture
def test_context():
    """Pre-configured test context."""
    ctx = TestRequestContext()
    ctx.user_id = "test-user"
    ctx.request_id = "test-request-123"
    return ctx

async def test_with_known_context(scope, test_context):
    # Override the scoped dependency
    scope.register_instance(RequestContextPort, test_context)

    service = scope.resolve(UserService)
    result = await service.current_user()

    assert result.id == "test-user"
```

## FastAPI Integration Example

Here's how scoping integrates with FastAPI:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from dioxide import Container, Profile, ScopedContainer

container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize container."""
    container.scan(profile=Profile.PRODUCTION)
    async with container:
        yield

app = FastAPI(lifespan=lifespan)

# Middleware to create request scope
@app.middleware("http")
async def scope_middleware(request: Request, call_next):
    async with container.create_scope() as scope:
        request.state.scope = scope
        response = await call_next(request)
    return response

# Dependency to get current scope
def get_scope(request: Request) -> ScopedContainer:
    return request.state.scope

# Use in routes
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    scope: ScopedContainer = Depends(get_scope)
):
    # Resolve request-scoped dependencies
    session = scope.resolve(DatabaseSession)
    service = scope.resolve(UserService)

    return await service.get_user(user_id)
```

## Summary

**Key concepts:**

1. **Scoping** creates isolated dependency contexts within bounded execution
2. **`create_scope()`** returns a `ScopedContainer` for resolving scoped dependencies
3. **Scope.REQUEST** is for adapters that need per-execution isolation (not services)
4. **Universal primitive** - works for web, CLI, background tasks, batch processing, tests
5. **Captive dependencies** are detected at scan time (singleton -> scoped = error)
6. **Lifecycle** is respected: scoped components with `@lifecycle` are initialized/disposed with the scope

**When to use Scope.REQUEST:**

| Component Type | Scope | Example |
|---------------|-------|---------|
| Core services | SINGLETON | `UserService`, `EmailService` |
| Request context | REQUEST | `RequestContext`, `UserSession` |
| Database connections | REQUEST | `DatabaseSession`, `Transaction` |
| Audit/logging | REQUEST | `AuditLogger`, `RequestMetrics` |
| Test fakes | Either | Depends on test needs |

**Decision flowchart:**

```{mermaid}
flowchart TD
    A[New Component] --> B{Is it core business logic?}
    B -->|Yes| C[Use @service<br/>SINGLETON]
    B -->|No| D{Does it hold per-request state?}
    D -->|No| E{Does it need per-request resources?}
    D -->|Yes| F[Use Scope.REQUEST]
    E -->|No| G[Use SINGLETON<br/>default]
    E -->|Yes| F

    style C fill:#e1f5fe
    style G fill:#e1f5fe
    style F fill:#fff3e0
```

Scoping in dioxide enables clean, isolated execution contexts while maintaining the simplicity of the dependency injection model. Use it whenever you need bounded, isolated dependencies - whether that's web requests, background tasks, CLI commands, or test cases.
