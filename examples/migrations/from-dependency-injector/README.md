# Migration from dependency-injector to dioxide

This example demonstrates how to migrate from the `dependency-injector` library to dioxide,
showing equivalent patterns and the simplifications that dioxide provides.

## Overview

`dependency-injector` is a popular Python DI framework that uses explicit container configuration
with providers. dioxide takes a different approach with decorator-based registration and
profile-based adapter selection.

## Key Differences

| Aspect | dependency-injector | dioxide |
|--------|---------------------|---------|
| **Container** | Class-based with explicit providers | Scan-based with decorators |
| **Registration** | `providers.Factory`, `providers.Singleton` | `@adapter.for_()`, `@service` |
| **Scoping** | Provider types determine lifecycle | `scope=Scope.SINGLETON/FACTORY` |
| **Profiles** | Manual via different containers | Built-in `Profile` enum |
| **Wiring** | `@inject` + container wiring | Constructor injection, automatic |
| **Testing** | Override providers in container | Profile.TEST with fake adapters |

## File Structure

```
from-dependency-injector/
├── README.md              # This file
├── before/                # dependency-injector approach
│   ├── pyproject.toml
│   ├── app/
│   │   ├── ports.py       # Same interfaces
│   │   ├── services.py    # Service with @inject
│   │   ├── adapters.py    # Implementations
│   │   ├── container.py   # Explicit container config
│   │   └── main.py        # Application entry
│   └── tests/
│       └── test_services.py
└── after/                 # dioxide approach
    ├── pyproject.toml
    ├── app/
    │   ├── ports.py       # Protocol definitions
    │   ├── services.py    # @service decorator
    │   ├── adapters.py    # @adapter.for_() decorators
    │   └── main.py        # Simplified entry
    └── tests/
        └── test_services.py
```

## Migration Steps

### Step 1: Convert Interfaces to Protocols

**Before (ABC-based):**
```python
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str) -> dict | None:
        pass
```

**After (Protocol-based):**
```python
from typing import Protocol

class UserRepositoryPort(Protocol):
    async def get(self, user_id: str) -> dict | None:
        ...
```

### Step 2: Convert Providers to Decorators

**Before (dependency-injector):**
```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    user_repository = providers.Singleton(
        PostgresUserRepository,
        connection_string=config.database.url,
    )

    user_service = providers.Factory(
        UserService,
        repository=user_repository,
    )
```

**After (dioxide):**
```python
from dioxide import adapter, service, Profile

@adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
class PostgresUserRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

@service
class UserService:
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository
```

### Step 3: Convert Test Overrides to Profiles

**Before (dependency-injector):**
```python
def test_user_service():
    container = Container()
    container.user_repository.override(providers.Singleton(FakeUserRepository))

    service = container.user_service()
    # test...
```

**After (dioxide):**
```python
@adapter.for_(UserRepositoryPort, profile=Profile.TEST)
class FakeUserRepository:
    def __init__(self):
        self.users = {}

def test_user_service(container):
    # FakeUserRepository automatically used with Profile.TEST
    service = container.resolve(UserService)
    # test...
```

### Step 4: Remove @inject Decorators

**Before (dependency-injector):**
```python
from dependency_injector.wiring import inject, Provide

@inject
async def get_user_endpoint(
    user_id: str,
    service: UserService = Provide[Container.user_service],
):
    return await service.get_user(user_id)
```

**After (dioxide):**
```python
async def get_user_endpoint(user_id: str, service: UserService):
    # Service resolved by framework integration (FastAPI, Flask, etc.)
    return await service.get_user(user_id)
```

## Running the Examples

### Before (dependency-injector)
```bash
cd before
pip install -e .
python -m app.main
```

### After (dioxide)
```bash
cd after
pip install -e .
python -m app.main
```

## Benefits of Migration

1. **Less Boilerplate**: No explicit container configuration
2. **Type Safety**: Protocol-based ports work with mypy
3. **Built-in Profiles**: No manual container overrides for testing
4. **Simpler Testing**: Fakes are just adapters with `Profile.TEST`
5. **No Wiring**: Dependencies resolved automatically from type hints
6. **Performance**: Rust-backed container for O(1) resolution

## Common Gotchas

1. **Singleton vs Factory**: dioxide defaults to `Scope.SINGLETON`. Use `scope=Scope.FACTORY`
   for per-request instances.

2. **Configuration**: dioxide doesn't handle config injection. Use Pydantic Settings
   or environment variables.

3. **Provider Overrides**: Replace with profile-based adapters. There's no runtime override.

4. **Wiring**: Remove all `@inject` decorators and `Provide[...]` defaults.
