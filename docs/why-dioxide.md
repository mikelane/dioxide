# Why dioxide?

dioxide is a dependency injection framework designed around a single philosophy: **make clean architecture the path of least resistance**.

This page provides an honest comparison with alternatives to help you choose the right tool.

---

## The Mission

> **Make the Dependency Inversion Principle feel inevitable.**

Most Python codebases suffer from tight coupling because it is the path of least resistance. Importing `sendgrid` directly into business logic is trivially easy. Defining ports, creating adapters, and wiring them together requires discipline.

dioxide exists to flip this equation. When adding a dependency is as simple as a type hint, and swapping implementations is a single profile parameter, clean architecture becomes the natural choice.

---

## The Philosophy

### 1. Clean Architecture Made Simple

dioxide's API mirrors hexagonal architecture concepts directly:

- **Ports** are Python `Protocol` classes (interfaces)
- **Adapters** implement ports with `@adapter.for_(Port, profile=...)`
- **Services** contain business logic with `@service`

Your architecture becomes visible in your code.

### 2. Type Hints Are the Contract

If mypy passes, your wiring is correct. No magic strings, no runtime surprises:

```python
@service
class UserService:
    def __init__(self, email: EmailPort):  # Type-checked!
        self.email = email
```

### 3. Profiles for Environment Switching

Different implementations for different environments. No overrides, no patching:

```python
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter: ...

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter: ...

# Production
container = Container(profile=Profile.PRODUCTION)  # Uses SendGrid

# Testing
container = Container(profile=Profile.TEST)  # Uses Fake
```

### 4. Fakes Over Mocks

Test with real implementations, not mock configurations:

```python
# Test uses real fake, not mock
async def test_notification():
    container = Container(profile=Profile.TEST)
    email = container.resolve(EmailPort)

    await container.resolve(NotificationService).notify("alice@example.com")

    assert len(email.sent_emails) == 1  # Inspect fake state
```

### 5. Fail Fast with Clear Errors

Circular dependencies and missing providers fail at startup, not at runtime:

```python
# At Container() creation time, not first request:
# CircularDependencyError: A -> B -> C -> A
```

---

## Feature Comparison

How does dioxide compare to popular Python DI frameworks?

:::{list-table} Feature Comparison Matrix
:header-rows: 1
:widths: 25 15 20 15 15

* - Feature
  - dioxide
  - dependency-injector
  - injector
  - Manual DI

* - **Profile/environment switching**
  - Built-in
  - Manual override
  - Manual
  - Manual

* - **Hexagonal architecture support**
  - Native API
  - Possible
  - Possible
  - Possible

* - **Type hint wiring**
  - Full (mypy)
  - Partial (stubs)
  - Full (mypy)
  - Full

* - **Auto-discovery**
  - Yes (scan packages)
  - No
  - No
  - N/A

* - **Async lifecycle**
  - Yes (`@lifecycle`)
  - Yes (Resources)
  - No
  - Manual

* - **Circular detection**
  - At startup
  - At runtime
  - At startup
  - N/A

* - **Performance**
  - Rust-backed
  - Cython-backed
  - Pure Python
  - N/A

* - **Learning curve**
  - Medium
  - High
  - Low
  - Low

* - **Boilerplate**
  - Low
  - High
  - Low
  - None
:::

**Notes on comparison:**

- **dependency-injector** is mature and feature-rich, written in Cython for performance. It uses an imperative provider-based API (`providers.Singleton(...)`) with explicit wiring.
- **injector** is inspired by Google Guice, with a simpler API. It uses Modules for configuration and supports full mypy typing.
- **Manual DI** means passing dependencies explicitly in constructors without a framework. Zero overhead but requires manual wiring.

---

## Code Comparison

The same use case implemented in dioxide vs dependency-injector:

### dioxide

```python
from typing import Protocol
from dioxide import adapter, service, Profile, Container

# Define port
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    def __init__(self, config: AppConfig):
        self.api_key = config.sendgrid_api_key

    async def send(self, to: str, subject: str, body: str) -> None:
        # SendGrid API call
        ...

# Test adapter
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

# Service
@service
class NotificationService:
    def __init__(self, email: EmailPort):
        self.email = email

    async def notify(self, user_email: str) -> None:
        await self.email.send(user_email, "Hello!", "Welcome!")

# Usage
container = Container(profile=Profile.PRODUCTION)
service = container.resolve(NotificationService)
```

**Lines of setup code:** ~25

### dependency-injector

```python
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide

class EmailPort:
    async def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError

class SendGridAdapter(EmailPort):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def send(self, to: str, subject: str, body: str) -> None:
        # SendGrid API call
        ...

class FakeEmailAdapter(EmailPort):
    def __init__(self):
        self.sent_emails = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})

class NotificationService:
    def __init__(self, email: EmailPort):
        self.email = email

    async def notify(self, user_email: str) -> None:
        await self.email.send(user_email, "Hello!", "Welcome!")

# Container definition
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    email_adapter = providers.Singleton(
        SendGridAdapter,
        api_key=config.sendgrid_api_key,
    )

    notification_service = providers.Singleton(
        NotificationService,
        email=email_adapter,
    )

# Usage
container = Container()
container.config.from_yaml("config.yml")
container.wire(modules=[__name__])

@inject
def get_service(service: NotificationService = Provide[Container.notification_service]):
    return service

# For testing, need to override:
container.email_adapter.override(providers.Object(FakeEmailAdapter()))
```

**Lines of setup code:** ~45

### Key Differences

| Aspect | dioxide | dependency-injector |
|--------|---------|---------------------|
| **Wiring** | Type hints only | `@inject` + `Provide[]` required |
| **Discovery** | Automatic via `Container(profile=...)` | Manual wiring required |
| **Profile switching** | Change profile parameter | Override providers manually |
| **Testing** | Use `Profile.TEST` | Use `override()` with mocks |
| **Boilerplate** | Minimal | Significant |

---

## When to Choose dioxide

### Choose dioxide when:

::::{grid} 2
:gutter: 3

:::{grid-item-card} You value minimal API surface
:class-card: sd-border-0 sd-shadow-sm

3 decorators (`@adapter.for_()`, `@service`, `@lifecycle`), 1 container class (`Container(profile=...)`). That's it.
:::

:::{grid-item-card} You want built-in environment profiles
:class-card: sd-border-0 sd-shadow-sm

Switch between production, test, and development implementations with a single parameter.
:::

:::{grid-item-card} You prefer fakes over mocks
:class-card: sd-border-0 sd-shadow-sm

dioxide's profile system naturally encourages testing with fast fakes rather than mock objects.
:::

:::{grid-item-card} Type safety matters
:class-card: sd-border-0 sd-shadow-sm

Full mypy/pyright support. If types check, wiring is correct.
:::

:::{grid-item-card} Performance is important
:class-card: sd-border-0 sd-shadow-sm

Rust-backed container provides sub-microsecond resolution, consistent under load.
:::

:::{grid-item-card} You want hexagonal architecture
:class-card: sd-border-0 sd-shadow-sm

API directly mirrors ports-and-adapters pattern. Architecture is explicit in decorators.
:::

::::

### Consider alternatives when:

::::{grid} 2
:gutter: 3

:::{grid-item-card} You need provider functions
:class-card: sd-border-0 sd-shadow-sm

dioxide focuses on class-based injection. For factory functions with logic, dependency-injector's `Factory` provider is more flexible.

**Workaround:** Use `register_factory()` for simple cases.
:::

:::{grid-item-card} You have an existing dependency-injector codebase
:class-card: sd-border-0 sd-shadow-sm

Migration requires effort. If your current setup works, the benefits may not justify the cost.

**See:** [Migration Guide](migration-from-dependency-injector.rst)
:::

:::{grid-item-card} You need XML/YAML configuration
:class-card: sd-border-0 sd-shadow-sm

dioxide is Python-only. Configuration happens in Python code, not external files.
:::

:::{grid-item-card} You need request scoping
:class-card: sd-border-0 sd-shadow-sm

dioxide currently supports SINGLETON and FACTORY scopes. Request scoping is planned for post-MLP.
:::

::::

---

## Honest Limitations

dioxide intentionally excludes some features to maintain simplicity:

### No Provider Functions (Yet)

dioxide uses class-based injection. You cannot do:

```python
# Not supported
@provider
def create_database(config: AppConfig) -> Database:
    return Database(config.db_url)
```

**Workaround:** Use a class with `@lifecycle`:

```python
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresDatabase:
    def __init__(self, config: AppConfig):
        self.config = config

    async def initialize(self) -> None:
        self.engine = create_async_engine(self.config.db_url)
```

### No XML/YAML Configuration

dioxide uses Python for configuration:

```python
# Not supported
# container.load("config.yaml")

# Use Pydantic Settings instead
class AppConfig(BaseSettings):
    db_url: str
    model_config = {"env_prefix": "APP_"}

container.register_instance(AppConfig, AppConfig())
```

### No Request Scoping (MLP)

Currently, all components are either SINGLETON or FACTORY. Request scoping (one instance per HTTP request) is planned for v0.2.0.

### Rust Requirement for Source Builds

dioxide uses Rust for performance. Installing from source requires a Rust toolchain. Pre-built wheels are available for common platforms:

- Linux (x86_64, ARM64)
- macOS (x86_64, ARM64)
- Windows (x86_64)

---

## What dioxide is NOT

These are not limitations to be fixed later. They are intentional design decisions.

### NOT a Framework

dioxide is a library, not a framework. It does not dictate your application structure:

- No required base classes
- No mandatory folder layouts
- No lifecycle hooks you must implement
- Integrate it into your architecture, not the reverse

### NOT a Configuration System

dioxide does not manage configuration. Use the right tool for configuration:

```python
# Use Pydantic Settings for configuration
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    database_url: str
    sendgrid_api_key: str

# dioxide injects the config, doesn't manage it
@service
class NotificationService:
    def __init__(self, config: AppConfig): ...
```

### NOT Trying to Solve Every DI Pattern

dioxide focuses on constructor injection only:

- **No property injection** - Explicit constructor parameters are clearer
- **No method injection** - If you need it, the design may need rethinking
- **No circular dependency resolution** - Circular deps are architecture problems, not DI problems

### NOT Necessarily the Fastest for Raw Lookups

While dioxide's Rust backend is fast, the comparison depends on what you measure:

- **Cached singleton resolution**: dioxide is extremely fast (~167ns)
- **Initial container setup**: Comparable to other frameworks
- **Complex provider factories**: dependency-injector's Cython may be faster for some patterns

Choose dioxide for the developer experience, not micro-benchmarks.

### NOT Feature-Complete by Design

dioxide intentionally has a small API surface:

- 3 decorators: `@adapter.for_()`, `@service`, `@lifecycle`
- 1 container class: `Container(profile=...)`
- That's it

If you need AOP interceptors, request scoping, or complex factory patterns, you may want a more feature-rich framework.

---

## Performance

dioxide's Rust backend provides significant performance advantages:

:::{list-table} Benchmark Results
:header-rows: 1
:widths: 40 30 30

* - Operation
  - dioxide
  - Pure Python DI

* - Simple resolution
  - ~167-300ns
  - ~10-50us

* - Nested dependencies (5 levels)
  - ~300-500ns
  - ~50-200us

* - Container initialization (100 components)
  - <10ms
  - ~50-100ms

* - High concurrency (1000 concurrent)
  - Consistent
  - Degrades
:::

**Why it matters:**

- Negligible overhead compared to manual DI
- No performance excuses for using dependency injection
- Consistent under load (important for production)

---

## Migration Path

If you're coming from another framework:

### From dependency-injector

dioxide provides a comprehensive migration guide with step-by-step instructions and code examples.

```{button-ref} migration-from-dependency-injector
:color: primary
:outline:
:class: sd-rounded-pill

View Migration Guide
```

### From manual DI

If you're manually passing dependencies, dioxide makes it automatic:

```python
# Before (manual)
config = AppConfig()
email = SendGridAdapter(config)
service = NotificationService(email)

# After (dioxide)
container = Container(profile=Profile.PRODUCTION)
service = container.resolve(NotificationService)  # All dependencies injected
```

### From no DI

If you're not using dependency injection at all, dioxide helps you adopt clean architecture incrementally:

1. Define a Protocol for one external dependency
2. Create production and test adapters
3. Add `@service` to business logic
4. Use `Container(profile=...)` and `resolve()`

Start with one port, expand as needed.

---

## Community and Support

dioxide is actively maintained with a focus on developer experience:

- **GitHub Issues:** [github.com/mikelane/dioxide/issues](https://github.com/mikelane/dioxide/issues)
- **Discussions:** [github.com/mikelane/dioxide/discussions](https://github.com/mikelane/dioxide/discussions)
- **Documentation:** [dioxide.readthedocs.io](https://dioxide.readthedocs.io)

---

## Summary

dioxide is the right choice if you value:

- **Simplicity** - Minimal API, maximum clarity
- **Type safety** - Full static analysis support
- **Architecture** - Explicit hexagonal patterns
- **Testing** - Fakes over mocks philosophy
- **Performance** - Rust-backed speed

It's honest about its limitations (no provider functions, no request scope yet) and doesn't try to be everything to everyone.

**The goal is simple:** Make the Dependency Inversion Principle feel inevitable.

```{button-ref} user_guide/getting_started
:color: primary
:class: sd-rounded-pill sd-px-4 sd-py-2

Get Started
```
