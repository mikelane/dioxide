# Architecture Diagrams

This page provides visual explanations of dioxide's hexagonal architecture patterns.
These diagrams illustrate how dioxide enables clean architecture through ports, adapters,
profiles, and lifecycle management.

## The Golden Path

Before diving into detailed diagrams, here's the core mental model in one picture:

```{image} ../_static/images/diagrams/golden-path.svg
:alt: The Golden Path - Service depends on Port, implemented by Adapters
:align: center
:class: diagram
```

This is the Dependency Inversion Principle in action: your business logic (`@service`) depends
on abstractions (Ports/Protocols), not concrete implementations. Adapters implement those ports
for different environments. At runtime, dioxide wires the correct adapter based on the active
profile - your service code never changes, only the adapters do.

---

## Hexagonal Architecture Overview

The hexagonal architecture (also known as ports-and-adapters) places your core business logic
at the center, surrounded by ports that define interfaces, with adapters plugging into those
ports from the outside. This creates natural seams for testing and implementation swapping.

```{image} ../_static/images/diagrams/user_guide-architecture-0-core-domain-service-.svg
:alt: Core Domain (@service)
:align: center
:class: diagram
```

**Key Concepts:**

- **Core Domain (center)**: Business logic in `@service` classes that depend only on ports
- **Ports Layer**: Python `Protocol` classes defining interfaces (no decorators needed)
- **Adapters Layer**: Concrete implementations with `@adapter.for_(Port, profile=...)` decorators
- **External Systems**: Real databases, APIs, and services that production adapters connect to

The core domain never knows which adapter is active - it only sees the port interface.
This enables testing with fast fakes and easy implementation swapping.

---

## Profile-Based Adapter Selection

dioxide uses profiles to determine which adapter implementation is active for each port.
When you scan with a specific profile, only adapters matching that profile are activated.

```{image} ../_static/images/diagrams/user_guide-architecture-1-adapter-registration.svg
:alt: Adapter Registration (Decoration Time)
:align: center
:class: diagram
```

**How Profile Selection Works:**

1. **Registration**: When Python loads your modules, `@adapter.for_()` decorators register
   each adapter class in a global registry, associated with its port and profile(s)

2. **Scanning**: When you create a container with `Container(profile=...)`, the container automatically:
   - Discovers all registered adapters
   - Filters to only those matching the active profile
   - Registers them as providers for their respective ports

3. **Resolution**: When you call `container.resolve(Port)`, the container returns
   the adapter instance registered for that port in the current profile

**Multiple Profiles**: An adapter can be registered for multiple profiles:

```python
@adapter.for_(EmailPort, profile=[Profile.TEST, Profile.DEVELOPMENT])
class SimpleEmailAdapter:
    """Available in both TEST and DEVELOPMENT profiles."""
    pass
```

---

## Dependency Resolution Flow

When you call `container.resolve(UserService)`, dioxide performs dependency resolution
by inspecting constructor type hints and recursively resolving dependencies.

```{image} ../_static/images/diagrams/user_guide-architecture-2-sequence.svg
:alt: Sequence diagram
:align: center
:class: diagram
```

**Resolution Steps:**

1. **Lookup Provider**: Container finds the registered provider for the requested type

2. **Inspect Dependencies**: Container reads `__init__` type hints to discover dependencies

3. **Recursive Resolution**: Each dependency is resolved recursively (depth-first)

4. **Singleton Caching**: By default, instances are cached (singleton scope):
   - First resolution creates the instance
   - Subsequent resolutions return the cached instance

5. **Dependency Injection**: Constructor is called with all resolved dependencies

**Circular Dependency Detection**: If A depends on B and B depends on A, dioxide
detects this at `scan()` time and raises a clear error before any resolution occurs.

---

## Lifecycle Initialization Order

When using `@lifecycle` decorated components, dioxide initializes them in dependency order
and disposes them in reverse order. This ensures dependencies are ready before dependents
and cleaned up after dependents.

```{image} ../_static/images/diagrams/user_guide-architecture-3-sequence.svg
:alt: Sequence diagram
:align: center
:class: diagram
```

**Lifecycle Management:**

1. **Topological Sort**: Container builds a dependency graph and sorts components
   so that dependencies come before dependents (using Kahn's algorithm)

2. **Initialization**: Components are initialized in dependency order:
   - `AppConfig` first (no dependencies)
   - `Database` second (depends on AppConfig)
   - `CacheService` third (depends on AppConfig)
   - `UserService` last (depends on Database and CacheService)

3. **Disposal**: Components are disposed in **reverse** dependency order:
   - `UserService` first (so it can still use Database/Cache during cleanup)
   - `CacheService` and `Database` next
   - `AppConfig` last

**Usage with Context Manager:**

```python
from dioxide import Container, Profile

async with Container(profile=Profile.PRODUCTION) as container:
    # All @lifecycle components are initialized here
    service = container.resolve(UserService)
    await service.do_something()
# All @lifecycle components are disposed here (reverse order)
```

The `Container(profile=...)` constructor accepts both `Profile` enum values and string profiles,
and automatically triggers scanning when created.

---

## Testing with Fakes

dioxide's architecture enables testing with fast, deterministic fakes instead of mocks.
The profile system makes swapping between production and test implementations trivial.

```{image} ../_static/images/diagrams/user_guide-architecture-4-production-environme.svg
:alt: Production Environment
:align: center
:class: diagram
```

**Testing Philosophy:**

1. **Same Service Code**: `UserService` is identical in production and test - only adapters differ

2. **Fast Fakes**: Test adapters are simple in-memory implementations:
   - `FakeUserRepository`: Dict-based storage with `seed()` helper
   - `FakeEmailAdapter`: Captures sent emails in a list for verification
   - `FakeClock`: Controllable time for testing time-dependent logic

3. **No Mocking**: Instead of `@patch` and `Mock()`, use real fake implementations:
   - Fakes run actual code paths
   - No brittle mock configurations
   - Tests verify behavior, not implementation

4. **Natural Verification**: Check fake state directly:
   ```python
   # Instead of: mock_email.send.assert_called_once_with(...)
   assert len(fake_email.sent_emails) == 1
   assert fake_email.sent_emails[0]["to"] == "alice@example.com"
   ```

**Test Fixture Pattern:**

```python
import pytest
from dioxide import Container, Profile

@pytest.fixture
def container():
    """Fresh container with test fakes for each test."""
    return Container(profile=Profile.TEST)

@pytest.fixture
def fake_email(container):
    """Get the fake email adapter."""
    return container.resolve(EmailPort)

@pytest.fixture
def fake_users(container):
    """Get the fake user repository."""
    return container.resolve(UserRepository)

async def test_welcome_email_sent(container, fake_email, fake_users):
    """Sends welcome email when user registers."""
    # Arrange
    fake_users.seed(User(id=1, email="alice@example.com", name="Alice"))

    # Act
    service = container.resolve(UserService)
    await service.send_welcome_email(user_id=1)

    # Assert
    assert fake_email.verify_sent_to("alice@example.com")
    assert "Welcome" in fake_email.sent_emails[0]["subject"]
```

---

## Summary

These diagrams illustrate dioxide's core architectural patterns:

| Pattern | Purpose | Key Benefit |
|---------|---------|-------------|
| **Hexagonal Architecture** | Separate core logic from external systems | Testability and flexibility |
| **Profile-Based Adapters** | Different implementations per environment | Easy environment configuration |
| **Dependency Resolution** | Automatic constructor injection | Zero-ceremony DI |
| **Lifecycle Management** | Ordered initialization and cleanup | Resource safety |
| **Testing with Fakes** | Fast, deterministic test doubles | No mocking frameworks needed |

For more details:
- [Hexagonal Architecture Guide](hexagonal_architecture.md) - Detailed patterns and examples
- [Testing with Fakes](testing_with_fakes.rst) - Comprehensive testing philosophy
- [API Reference](../api/dioxide/index.rst) - Full API documentation
