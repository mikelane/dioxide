# Migration from injector to dioxide

This example demonstrates how to migrate from the `injector` library to dioxide,
showing the key pattern differences and simplifications.

## Overview

`injector` is a Python dependency injection framework inspired by Guice (Java).
It uses `Module` classes with `Binder` configuration and `@inject` decorators.
dioxide replaces this with decorator-based registration and profile-based selection.

## Key Differences

| Aspect | injector | dioxide |
|--------|----------|---------|
| **Container** | `Injector` with `Module` classes | `Container` with `scan()` |
| **Registration** | `Binder.bind()` in modules | `@adapter.for_()` decorators |
| **Injection** | `@inject` decorator required | Automatic from type hints |
| **Scoping** | `@singleton` decorator | `scope=Scope.SINGLETON/FACTORY` |
| **Profiles** | Manual module composition | Built-in `Profile` enum |
| **Interface binding** | `binder.bind(Interface, to=Impl)` | `@adapter.for_(Port, profile=...)` |

## File Structure

```
from-injector/
├── README.md              # This file
├── before/                # injector approach
│   ├── pyproject.toml
│   ├── app/
│   │   ├── ports.py       # ABC-based interfaces
│   │   ├── services.py    # Services with @inject
│   │   ├── adapters.py    # Implementations
│   │   ├── modules.py     # Binder configuration
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

### Step 1: Replace ABC with Protocol

**Before (ABC-based):**
```python
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool:
        pass
```

**After (Protocol-based):**
```python
from typing import Protocol

class NotificationPort(Protocol):
    def send(self, recipient: str, message: str) -> bool:
        ...
```

### Step 2: Remove @inject Decorators

**Before (injector):**
```python
from injector import inject

class OrderService:
    @inject
    def __init__(
        self,
        repository: OrderRepository,
        notifications: NotificationService,
    ):
        self.repository = repository
        self.notifications = notifications
```

**After (dioxide):**
```python
from dioxide import service

@service
class OrderService:
    def __init__(
        self,
        repository: OrderRepositoryPort,
        notifications: NotificationPort,
    ):
        self.repository = repository
        self.notifications = notifications
```

### Step 3: Convert Modules to Decorators

**Before (injector modules):**
```python
from injector import Module, Binder, singleton

class ProductionModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(OrderRepository, to=PostgresOrderRepository, scope=singleton)
        binder.bind(NotificationService, to=EmailNotificationService, scope=singleton)

class TestModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(OrderRepository, to=FakeOrderRepository, scope=singleton)
        binder.bind(NotificationService, to=FakeNotificationService, scope=singleton)
```

**After (dioxide decorators):**
```python
from dioxide import adapter, Profile, Scope

@adapter.for_(OrderRepositoryPort, profile=Profile.PRODUCTION, scope=Scope.SINGLETON)
class PostgresOrderRepository:
    ...

@adapter.for_(OrderRepositoryPort, profile=Profile.TEST, scope=Scope.SINGLETON)
class FakeOrderRepository:
    ...

@adapter.for_(NotificationPort, profile=Profile.PRODUCTION)
class EmailNotificationAdapter:
    ...

@adapter.for_(NotificationPort, profile=Profile.TEST)
class FakeNotificationAdapter:
    ...
```

### Step 4: Simplify Container Usage

**Before (injector):**
```python
from injector import Injector

# Production
injector = Injector([ProductionModule()])
service = injector.get(OrderService)

# Testing
test_injector = Injector([TestModule()])
service = test_injector.get(OrderService)
```

**After (dioxide):**
```python
from dioxide import Container, Profile

# Production
container = Container()
container.scan("app", profile=Profile.PRODUCTION)
service = container.resolve(OrderService)

# Testing
container = Container()
container.scan("app", profile=Profile.TEST)
service = container.resolve(OrderService)
```

## Running the Examples

### Before (injector)
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

1. **No @inject Boilerplate**: Dependencies resolved from type hints alone
2. **Built-in Profiles**: No need to create separate module classes
3. **Decorator Registration**: Clear, declarative adapter binding
4. **Type Safety**: Protocol-based ports work better with mypy
5. **Simpler Testing**: Profile.TEST selects fakes automatically
6. **Less Configuration**: No Module classes to write and compose

## Common Gotchas

1. **@singleton Scope**: Replace `@singleton` with `scope=Scope.SINGLETON` in the
   `@adapter.for_()` decorator. Note: dioxide defaults to SINGLETON.

2. **Module Composition**: injector allows composing multiple modules. With dioxide,
   use a single scan with the appropriate profile instead.

3. **Provider Functions**: injector supports `@provider` methods in modules. With
   dioxide, create an adapter class instead or use a factory pattern.

4. **Assisted Injection**: injector supports `@assisted` for partial injection.
   dioxide doesn't have this - refactor to use factories or configuration objects.

5. **Multi-binding**: injector supports binding lists of implementations. dioxide
   doesn't support this directly - use a factory that creates the list.
