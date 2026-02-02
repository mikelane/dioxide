# Understanding @service vs @adapter

This guide clarifies the mental model for when to use `@service` versus `@adapter.for_()` decorators in dioxide.

## The Decision Tree

Use this flowchart when deciding which decorator to apply.

```
Do you need to swap implementations based on profile (test/prod/dev)?
├── YES → Define a Port (Protocol) + use @adapter.for_(Port, profile=...)
│         Examples: Database, Email, Payment Gateway, External APIs
│
└── NO → Use @service
         Examples: Business logic, Domain services, Use cases

Is this core business logic that shouldn't change between environments?
├── YES → @service
└── NO → @adapter.for_(Port)

Does this component talk to external systems (DB, network, filesystem)?
├── YES → Port + @adapter (allows faking in tests)
└── NO → Probably @service
```

## The Mental Model

Understanding the relationship between services, ports, and adapters is fundamental to dioxide and hexagonal architecture.

```{mermaid}
flowchart LR
    subgraph driving["External World<br/>(Driving Side)"]
        direction TB
        FA[FastAPI]
        CL[Click]
        FL[Flask]
    end

    subgraph core["Application Core"]
        direction TB
        SVC["@service<br/>(core logic)"]
    end

    subgraph driven["External World<br/>(Driven Side)"]
        direction TB
        PORT["Port<br/>(Protocol)"]
        ADP["@adapter<br/>(implements port)"]
    end

    driving -->|"calls"| core
    core -->|"depends on"| PORT
    PORT -->|"implemented by"| ADP
```

### @service: The Core

Services represent **core business logic** - the domain rules that define your application's behavior. They sit at the center of the hexagon.

**Key characteristics of @service:**

| Characteristic | Description |
|----------------|-------------|
| **Singleton** | One shared instance across the application |
| **Profile-agnostic** | Available in ALL profiles (production, test, development) |
| **Depends on Ports** | Uses Protocol types, not concrete implementations |
| **Pure business logic** | No knowledge of databases, APIs, or infrastructure |

**Why @service doesn't require a port:**

Services ARE the abstraction. They represent your domain logic, which doesn't need to be swapped based on environment. The same `UserService` runs in production and tests - only its *dependencies* (the ports) change.

### @adapter.for_(): The Boundaries

Adapters are **concrete implementations** of ports that connect your application to the outside world. They live at the hexagon's edges.

**Key characteristics of @adapter.for_():**

| Characteristic | Description |
|----------------|-------------|
| **Profile-specific** | Different adapter per environment |
| **Implements a Port** | Satisfies a Protocol contract |
| **Singleton by default** | One instance per profile (can be overridden) |
| **Infrastructure code** | Talks to databases, APIs, filesystems |

**Why @adapter requires a port:**

Adapters implement abstractions (ports). Multiple adapters can satisfy the same port contract - one for production (real database), one for testing (in-memory), one for development (local file). The container selects the right one based on the active profile.

### Ports: The Contracts

Ports are **interfaces** (Python Protocols) that define contracts between your core and the outside world.

**Important:** Ports have NO decorator. They're just type definitions.

```python
from typing import Protocol

class EmailPort(Protocol):
    """Port defining email operations - no decorator needed."""
    async def send(self, to: str, subject: str, body: str) -> None: ...
```

## Practical Examples

### Example 1: Email System

**Port (the interface):**
```python
from typing import Protocol

class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...
```

**Adapters (profile-specific implementations):**
```python
from dioxide import adapter, Profile

@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Real email via SendGrid API."""
    async def send(self, to: str, subject: str, body: str) -> None:
        # Real API calls
        ...

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Fast fake for testing."""
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    """Console logging for development."""
    async def send(self, to: str, subject: str, body: str) -> None:
        print(f"EMAIL TO: {to}\nSUBJECT: {subject}")
```

**Service (core business logic):**
```python
from dioxide import service

@service
class NotificationService:
    """Business logic - depends on EmailPort, not concrete adapter."""
    def __init__(self, email: EmailPort):
        self.email = email  # Could be SendGrid, Fake, or Console

    async def send_welcome(self, user_email: str, user_name: str) -> None:
        # Business rule: validate email
        if "@" not in user_email:
            raise ValueError("Invalid email")

        # Delegate to port - service doesn't know/care which adapter
        await self.email.send(
            to=user_email,
            subject="Welcome!",
            body=f"Hello {user_name}, welcome to our service!"
        )
```

### Example 2: Configuration

Sometimes you need something that IS a service (singleton, profile-agnostic) but also loads from environment:

```python
from dioxide import service
from pydantic_settings import BaseSettings

@service
class AppConfig(BaseSettings):
    """Configuration - it's a service, not an adapter.

    Why @service?
    - Same config class runs in all profiles
    - Doesn't implement a port
    - Just stores configuration values
    """
    database_url: str = "sqlite:///dev.db"
    sendgrid_api_key: str = ""
```

### Example 3: Repository Pattern

**Port:**
```python
class UserRepository(Protocol):
    async def save(self, user: dict) -> None: ...
    async def find_by_id(self, user_id: str) -> dict | None: ...
```

**Production adapter:**
```python
@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class PostgresUserRepository:
    """Real database."""
    def __init__(self, db: Database):
        self.db = db

    async def save(self, user: dict) -> None:
        # Real SQL
        ...
```

**Test adapter:**
```python
@adapter.for_(UserRepository, profile=Profile.TEST)
class InMemoryUserRepository:
    """Fast fake - no database needed."""
    def __init__(self):
        self.users = {}

    async def save(self, user: dict) -> None:
        self.users[user["id"]] = user

    async def find_by_id(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def seed(self, *users: dict) -> None:
        """Test helper - seed with test data."""
        for user in users:
            self.users[user["id"]] = user
```

## Quick Reference Table

| Question | @service | @adapter.for_() |
|----------|----------|-----------------|
| **What is it?** | Core domain logic | Boundary implementation |
| **Requires a port?** | No | Yes |
| **Profile-specific?** | No (same in all profiles) | Yes (different per profile) |
| **Scope** | Singleton | Singleton (default) |
| **Dependencies** | Depends on Ports | May depend on services or other adapters |
| **Testing** | Same service, different adapters injected | Different adapter per profile |

## Common Patterns

### Pattern 1: Service Depends on Multiple Ports

```python
@service
class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        payments: PaymentGateway,
        email: EmailPort,
        clock: ClockPort
    ):
        # All dependencies are ports - injectable via profiles
        self.orders = orders
        self.payments = payments
        self.email = email
        self.clock = clock

    async def process_order(self, order_id: str) -> None:
        # Pure business logic using ports
        order = await self.orders.find_by_id(order_id)
        await self.payments.charge(order["amount"], order["card_token"])
        await self.email.send(order["customer_email"], "Order Confirmed", "...")
```

### Pattern 2: Adapter Depends on Configuration

```python
@adapter.for_(PaymentGateway, profile=Profile.PRODUCTION)
class StripeAdapter:
    def __init__(self, config: AppConfig):
        # Adapters can depend on services like AppConfig
        self.api_key = config.stripe_api_key
```

### Pattern 3: Adapter for Multiple Profiles

```python
@adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
class InMemoryCacheAdapter:
    """Simple cache for both test and dev environments."""
    def __init__(self):
        self._cache = {}
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Service with Infrastructure

```python
# BAD - service contains infrastructure
@service
class UserService:
    async def register(self, email: str) -> None:
        # Don't do this!
        conn = psycopg2.connect("dbname=prod")  # Infrastructure in service!
        sendgrid.send(to=email, subject="Welcome!")  # More infrastructure!
```

**Fix:** Depend on ports instead.

### Anti-Pattern 2: Adapter with Business Logic

```python
# BAD - adapter contains business logic
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        # Don't put business rules here!
        if "@" not in to:
            raise ValueError("Invalid email")  # This is a business rule!
        # ... actual sending
```

**Fix:** Move business logic to the service.

### Anti-Pattern 3: Service that Should Be an Adapter

```python
# BAD - this should be an adapter
@service
class EmailSender:
    async def send(self, to: str, subject: str, body: str) -> None:
        # This talks to external systems - should be an adapter!
        async with httpx.AsyncClient() as client:
            await client.post("https://api.sendgrid.com/...")
```

**Fix:** Create a port and use `@adapter.for_()`.

## Summary

**Use @service when:**
- Implementing core business logic
- The component shouldn't change between environments
- You're writing domain rules and use cases

**Use @adapter.for_() when:**
- Connecting to external systems (DB, API, filesystem)
- You need different implementations for different profiles
- You want to swap real implementations for fakes in tests

**The key insight:** Services depend on ports (abstractions), adapters implement ports (concrete). This IS the Dependency Inversion Principle in action.

## Next Steps

- Read [Hexagonal Architecture with dioxide](hexagonal_architecture.md) for the full picture
- See [Testing with Fakes](testing_with_fakes.rst) for testing patterns
- Check the [API Reference](../api/dioxide/index.rst) for decorator details
