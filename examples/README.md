# dioxide Examples

This directory contains working examples demonstrating dioxide's hexagonal architecture patterns.

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
prod_container = Container()
prod_container.scan(profile=Profile.PRODUCTION)
prod_service = prod_container.resolve(UserService)

# Testing: Fake email + In-memory DB
test_container = Container()
test_container.scan(profile=Profile.TEST)
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

- **MLP Vision**: `docs/MLP_VISION.md` - dioxide's design philosophy
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
