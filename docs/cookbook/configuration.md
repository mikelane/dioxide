# Configuration

Recipes for managing configuration with Pydantic Settings and dioxide.

---

## Recipe: Pydantic Settings Adapter

### Problem

You want type-safe configuration with validation, environment variable loading, and IDE support.

### Solution

Use Pydantic Settings as a service that other components can depend on.

### Code

```python
"""Pydantic Settings as a dioxide service."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class AppConfig(BaseSettings):
    """Application configuration with validation.

    Pydantic automatically loads from:
    1. Environment variables
    2. .env file (if python-dotenv installed)
    3. Default values

    As a @service, this is a singleton - same instance everywhere.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="sqlite:///./dev.db",
        description="Database connection URL",
    )

    # Email
    sendgrid_api_key: str = Field(
        default="",
        description="SendGrid API key for production email",
    )
    email_from: str = Field(
        default="noreply@example.com",
        description="Default sender email address",
    )

    # Application
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )


# Other services can depend on AppConfig
from dioxide import adapter, Profile


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: AppConfig) -> None:
        # AppConfig is injected automatically
        self.connection_url = config.database_url

    async def connect(self) -> None:
        # Use self.connection_url
        pass


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.sendgrid_api_key
        self.from_email = config.email_from

    async def send(self, to: str, subject: str, body: str) -> None:
        # Use self.api_key
        pass
```

### Explanation

1. **@service decorator**: Makes config a singleton, injectable into other components
2. **Pydantic validation**: Type coercion and validation on startup
3. **Environment loading**: Automatic loading from env vars and .env files
4. **IDE support**: Full autocomplete for config attributes
5. **Constructor injection**: Adapters receive config automatically

---

## Recipe: Profile-Based Configuration

### Problem

You need different configuration values for production, development, and testing.

### Solution

Create a ConfigPort protocol with profile-specific adapters.

### Code

```python
"""Profile-based configuration with adapters."""
import os
from typing import Protocol

from dioxide import Profile, adapter, service


class ConfigPort(Protocol):
    """Configuration port - defines what config methods are available."""

    def get(self, key: str, default: str = "") -> str:
        """Get a configuration value."""
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        ...


@adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
class EnvConfigAdapter:
    """Production config from environment variables."""

    def get(self, key: str, default: str = "") -> str:
        return os.environ.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        value = os.environ.get(key)
        return int(value) if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = os.environ.get(key, "").lower()
        if value in ("true", "1", "yes"):
            return True
        if value in ("false", "0", "no"):
            return False
        return default


@adapter.for_(ConfigPort, profile=Profile.TEST)
class FakeConfigAdapter:
    """Test config with in-memory values."""

    def __init__(self):
        self.values: dict[str, str] = {
            "DATABASE_URL": "sqlite:///:memory:",
            "SENDGRID_API_KEY": "test-key",
            "DEBUG": "true",
        }

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.values.get(key)
        return int(value) if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.values.get(key, "").lower()
        if value in ("true", "1", "yes"):
            return True
        if value in ("false", "0", "no"):
            return False
        return default

    # Test helper
    def set(self, key: str, value: str) -> None:
        """Set config value for testing."""
        self.values[key] = value


@adapter.for_(ConfigPort, profile=Profile.DEVELOPMENT)
class DevConfigAdapter:
    """Development config with sensible defaults."""

    def __init__(self):
        self.defaults = {
            "DATABASE_URL": "sqlite:///./dev.db",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
        }

    def get(self, key: str, default: str = "") -> str:
        # Check env first, then defaults
        return os.environ.get(key, self.defaults.get(key, default))

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.get(key)
        return int(value) if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key).lower()
        if value in ("true", "1", "yes"):
            return True
        if value in ("false", "0", "no"):
            return False
        return default


# Usage - adapters inject ConfigPort
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: ConfigPort) -> None:
        self.url = config.get("DATABASE_URL")
```

### Explanation

1. **ConfigPort protocol**: Defines the configuration interface
2. **Profile-specific adapters**: Different config sources per environment
3. **Production**: Reads from real environment variables
4. **Test**: In-memory values you can control
5. **Development**: Defaults with environment override

---

## Recipe: Secrets from Environment

### Problem

You need to handle sensitive configuration (API keys, passwords) securely.

### Solution

Use Pydantic's SecretStr type and validation.

### Code

```python
"""Secure secrets handling with Pydantic."""
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class SecureConfig(BaseSettings):
    """Configuration with secure secret handling."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Secrets - never logged or displayed
    database_password: SecretStr = Field(
        default=SecretStr(""),
        description="Database password",
    )
    sendgrid_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="SendGrid API key",
    )
    jwt_secret: SecretStr = Field(
        default=SecretStr(""),
        description="JWT signing secret",
    )

    # Non-secret config
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "myapp"

    @property
    def database_url(self) -> str:
        """Build database URL with secret password."""
        password = self.database_password.get_secret_value()
        return (
            f"postgresql://user:{password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, v: SecretStr) -> SecretStr:
        """Validate JWT secret is set in production."""
        import os
        if os.getenv("PROFILE") == "production":
            if not v.get_secret_value():
                raise ValueError("JWT_SECRET must be set in production")
        return v


# Using secrets in adapters
from dioxide import adapter, Profile


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: SecureConfig) -> None:
        # get_secret_value() returns the actual string
        self.url = config.database_url  # Password embedded securely


@adapter.for_(AuthPort, profile=Profile.PRODUCTION)
class JWTAuthAdapter:
    def __init__(self, config: SecureConfig) -> None:
        # Extract secret value only when needed
        self.secret = config.jwt_secret.get_secret_value()

    def sign_token(self, payload: dict) -> str:
        import jwt
        return jwt.encode(payload, self.secret, algorithm="HS256")
```

### Explanation

1. **SecretStr type**: Prevents accidental logging of secrets
2. **get_secret_value()**: Explicit extraction of secret value
3. **Validation**: Can validate secrets are set in production
4. **Properties**: Build complex values (URLs) from parts

---

## Recipe: Startup Validation

### Problem

You want to fail fast if required configuration is missing.

### Solution

Use Pydantic validators to check config at container scan time.

### Code

```python
"""Fail-fast configuration validation."""
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class ValidatedConfig(BaseSettings):
    """Configuration that validates on startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Required in production
    database_url: str = Field(default="")
    sendgrid_api_key: str = Field(default="")

    # Optional with defaults
    redis_url: str = Field(default="redis://localhost:6379")
    log_level: str = Field(default="INFO")

    # Profile (set from environment)
    profile: str = Field(default="development")

    @model_validator(mode="after")
    def validate_production_config(self) -> Self:
        """Validate required config is set in production."""
        if self.profile == "production":
            missing = []

            if not self.database_url:
                missing.append("DATABASE_URL")
            if not self.sendgrid_api_key:
                missing.append("SENDGRID_API_KEY")

            if missing:
                raise ValueError(
                    f"Missing required production config: {', '.join(missing)}"
                )

        return self


# Usage in application startup
from dioxide import Container, Profile

def create_app():
    """Create application with validated config."""
    try:
        # Container creation triggers validation
        container = Container(profile=Profile.PRODUCTION)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please set required environment variables")
        raise SystemExit(1)

    return container


# Test that validation works
import pytest
import os


class DescribeConfigValidation:
    """Tests for configuration validation."""

    def it_fails_without_database_url_in_production(self, monkeypatch):
        """Raises error when DATABASE_URL missing in production."""
        monkeypatch.setenv("PROFILE", "production")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValueError) as exc_info:
            ValidatedConfig()

        assert "DATABASE_URL" in str(exc_info.value)

    def it_allows_missing_config_in_development(self, monkeypatch):
        """Development profile allows missing config."""
        monkeypatch.setenv("PROFILE", "development")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        config = ValidatedConfig()  # Should not raise

        assert config.profile == "development"
```

### Explanation

1. **model_validator**: Runs after all fields are parsed
2. **Profile check**: Only validate required fields in production
3. **Clear errors**: List all missing config at once
4. **Fail fast**: App won't start with invalid config

---

## Recipe: Config with Aliases

### Problem

You want to support both legacy and new environment variable names.

### Solution

Use Pydantic's alias and validation_alias features.

### Code

```python
"""Configuration with aliases for backward compatibility."""
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


@service
class CompatibleConfig(BaseSettings):
    """Config supporting legacy env var names."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        # Try these prefixes when looking for env vars
        env_prefix="",
    )

    # Supports both DATABASE_URL and DB_URL
    database_url: str = Field(
        default="sqlite:///./dev.db",
        validation_alias=AliasChoices("DATABASE_URL", "DB_URL"),
    )

    # Supports SENDGRID_API_KEY, SG_API_KEY, and EMAIL_API_KEY
    email_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SENDGRID_API_KEY",
            "SG_API_KEY",
            "EMAIL_API_KEY",
        ),
    )

    # Supports LOG_LEVEL and LOGGING_LEVEL
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "LOGGING_LEVEL"),
    )

    # Port with common variations
    server_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "SERVER_PORT", "HTTP_PORT"),
    )


# Test that aliases work
def test_database_url_alias():
    """DATABASE_URL alias works."""
    import os

    os.environ["DB_URL"] = "postgresql://localhost/test"
    config = CompatibleConfig()
    assert config.database_url == "postgresql://localhost/test"
    del os.environ["DB_URL"]
```

### Explanation

1. **AliasChoices**: Try multiple env var names in order
2. **Backward compatibility**: Support old names without breaking existing deployments
3. **Migration path**: Document preferred names, support legacy ones
4. **Priority**: First match wins

---

## Recipe: Nested Configuration

### Problem

You have complex configuration with nested sections.

### Solution

Use nested Pydantic models for organized config.

### Code

```python
"""Nested configuration with Pydantic models."""
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dioxide import service


class DatabaseConfig(BaseModel):
    """Database configuration section."""

    host: str = "localhost"
    port: int = 5432
    name: str = "myapp"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 5
    pool_timeout: int = 30

    @property
    def url(self) -> str:
        """Build connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}"
        )


class EmailConfig(BaseModel):
    """Email configuration section."""

    provider: str = "sendgrid"
    api_key: str = ""
    from_address: str = "noreply@example.com"
    from_name: str = "My App"


class CacheConfig(BaseModel):
    """Cache configuration section."""

    enabled: bool = True
    backend: str = "redis"
    url: str = "redis://localhost:6379"
    ttl_seconds: int = 3600


@service
class AppConfig(BaseSettings):
    """Application configuration with nested sections."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",  # DATABASE__HOST -> database.host
        extra="ignore",
    )

    # Nested configuration sections
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # Top-level config
    debug: bool = False
    log_level: str = "INFO"


# Environment variables work with nested delimiter:
# DATABASE__HOST=db.example.com
# DATABASE__PORT=5432
# EMAIL__API_KEY=SG.xxx
# CACHE__TTL_SECONDS=7200


# Usage in adapters
from dioxide import adapter, Profile


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
class PostgresAdapter:
    def __init__(self, config: AppConfig) -> None:
        # Access nested config
        self.url = config.database.url
        self.pool_size = config.database.pool_size


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.email.api_key
        self.from_email = config.email.from_address
```

### Explanation

1. **Nested models**: Organize related config into sections
2. **env_nested_delimiter**: `DATABASE__HOST` maps to `database.host`
3. **default_factory**: Create fresh nested models
4. **Properties**: Compute derived values from parts

---

## See Also

- [FastAPI Integration](fastapi.md) - Using config in FastAPI apps
- [Database Patterns](database.md) - Database connection config
- [Testing Patterns](testing.md) - Testing with fake config
