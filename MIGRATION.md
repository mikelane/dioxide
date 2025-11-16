# Migration Guide

This guide helps you migrate between dioxide versions with breaking API changes.

## v0.0.1-alpha → v0.0.2-alpha (Hexagonal Architecture API)

v0.0.2-alpha introduces a **breaking API change** to embrace hexagonal architecture (ports-and-adapters pattern). The new API makes clean architecture patterns explicit and type-safe.

### Summary of Changes

| v0.0.1-alpha (Old) | v0.0.2-alpha (New) | Notes |
|-------------------|-------------------|-------|
| `@component` | `@service` | For core business logic |
| `@component(scope=Scope.FACTORY)` | N/A (removed) | Services are always singletons |
| `@component` + `@profile` | `@adapter.for_(Port, profile=...)` | For infrastructure adapters |
| `container.scan()` | `container.scan(profile=...)` | Profile-based filtering |
| Manual container instantiation | `from dioxide import container` | Global singleton pattern (recommended) |

### Breaking Changes

#### 1. `@component` → `@service` for Core Business Logic

**Before (v0.0.1-alpha):**
```python
from dioxide import component

@component
class UserService:
    def create_user(self, name: str) -> dict:
        return {"name": name, "id": 1}
```

**After (v0.0.2-alpha):**
```python
from dioxide import service

@service
class UserService:
    def create_user(self, name: str) -> dict:
        return {"name": name, "id": 1}
```

**Why?** The `@service` decorator explicitly marks classes as core business logic that:
- Is always a singleton (one shared instance)
- Is available in all profiles (production, test, development)
- Contains no infrastructure knowledge

#### 2. Hexagonal Architecture: Ports and Adapters

**Before (v0.0.1-alpha):**
```python
from dioxide import component, profile
from typing import Protocol

class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

@component
@profile("production")
class SendGridEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass  # Real implementation

@component
@profile("test")
class FakeEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass  # Fake implementation
```

**After (v0.0.2-alpha):**
```python
from dioxide import adapter, service, Profile
from typing import Protocol

# Define port (interface) - the seam
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Production adapter
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass  # Real SendGrid implementation

# Test adapter (fake)
@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        pass  # Fake for testing
```

**Why?** The `@adapter.for_(Port, profile=...)` syntax makes the relationship between ports (interfaces) and adapters (implementations) explicit. This encourages hexagonal architecture patterns.

#### 3. Profile System: String → Enum

**Before (v0.0.1-alpha):**
```python
from dioxide import container

container.scan(profile="production")
```

**After (v0.0.2-alpha - Recommended):**
```python
from dioxide import container, Profile

container.scan(profile=Profile.PRODUCTION)
```

**Or (still supported):**
```python
container.scan(profile="production")  # String still works
```

**Why?** The `Profile` enum provides type safety and IDE autocomplete for standard profiles:
- `Profile.PRODUCTION`
- `Profile.TEST`
- `Profile.DEVELOPMENT`
- `Profile.STAGING`
- `Profile.CI`
- `Profile.ALL` (wildcard - available in all environments)

#### 4. Global Singleton Container (Recommended)

**Before (v0.0.1-alpha):**
```python
from dioxide import Container

container = Container()  # Manual instantiation
container.scan()
service = container.resolve(UserService)
```

**After (v0.0.2-alpha - Recommended):**
```python
from dioxide import container  # Import global singleton

container.scan(profile=Profile.PRODUCTION)
service = container.resolve(UserService)

# Or bracket syntax:
service = container[UserService]
```

**Why?** The global singleton container simplifies the common case where you only need one container per application. You can still create separate `Container()` instances for testing isolation.

#### 5. Service Dependencies on Ports (Not Adapters)

**Before (v0.0.1-alpha):**
```python
@component
class NotificationService:
    def __init__(self, email: SendGridEmail):  # ❌ Depends on concrete class
        self.email = email
```

**After (v0.0.2-alpha):**
```python
@service
class NotificationService:
    def __init__(self, email: EmailPort):  # ✅ Depends on port (Protocol)
        self.email = email
```

**Why?** Services should depend on ports (interfaces), not concrete adapters. This is the core of hexagonal architecture - your business logic doesn't know or care about infrastructure details.

### Migration Checklist

- [ ] Replace `@component` with `@service` for core business logic classes
- [ ] Remove `@component(scope=Scope.FACTORY)` usage (services are always singletons)
- [ ] Create Protocol/ABC ports for infrastructure boundaries (email, database, HTTP, etc.)
- [ ] Replace `@component` + `@profile` with `@adapter.for_(Port, profile=...)` for adapters
- [ ] Update service constructors to depend on ports (Protocols), not concrete adapters
- [ ] Replace string profiles with `Profile` enum (recommended for type safety)
- [ ] Use global `container` singleton instead of manual `Container()` (optional but recommended)
- [ ] Update `container.scan()` to `container.scan(profile=...)` for profile filtering

### Complete Migration Example

**Before (v0.0.1-alpha):**
```python
from dioxide import Container, component, profile, Scope
from typing import Protocol

class EmailProvider(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

@component
@profile("production")
class SendGridEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        print("Sending via SendGrid")

@component
@profile("test")
class FakeEmail:
    async def send(self, to: str, subject: str, body: str) -> None:
        print("Fake email")

@component
class UserService:
    def __init__(self, email: EmailProvider):
        self.email = email

    async def register(self, email_addr: str) -> None:
        await self.email.send(email_addr, "Welcome!", "Thanks for signing up")

# Usage
container = Container()
container.scan(profile="production")
service = container.resolve(UserService)
```

**After (v0.0.2-alpha):**
```python
from dioxide import container, adapter, service, Profile
from typing import Protocol

# Port (interface)
class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...

# Adapters (implementations)
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        print("Sending via SendGrid")

@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    async def send(self, to: str, subject: str, body: str) -> None:
        print("Fake email")

# Service (core business logic)
@service
class UserService:
    def __init__(self, email: EmailPort):  # Depends on port
        self.email = email

    async def register(self, email_addr: str) -> None:
        await self.email.send(email_addr, "Welcome!", "Thanks for signing up")

# Usage (global singleton container)
container.scan(profile=Profile.PRODUCTION)
service = container[UserService]  # Bracket syntax
```

### Benefits of the New API

1. **Explicit Architecture**: Ports and adapters are clearly distinguished
2. **Type Safety**: `Profile` enum provides IDE autocomplete and type checking
3. **Testability**: Swap entire infrastructure layers by changing profile
4. **Clean Code**: Services have zero knowledge of infrastructure details
5. **Maintainability**: Clear separation between business logic and infrastructure

### Troubleshooting

**Problem**: `KeyError: 'Dependency not registered'`

**Solution**: Ensure you're calling `container.scan(profile=...)` with the correct profile before resolving components. Services are available in all profiles, but adapters are profile-specific.

**Problem**: Multiple adapters registered for the same port

**Solution**: Each `(Port, profile)` combination can only have one adapter. Either:
- Use different profiles for different adapters (`Profile.PRODUCTION` vs `Profile.TEST`)
- Use different ports if you need multiple implementations in the same profile

**Problem**: Service not found after scanning

**Solution**: Ensure the service class is decorated with `@service` and has been imported before calling `container.scan()`. Python won't execute the decorator unless the module is imported.

### Need Help?

- See [README.md](README.md) for Quick Start examples
- See [CLAUDE.md](CLAUDE.md) for detailed API documentation
- See [examples/hexagonal_architecture.py](examples/hexagonal_architecture.py) for working examples
- Open an issue on GitHub: https://github.com/mikelane/dioxide/issues
