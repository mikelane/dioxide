# Choosing Between @service and @adapter

**Goal:** Answer "which decorator?" in 10 seconds.

## The Decision Tree

```{mermaid}
flowchart TD
    START([What decorator should I use?])

    Q1{Does it talk to<br/>external systems?}
    Q2{Should different profiles<br/>use different implementations?}

    SERVICE[/"@service<br/><i>Singleton, profile-agnostic</i>"/]
    ADAPTER[/"@adapter.for_(Port, profile=...)<br/><i>Profile-specific implementation</i>"/]

    START --> Q1

    Q1 -->|"Yes<br/><small>DB, API, file, network</small>"| ADAPTER
    Q1 -->|"No<br/><small>Pure logic</small>"| Q2

    Q2 -->|"Yes<br/><small>Test vs prod behavior</small>"| ADAPTER
    Q2 -->|"No<br/><small>Same everywhere</small>"| SERVICE

    style SERVICE fill:#2ecc71,stroke:#27ae60,color:#000
    style ADAPTER fill:#e67e22,stroke:#d35400,color:#000
    style Q1 fill:#3498db,stroke:#2980b9,color:#fff
    style Q2 fill:#3498db,stroke:#2980b9,color:#fff
```

## Quick Summary

| Use This | When | Examples |
|----------|------|----------|
| `@service` | Core business logic that stays the same everywhere | `OrderService`, `PricingEngine`, `ValidationService` |
| `@adapter.for_()` | Connects to external systems OR needs profile switching | `PostgresRepo`, `SendGridEmail`, `FakeClock` |

## Code Examples

### Use @service for Business Logic

Business rules, use cases, and domain services that don't change between environments.

```python
from dioxide import service

@service
class OrderService:
    """Core business logic - same in production and tests."""

    def __init__(self, orders: OrderRepository, payments: PaymentGateway):
        self.orders = orders  # Depends on PORTS, not implementations
        self.payments = payments

    async def process_order(self, order_id: str) -> bool:
        order = await self.orders.find(order_id)
        if order.total > 1000:
            # Business rule: require approval for large orders
            return False
        await self.payments.charge(order.total)
        return True
```

**Key insight:** The `OrderService` logic is identical whether running against a real database or an in-memory fake. Only its *dependencies* change.

### Use @adapter.for_() for External Integrations

Implementations that talk to databases, APIs, filesystems, or need different behavior per profile.

```python
from typing import Protocol
from dioxide import adapter, Profile

# First, define the Port (interface)
class OrderRepository(Protocol):
    async def find(self, order_id: str) -> Order: ...
    async def save(self, order: Order) -> None: ...

# Production adapter - real database
@adapter.for_(OrderRepository, profile=Profile.PRODUCTION)
class PostgresOrderRepository:
    def __init__(self, db: Database):
        self.db = db

    async def find(self, order_id: str) -> Order:
        # Real SQL query
        ...

# Test adapter - fast fake
@adapter.for_(OrderRepository, profile=Profile.TEST)
class FakeOrderRepository:
    def __init__(self):
        self.orders = {}

    async def find(self, order_id: str) -> Order:
        return self.orders.get(order_id)

    def seed(self, *orders: Order) -> None:
        """Test helper to populate data."""
        for order in orders:
            self.orders[order.id] = order
```

## Common Patterns

### Pattern: Configuration as @service

Configuration classes ARE services - they don't need profile switching because you control config via environment variables.

```python
from pydantic_settings import BaseSettings
from dioxide import service

@service
class AppConfig(BaseSettings):
    """Configuration is a service, not an adapter."""
    database_url: str = "sqlite:///dev.db"
    stripe_api_key: str = ""
```

### Pattern: Adapter Depends on @service

Adapters can depend on services (like config) to get their settings.

```python
@adapter.for_(PaymentGateway, profile=Profile.PRODUCTION)
class StripeAdapter:
    def __init__(self, config: AppConfig):  # Depends on config service
        self.api_key = config.stripe_api_key
```

### Pattern: Adapter for Multiple Profiles

Use a list when the same implementation works for multiple profiles.

```python
@adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
class InMemoryCache:
    """Simple cache for both test and dev."""
    def __init__(self):
        self._cache = {}
```

## The Mental Model

```
          @service                    Port                   @adapter
    ┌─────────────────┐          ┌───────────┐         ┌─────────────────┐
    │                 │          │           │         │                 │
    │  Business       │─depends→ │ Protocol  │←implements│  Real DB       │
    │  Logic          │          │           │         │  Real Email     │
    │                 │          │           │         │  Real Payment   │
    └─────────────────┘          └───────────┘         └─────────────────┘
          ↑                            ↑                       ↑
    Same in all profiles       No decorator!         Profile-specific
```

**Services** contain business rules and depend on **Ports** (Protocols). **Adapters** implement those ports for specific environments.

## Anti-Patterns to Avoid

### Wrong: Service with Infrastructure

```python
# BAD - service contains infrastructure
@service
class UserService:
    async def register(self, email: str) -> None:
        conn = psycopg2.connect("dbname=prod")  # Infrastructure leak!
        sendgrid.send(to=email, subject="Welcome!")  # More leakage!
```

**Fix:** Depend on ports, not implementations.

### Wrong: Adapter with Business Logic

```python
# BAD - adapter contains business rules
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        if "@" not in to:  # Business rule in adapter!
            raise ValueError("Invalid email")
        # ... send email
```

**Fix:** Move validation to the service layer.

## Still Not Sure?

Ask these questions:

1. **Would I want a different implementation in tests?**
   - Yes → `@adapter.for_(Port, profile=Profile.TEST)` for the test version
   - No → Probably `@service`

2. **Does this code make network calls, touch files, or use a database?**
   - Yes → `@adapter.for_()` with a Port
   - No → `@service`

3. **Is this pure business logic with no side effects?**
   - Yes → `@service`
   - No → Consider whether it should be split

## Next Steps

- {doc}`/user_guide/services-vs-adapters` - Deep dive with more examples
- {doc}`/user_guide/hexagonal_architecture` - Full architectural context
- {doc}`/user_guide/testing_with_fakes` - Testing patterns with profile-based fakes
