# Cookbook

Practical, copy-paste-ready recipes for common dioxide patterns.

This cookbook provides working code examples for real-world scenarios. Each recipe follows a consistent format:

- **Problem**: What you're trying to solve
- **Solution**: The dioxide approach
- **Code**: Complete, working example
- **Explanation**: Why this works

## Quick Links

::::{grid} 2
:gutter: 3

:::{grid-item-card} FastAPI Integration
:link: fastapi
:link-type: doc

Routes, dependency injection, lifecycle management, and testing endpoints.
:::

:::{grid-item-card} Testing Patterns
:link: testing
:link-type: doc

Fixtures, fakes, test isolation, and async testing patterns.
:::

:::{grid-item-card} Configuration
:link: configuration
:link-type: doc

Pydantic Settings integration and environment-specific config.
:::

:::{grid-item-card} Database Patterns
:link: database
:link-type: doc

SQLAlchemy adapters, repository pattern, and transaction handling.
:::

:::{grid-item-card} Library Authors
:link: libraries
:link-type: doc

Make your library dioxide-compatible without depending on dioxide.
:::

::::

## Recipe Index

### FastAPI Integration

| Recipe | Description |
|--------|-------------|
| [Basic Setup](fastapi.md#recipe-basic-fastapi-setup) | Container + lifespan integration |
| [Dependency Injection](fastapi.md#recipe-inject-services-into-routes) | Using `Depends()` with dioxide |
| [Testing Endpoints](fastapi.md#recipe-testing-fastapi-endpoints) | TestClient with fakes |
| [Middleware Integration](fastapi.md#recipe-custom-middleware-with-dioxide) | Access container in middleware |

### Testing Patterns

| Recipe | Description |
|--------|-------------|
| [Container Fixture](testing.md#recipe-container-fixture) | Fresh container per test |
| [Typed Fake Access](testing.md#recipe-typed-fake-access) | IDE-friendly fixture typing |
| [Async Testing](testing.md#recipe-async-test-setup) | pytest-asyncio patterns |
| [Error Injection](testing.md#recipe-error-injection) | Configurable fake failures |
| [Time Control](testing.md#recipe-controllable-time) | Fake clock for time-dependent tests |

### Configuration

| Recipe | Description |
|--------|-------------|
| [Pydantic Settings](configuration.md#recipe-pydantic-settings-adapter) | Type-safe config with validation |
| [Profile-Based Config](configuration.md#recipe-profile-based-configuration) | Different settings per environment |
| [Secrets Management](configuration.md#recipe-secrets-from-environment) | Secure secret handling |
| [Config Validation](configuration.md#recipe-startup-validation) | Fail fast on missing config |

### Database Patterns

| Recipe | Description |
|--------|-------------|
| [SQLAlchemy Adapter](database.md#recipe-sqlalchemy-async-adapter) | Async SQLAlchemy with lifecycle |
| [Repository Pattern](database.md#recipe-repository-pattern) | Clean data access abstraction |
| [In-Memory Fake](database.md#recipe-in-memory-repository-fake) | Fast fake for testing |
| [Transaction Handling](database.md#recipe-transaction-management) | Commit/rollback patterns |

### Library Authors

| Recipe | Description |
|--------|-------------|
| [dioxide-Compatible Libraries](libraries.md) | Optional DI with sensible defaults |

## Philosophy

These recipes follow dioxide's core principles:

1. **Fakes over mocks** - Real implementations with shortcuts
2. **Ports define boundaries** - Clear interfaces between layers
3. **Profiles select adapters** - Environment determines implementation
4. **Type safety matters** - Leverage Python's type system

```{toctree}
:hidden:
:maxdepth: 1

fastapi
testing
configuration
database
libraries
```
