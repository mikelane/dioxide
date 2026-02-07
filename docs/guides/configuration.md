# Configuration Injection

This guide covers how to inject configuration into your dioxide application, why it matters for testability, and patterns for managing configuration across environments.

## Why Inject Configuration?

Most Python applications access configuration through hidden calls scattered throughout the codebase:

```python
# Hidden dependency - hard to test, hard to trace
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        api_key = os.environ["SENDGRID_API_KEY"]  # Hidden!
        from_addr = os.environ["EMAIL_FROM"]       # Hidden!
        # ...
```

This creates problems:

| Hidden Configuration | Explicit Injection |
|---------------------|--------------------|
| `os.environ["KEY"]` scattered everywhere | Config declared once, injected everywhere |
| Tests must manipulate `os.environ` | Tests pass config directly |
| Missing config crashes at runtime | Missing config caught at startup |
| No IDE autocomplete for config keys | Full autocomplete on config attributes |
| Typos in key strings fail silently | Typos caught by type checker |

The fix: treat configuration as a dependency and inject it through the container.

## Quick Start

The simplest approach: define a config class with `@service` and inject it into adapters.

```python
from pydantic_settings import BaseSettings
from dioxide import adapter, service, Container, Profile

@service
class AppConfig(BaseSettings):
    database_url: str = "sqlite:///dev.db"
    sendgrid_api_key: str = ""
    debug: bool = False

@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.url = config.database_url

# Container auto-discovers and injects AppConfig
container = Container(profile=Profile.PRODUCTION)
db = container.resolve(DatabasePort)
```

That is the entire pattern. The `@service` decorator registers `AppConfig` as a singleton, and any component that type-hints `AppConfig` in its constructor receives the same instance.

## Pattern 1: Pydantic Settings with Environment Variables

[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) provides type-safe configuration with automatic environment variable loading, validation, and IDE support.

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="sqlite:///dev.db",
        description="Database connection URL",
    )

    # Email
    sendgrid_api_key: str = Field(
        default="",
        description="SendGrid API key",
    )
    email_from: str = Field(
        default="noreply@example.com",
        description="Default sender email",
    )

    # Application
    debug: bool = False
    log_level: str = "INFO"
```

Pydantic loads values from environment variables automatically. Set `DATABASE_URL=postgresql://...` in your environment or `.env` file and the config picks it up.

### Injecting Config into Adapters

```python
from dioxide import adapter, Profile


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.sendgrid_api_key
        self.from_email = config.email_from

    async def send(self, to: str, subject: str, body: str) -> None:
        # Use self.api_key to authenticate with SendGrid
        ...


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.connection_url = config.database_url

    async def connect(self) -> None:
        # Use self.connection_url to connect
        ...
```

Both adapters receive the same `AppConfig` singleton instance, configured from the environment.

## Pattern 2: Multiple Config Classes

Large applications benefit from splitting configuration into focused classes. Each config class handles one concern.

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 5

    @property
    def url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


@service
class EmailConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMAIL_")

    provider: str = "sendgrid"
    api_key: str = ""
    from_address: str = "noreply@example.com"


@service
class FeatureFlags(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FEATURE_")

    new_checkout: bool = False
    dark_mode: bool = False
    beta_api: bool = False
```

Each class reads from prefixed environment variables: `DB_HOST`, `DB_PORT`, `EMAIL_API_KEY`, `FEATURE_NEW_CHECKOUT`, and so on.

### Injecting Specific Config

Adapters depend only on the config they need:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: DatabaseConfig) -> None:
        self.url = config.url
        self.pool_size = config.pool_size


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: EmailConfig) -> None:
        self.api_key = config.api_key


@service
class CheckoutService:
    def __init__(self, features: FeatureFlags, orders: OrderPort) -> None:
        self.features = features
        self.orders = orders

    async def process(self, order_id: str) -> None:
        if self.features.new_checkout:
            # New checkout flow
            ...
        else:
            # Legacy checkout flow
            ...
```

This keeps each component's dependencies narrow and explicit.

## Pattern 3: Testing with Config Overrides

Because configuration is injected through the container, testing with different config values requires no environment variable manipulation.

### Using `register_instance()`

Create a config object with test values and register it before scanning:

```python
import pytest
from dioxide import Container, Profile


@pytest.fixture
def container() -> Container:
    container = Container()

    test_config = AppConfig(
        database_url="sqlite:///:memory:",
        sendgrid_api_key="test-key-123",
        debug=True,
    )
    container.register_instance(AppConfig, test_config)

    container.scan(profile=Profile.TEST)
    return container


def it_uses_test_database_url(container: Container) -> None:
    db = container.resolve(DatabasePort)
    assert db.connection_url == "sqlite:///:memory:"
```

The `register_instance()` method registers a pre-created object that the container returns whenever `AppConfig` is resolved. Because the instance is registered before scanning, all adapters receive the test config.

### Using `register_instance()` with Multiple Config Classes

```python
@pytest.fixture
def container() -> Container:
    container = Container()

    container.register_instance(
        DatabaseConfig,
        DatabaseConfig(host="localhost", name="test_db", pool_size=1),
    )
    container.register_instance(
        EmailConfig,
        EmailConfig(api_key="test-key", from_address="test@example.com"),
    )
    container.register_instance(
        FeatureFlags,
        FeatureFlags(new_checkout=True, dark_mode=False),
    )

    container.scan(profile=Profile.TEST)
    return container
```

Each config class is overridden independently. This lets tests exercise specific feature flag combinations without touching the environment.

## Pattern 4: Environment-Specific Configuration

Use environment variables to control which values are active. The same `@service` config class works across all environments because Pydantic loads values from the environment at instantiation time.

### Development

```bash
# .env file for local development
DATABASE_URL=sqlite:///dev.db
DEBUG=true
LOG_LEVEL=DEBUG
SENDGRID_API_KEY=""
```

### Production

```bash
# Set in production environment (Docker, Kubernetes, etc.)
DATABASE_URL=postgresql://user:pass@db.example.com:5432/myapp
DEBUG=false
LOG_LEVEL=WARNING
SENDGRID_API_KEY=SG.actual-production-key
```

### CI

```bash
# Set in CI environment
DATABASE_URL=sqlite:///:memory:
DEBUG=false
LOG_LEVEL=ERROR
SENDGRID_API_KEY=test-key
```

The application code stays identical. Only the environment changes.

```python
# Same code runs everywhere
container = Container(profile=Profile.PRODUCTION)
service = container.resolve(UserService)
```

## API Reference: `container.register_instance()`

```python
container.register_instance(component_type: type[T], instance: T) -> None
```

Registers a pre-created instance that the container returns whenever `component_type` is resolved.

**Parameters:**

- `component_type` -- The type to register as the lookup key.
- `instance` -- The pre-created object to return for this type.

**Raises:**

- `TypeError` -- If `instance` is not an instance of `component_type` (or structurally compatible for Protocol types).
- `KeyError` -- If `component_type` is already registered. Each type can only be registered once per container.

**Type safety:**

```python
container = Container()

# Valid - Config is an instance of Config
config = AppConfig(debug=True)
container.register_instance(AppConfig, config)

# Invalid - raises TypeError at registration time
container.register_instance(str, 42)
# TypeError: instance must be of type 'str', got 'int'
```

**Resolution:**

```python
container.register_instance(AppConfig, config)
resolved = container.resolve(AppConfig)
assert resolved is config  # Same object, not a copy
```

Registered instances behave as singletons. The container returns the exact object you registered.

## Common Mistakes

### Mistake: Hidden `Settings()` Calls

```python
# BAD - config created inside the adapter, invisible to the container
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self) -> None:
        config = AppConfig()  # Hidden dependency!
        self.api_key = config.sendgrid_api_key
```

This defeats dependency injection. The adapter creates its own config, making it impossible to override in tests without manipulating environment variables.

```python
# GOOD - config injected by the container
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.sendgrid_api_key
```

### Mistake: Using `os.environ` Directly

```python
# BAD - scattered env var access
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self) -> None:
        self.url = os.environ["DATABASE_URL"]      # Crashes if missing
        self.pool = int(os.environ.get("POOL", 5))  # No validation
```

This spreads configuration access across the codebase and loses all the benefits of centralized config: validation, defaults, type safety, and testability.

```python
# GOOD - centralized config with validation
@service
class DatabaseConfig(BaseSettings):
    url: str = "sqlite:///dev.db"
    pool_size: int = 5

@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: DatabaseConfig) -> None:
        self.url = config.url
        self.pool_size = config.pool_size
```

### Mistake: Config as an Adapter

Configuration does not need profile switching because you control config values through environment variables. Making config an adapter adds unnecessary complexity.

```python
# UNNECESSARY - config doesn't need profile switching
@adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
class ProdConfig:
    database_url = "postgresql://..."

@adapter.for_(ConfigPort, profile=Profile.TEST)
class TestConfig:
    database_url = "sqlite:///:memory:"
```

```python
# SIMPLER - one config class, environment controls values
@service
class AppConfig(BaseSettings):
    database_url: str = "sqlite:///dev.db"

# In production: DATABASE_URL=postgresql://...
# In tests: use register_instance() with test values
```

The `@service` approach is simpler and more flexible. You set environment variables for production and use `register_instance()` for tests.

## Startup Validation

Pydantic validators catch missing or invalid configuration at container creation time, before your application starts serving requests.

```python
from typing import Self
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    sendgrid_api_key: str = ""

    @model_validator(mode="after")
    def check_required_fields(self) -> Self:
        missing = []
        if not self.database_url:
            missing.append("DATABASE_URL")
        if not self.sendgrid_api_key:
            missing.append("SENDGRID_API_KEY")
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}"
            )
        return self
```

When the container scans and creates the `AppConfig` singleton, Pydantic runs the validator. If required fields are missing, the application fails immediately with a clear error message rather than crashing later when an adapter tries to use an empty API key.

## Putting It All Together

Here is a complete application showing configuration injection from end to end.

```python
from typing import Protocol

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import Container, Profile, adapter, service


# --- Configuration ---

@service
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///dev.db"
    sendgrid_api_key: str = ""
    email_from: str = "noreply@example.com"
    debug: bool = False


# --- Ports ---

class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

class UserRepository(Protocol):
    async def save(self, user: dict) -> None: ...
    async def find_by_email(self, email: str) -> dict | None: ...


# --- Production adapters ---

@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.sendgrid_api_key
        self.from_email = config.email_from

    async def send(self, to: str, subject: str, body: str) -> None:
        # Use self.api_key to call SendGrid API
        ...


# --- Test adapters ---

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})


# --- Service ---

@service
class UserService:
    def __init__(self, email: EmailPort, users: UserRepository) -> None:
        self.email = email
        self.users = users

    async def register(self, name: str, email_addr: str) -> None:
        await self.users.save({"name": name, "email": email_addr})
        await self.email.send(email_addr, "Welcome!", f"Hello {name}!")


# --- Production usage ---

container = Container(profile=Profile.PRODUCTION)
user_service = container.resolve(UserService)


# --- Test usage ---

def test_registration() -> None:
    container = Container()

    test_config = AppConfig(
        database_url="sqlite:///:memory:",
        sendgrid_api_key="test-key",
    )
    container.register_instance(AppConfig, test_config)
    container.scan(profile=Profile.TEST)

    user_service = container.resolve(UserService)
    email = container.resolve(EmailPort)

    # Run the registration flow, then verify
    # email.sent_emails contains the welcome email
```

## Next Steps

- {doc}`/cookbook/configuration` -- Copy-paste recipes for secrets, nested config, aliases, and validation
- {doc}`/guides/choosing-decorators` -- When to use `@service` vs `@adapter.for_()`
- {doc}`/testing/writing-fakes` -- Writing test fakes for adapters
- {doc}`/user_guide/container_patterns` -- Container patterns (global vs instance)
