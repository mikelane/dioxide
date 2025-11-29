# Architecture Diagrams

This page provides visual explanations of dioxide's hexagonal architecture patterns through
comprehensive Mermaid diagrams. These diagrams illustrate how dioxide enables clean
architecture through ports, adapters, profiles, and lifecycle management.

## Hexagonal Architecture Overview

The hexagonal architecture (also known as ports-and-adapters) places your core business logic
at the center, surrounded by ports that define interfaces, with adapters plugging into those
ports from the outside. This creates natural seams for testing and implementation swapping.

```{mermaid}
flowchart TB
    subgraph EXTERNAL["External Systems"]
        direction TB
        DB[(PostgreSQL)]
        API[SendGrid API]
        FS[File System]
        CACHE[(Redis)]
    end

    subgraph ADAPTERS["Adapters Layer"]
        direction TB
        subgraph PROD_ADAPTERS["Production Adapters"]
            PGA[PostgresUserRepository]
            SGA[SendGridEmailAdapter]
            FSA[S3StorageAdapter]
            RCA[RedisCacheAdapter]
        end
        subgraph TEST_ADAPTERS["Test Adapters"]
            FUR[FakeUserRepository]
            FEA[FakeEmailAdapter]
            FFS[FakeStorageAdapter]
            FCA[FakeCacheAdapter]
        end
    end

    subgraph PORTS["Ports Layer"]
        direction TB
        UP{{UserRepository}}
        EP{{EmailPort}}
        SP{{StoragePort}}
        CP{{CachePort}}
    end

    subgraph CORE["Core Domain"]
        direction TB
        US[UserService]
        NS[NotificationService]
        OS[OrderService]
    end

    %% External to Production Adapters
    DB --- PGA
    API --- SGA
    FS --- FSA
    CACHE --- RCA

    %% Production Adapters to Ports
    PGA --> UP
    SGA --> EP
    FSA --> SP
    RCA --> CP

    %% Test Adapters to Ports
    FUR --> UP
    FEA --> EP
    FFS --> SP
    FCA --> CP

    %% Core depends on Ports
    US --> UP
    US --> EP
    NS --> EP
    NS --> UP
    OS --> UP
    OS --> SP
    OS --> CP
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

```{mermaid}
flowchart TB
    subgraph REGISTRATION["Adapter Registration (Decoration Time)"]
        direction LR
        A1["@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter"]
        A2["@adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter"]
        A3["@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
        class ConsoleEmailAdapter"]
    end

    subgraph REGISTRY["Global Registry"]
        direction TB
        REG[("Adapter Registry
        EmailPort:
          - PRODUCTION: SendGridAdapter
          - TEST: FakeEmailAdapter
          - DEVELOPMENT: ConsoleEmailAdapter")]
    end

    subgraph SCANNING["Container Creation (Auto-Scans)"]
        direction TB
        SCAN_PROD["Container(profile=Profile.PRODUCTION)"]
        SCAN_TEST["Container(profile=Profile.TEST)"]
        SCAN_DEV["Container(profile=Profile.DEVELOPMENT)"]
    end

    subgraph ACTIVATION["Active Adapters"]
        direction TB
        ACT_PROD["EmailPort -> SendGridAdapter"]
        ACT_TEST["EmailPort -> FakeEmailAdapter"]
        ACT_DEV["EmailPort -> ConsoleEmailAdapter"]
    end

    subgraph RESOLUTION["Resolution"]
        direction TB
        RES["container.resolve(EmailPort)
        Returns active adapter for current profile"]
    end

    A1 --> REG
    A2 --> REG
    A3 --> REG

    REG --> SCAN_PROD
    REG --> SCAN_TEST
    REG --> SCAN_DEV

    SCAN_PROD --> ACT_PROD
    SCAN_TEST --> ACT_TEST
    SCAN_DEV --> ACT_DEV

    ACT_PROD --> RES
    ACT_TEST --> RES
    ACT_DEV --> RES
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

```{mermaid}
sequenceDiagram
    participant App as Application
    participant Container as Container
    participant Registry as Provider Registry
    participant Cache as Singleton Cache

    App->>Container: resolve(UserService)

    Container->>Registry: lookup(UserService)
    Registry-->>Container: ServiceProvider(UserService)

    Container->>Container: inspect __init__ type hints
    Note over Container: UserService.__init__(self, db: UserRepository, email: EmailPort)

    Container->>Container: resolve(UserRepository)
    Container->>Registry: lookup(UserRepository)
    Registry-->>Container: AdapterProvider(PostgresUserRepository)

    Container->>Cache: check cache(PostgresUserRepository)
    Cache-->>Container: not cached

    Container->>Container: create PostgresUserRepository()
    Container->>Cache: store(PostgresUserRepository, instance)
    Container-->>Container: PostgresUserRepository instance

    Container->>Container: resolve(EmailPort)
    Container->>Registry: lookup(EmailPort)
    Registry-->>Container: AdapterProvider(SendGridAdapter)

    Container->>Cache: check cache(SendGridAdapter)
    Cache-->>Container: not cached

    Container->>Container: create SendGridAdapter()
    Container->>Cache: store(SendGridAdapter, instance)
    Container-->>Container: SendGridAdapter instance

    Container->>Container: create UserService(db, email)
    Container->>Cache: store(UserService, instance)

    Container-->>App: UserService instance
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

```{mermaid}
sequenceDiagram
    participant App as Application
    participant Container as Container
    participant Graph as Dependency Graph
    participant Config as AppConfig
    participant DB as Database
    participant Cache as CacheService
    participant User as UserService

    Note over App,User: Dependency Order: AppConfig -> Database -> CacheService -> UserService

    App->>Container: async with container:

    Container->>Graph: topological_sort(lifecycle_components)
    Graph-->>Container: [AppConfig, Database, CacheService, UserService]

    rect rgb(230, 245, 230)
        Note over Container,User: Initialization Phase (dependency order)
        Container->>Config: initialize()
        Config-->>Container: ready

        Container->>DB: initialize()
        Note over DB: Connects to PostgreSQL
        DB-->>Container: ready

        Container->>Cache: initialize()
        Note over Cache: Connects to Redis
        Cache-->>Container: ready

        Container->>User: initialize()
        Note over User: All dependencies ready
        User-->>Container: ready
    end

    Container-->>App: context entered

    Note over App: Application runs...
    App->>Container: resolve(UserService)
    Container-->>App: UserService (already initialized)

    App->>Container: exit context

    rect rgb(245, 230, 230)
        Note over Container,User: Disposal Phase (reverse dependency order)
        Container->>User: dispose()
        User-->>Container: disposed

        Container->>Cache: dispose()
        Note over Cache: Disconnects from Redis
        Cache-->>Container: disposed

        Container->>DB: dispose()
        Note over DB: Closes PostgreSQL connection
        DB-->>Container: disposed

        Container->>Config: dispose()
        Config-->>Container: disposed
    end

    Container-->>App: context exited
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

```{mermaid}
flowchart TB
    subgraph PRODUCTION["Production Environment"]
        direction TB
        subgraph PROD_CONTAINER["Container(profile=PRODUCTION)"]
            PUS[UserService]
            PNS[NotificationService]
        end
        subgraph PROD_ADAPTERS["Production Adapters"]
            PPG[(PostgreSQL)]
            PSG[SendGrid API]
            PRC[(Redis)]
        end
        PUS --> PPG
        PUS --> PSG
        PNS --> PSG
        PNS --> PRC
    end

    subgraph TESTING["Test Environment"]
        direction TB
        subgraph TEST_CONTAINER["Container(profile=TEST)"]
            TUS[UserService]
            TNS[NotificationService]
        end
        subgraph TEST_FAKES["Fast Fakes (In-Memory)"]
            TFU["FakeUserRepository
            users: dict[int, User]
            + seed(*users)
            + clear()"]
            TFE["FakeEmailAdapter
            sent_emails: list[dict]
            + verify_sent_to(email)
            + clear()"]
            TFC["FakeCacheAdapter
            cache: dict[str, Any]
            + clear()"]
        end
        TUS --> TFU
        TUS --> TFE
        TNS --> TFE
        TNS --> TFC
    end

    subgraph TEST_CODE["Test Code"]
        direction TB
        ARRANGE["Arrange:
        fake_users.seed(User(id=1, email='alice@example.com'))
        fake_clock.set_time(datetime(2024, 1, 1))"]

        ACT["Act:
        result = await service.register_user('Alice', 'alice@example.com')"]

        ASSERT["Assert:
        assert result['email'] == 'alice@example.com'
        assert fake_email.verify_sent_to('alice@example.com')
        assert len(fake_email.sent_emails) == 1"]
    end

    TEST_CONTAINER --> TEST_CODE
    ARRANGE --> ACT
    ACT --> ASSERT
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
