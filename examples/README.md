# dioxide Examples

This directory contains working examples demonstrating dioxide's hexagonal architecture patterns,
real-world usage scenarios, and migration guides from other DI frameworks.

## Directory Structure

```
examples/
├── README.md                    # This file
├── getting_started_example.py   # Quick start example
├── hexagonal_architecture.py    # Complete hexagonal architecture demo
│
├── patterns/                    # Real-world patterns
│   ├── dependency-chain/        # Multi-service dependency chains
│   ├── circular-deps/           # Circular dependency detection/fixes
│   ├── caching/                 # Caching adapter pattern
│   └── external-api/            # External API with error injection
│
├── migrations/                  # Framework migration guides
│   ├── from-dependency-injector/  # Migration from dependency-injector
│   └── from-injector/             # Migration from injector
│
└── [framework integrations]/    # FastAPI, Flask, Celery, Click
    ├── fastapi/
    ├── flask/
    ├── celery/
    └── click/
```

## Running the Examples

### Prerequisites

**Note**: Examples must be run from the main repository directory where dioxide is installed.

```bash
# From the dioxide repository root:

# Install dioxide with development dependencies (uses PEP 735 dependency groups)
uv sync --group dev

# Build the Rust extension
maturin develop

# Run examples from repository root
python examples/hexagonal_architecture.py
```

---

## Pattern Examples

### Multi-Service Dependency Chain

**Location:** `patterns/dependency-chain/`

Demonstrates complex service dependencies: `OrderController -> OrderService -> [OrderRepository, ProductRepository, Cache, EventPublisher]`

```bash
# Run the example
python examples/patterns/dependency-chain/app/main.py

# Run tests
uv run pytest examples/patterns/dependency-chain/tests/ -v
```

**Key concepts:**
- Services depending on multiple ports
- Deep dependency trees resolved automatically
- Test isolation with fresh containers

### Circular Dependency Detection

**Location:** `patterns/circular-deps/`

Shows how dioxide detects circular dependencies and provides solutions using event-based patterns.

**Files:**
- `problem.py` - Demonstrates the circular dependency error
- `solution.py` - Shows the fix using events

```bash
# See the error
python examples/patterns/circular-deps/problem.py

# See the solution
python examples/patterns/circular-deps/solution.py
```

### Caching Adapter Pattern

**Location:** `patterns/caching/`

Demonstrates the caching adapter pattern where a `CachingUserRepository` wraps the real repository.

```bash
# Run the example
python examples/patterns/caching/app/main.py

# Run tests
uv run pytest examples/patterns/caching/tests/ -v
```

**Key concepts:**
- Decorator pattern for cross-cutting concerns
- Cache-aside pattern with dioxide
- Fake cache for testing with hit/miss tracking

### External API Integration

**Location:** `patterns/external-api/`

Complete payment gateway integration with error injection for testing various failure scenarios.

```bash
# Run the example
python examples/patterns/external-api/app/main.py

# Run tests
uv run pytest examples/patterns/external-api/tests/ -v
```

**Key concepts:**
- Error injection pattern for testing failures
- Transient failure simulation with retry logic
- Rate limiting and network error handling
- Domain-specific error types

---

## Migration Guides

### From dependency-injector

**Location:** `migrations/from-dependency-injector/`

Complete before/after comparison showing migration from the `dependency-injector` library.

**Structure:**
- `before/` - Original code using `dependency-injector`
- `after/` - Migrated code using `dioxide`

**Key changes:**
- Replace `Container` with provider definitions -> `@adapter.for_()` decorators
- Replace ABC interfaces -> Protocols
- Replace `providers.Singleton/Factory` -> `scope` parameter
- Replace provider overrides -> `Profile.TEST`

```bash
# Run dioxide version tests
uv run pytest examples/migrations/from-dependency-injector/after/tests/ -v
```

### From injector

**Location:** `migrations/from-injector/`

Complete before/after comparison showing migration from the `injector` library (Guice-inspired).

**Structure:**
- `before/` - Original code using `injector`
- `after/` - Migrated code using `dioxide`

**Key changes:**
- Remove `@inject` decorators (dioxide infers from type hints)
- Replace `Module` classes -> `@adapter.for_()` decorators
- Replace `Injector([modules])` -> `Container(profile=...)`
- Replace `binder.bind()` -> profile-based registration

```bash
# Run dioxide version tests
uv run pytest examples/migrations/from-injector/after/tests/ -v
```

---

### Hexagonal Architecture Example

The main example demonstrates the complete hexagonal architecture pattern:

```bash
python examples/hexagonal_architecture.py
```

**What it demonstrates:**

1. **Defining Ports (Interfaces)**: Using Python `Protocol` to define clean boundaries
2. **Creating Adapters**: Multiple implementations for different environments (production, test, dev)
3. **Writing Services**: Core business logic that depends on ports, not implementations
4. **Profile-Based Injection**: Swapping implementations with `profile` parameter
5. **Testing with Fakes**: Fast, reliable tests without mocks

**Expected output:**

```
🎯 Hexagonal Architecture with dioxide

======================================================================
PRODUCTION EXAMPLE - Real SendGrid + PostgreSQL
======================================================================

📧 [SendGrid] Sending to alice@example.com: Welcome!
💾 [Postgres] Saved user 1: Alice Smith (alice@example.com)

✅ User registered with ID: 1

======================================================================
TEST EXAMPLE - Fake Email + In-Memory Database
======================================================================

💾 [InMemory] Saved user 1: Bob Jones
✅ [Fake] Recorded email to bob@test.com: Welcome!
🔍 [InMemory] Looking up user 1

✅ All assertions passed! User ID: 1

======================================================================
DEVELOPMENT EXAMPLE - Console Email + Postgres
======================================================================

💾 [Postgres] Saved user 1: Charlie Brown (charlie@dev.local)
📝 [Console] Email to charlie@dev.local
   Subject: Welcome!
   Body: Hello Charlie Brown, welcome to our platform!

✅ User registered with ID: 1

======================================================================
KEY TAKEAWAYS
======================================================================
✅ Core logic (services) has ZERO infrastructure knowledge
✅ Testing uses fast fakes, not slow mocks
✅ Swapping implementations = changing one line (profile)
✅ Type-safe dependency injection via constructor hints
✅ Ports (Protocols) define clear boundaries
======================================================================
```

## Key Concepts

### Ports (Interfaces)

Ports define **what** operations are needed, not **how** they're implemented:

```python
from typing import Protocol

class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None:
        ...
```

### Adapters (Implementations)

Adapters implement ports for specific environments:

```python
from dioxide import adapter, Profile

@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real SendGrid API calls
        pass

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
```

### Services (Core Logic)

Services contain business logic and depend on **ports**, not adapters:

```python
from dioxide import service

@service
class UserService:
    def __init__(self, email: EmailPort, db: DatabasePort):
        self.email = email  # Don't know/care which adapter
        self.db = db

    async def register_user(self, name: str, email: str) -> int:
        user_id = await self.db.save_user(name, email)
        await self.email.send(email, "Welcome!", f"Hello {name}")
        return user_id
```

### Profile-Based Injection

Swap all implementations by changing the profile:

```python
from dioxide import Container, Profile

# Production: Real SendGrid + PostgreSQL
prod_container = Container(profile=Profile.PRODUCTION)
prod_service = prod_container.resolve(UserService)

# Testing: Fake email + In-memory DB
test_container = Container(profile=Profile.TEST)
test_service = test_container.resolve(UserService)
```

## Why This Pattern Matters

### Testability

**Before (tightly coupled):**
```python
class UserService:
    def __init__(self):
        self.email = SendGridClient()  # Hard-coded dependency
        self.db = PostgresClient()

    async def register_user(self, name: str, email: str):
        # Testing requires mocking SendGrid and Postgres
        pass
```

**After (hexagonal architecture):**
```python
@service
class UserService:
    def __init__(self, email: EmailPort, db: DatabasePort):
        self.email = email  # Injected port
        self.db = db

    async def register_user(self, name: str, email: str):
        # Testing uses fast fakes, no mocks needed
        pass
```

### Maintainability

**Swapping implementations is trivial:**

- Want to switch from SendGrid to AWS SES? Create new `SESAdapter`, change nothing else
- Need to test offline? Use `profile=Profile.TEST`, get fakes automatically
- Want console logging in dev? Use `profile=Profile.DEVELOPMENT`

**Core logic never changes** - only the adapters change.

### Type Safety

If mypy passes, your wiring is correct:

```bash
mypy examples/hexagonal_architecture.py
# Success: no issues found
```

Type errors are caught at **static analysis time**, not runtime:

```python
@service
class UserService:
    def __init__(self, email: EmailPort, wrong_type: str):  # mypy error!
        pass
```

## Further Reading

- **Design Principles**: `docs/design-principles.md` - dioxide's design philosophy
- **Main README**: `README.md` - Quick start and overview
- **CLAUDE.md**: Developer guide for working on dioxide

## Contributing Examples

Want to add an example? Follow these guidelines:

1. **Create issue** for the example
2. **Ensure it runs** - verify with `python examples/your_example.py`
3. **Add to this README** - document what it demonstrates
4. **Include docstrings** - explain the key concepts
5. **Keep it focused** - one concept per example

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.
