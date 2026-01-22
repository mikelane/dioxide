# Decorator Order Guide

dioxide decorators (`@service`, `@adapter.for_()`, `@lifecycle`) work in **any order**. This guide explains why and recommends a consistent convention for readability.

## TL;DR

**Order doesn't matter functionally**, but for consistency we recommend:

```python
# Recommended convention
@adapter.for_(Port, profile=Profile.PRODUCTION)
@lifecycle
class MyAdapter:
    ...

@service
@lifecycle
class MyService:
    ...
```

## Why Order Doesn't Matter

dioxide decorators only **add metadata attributes** to the class. They don't wrap, transform, or modify the class behavior. This makes them fully commutative - order of application is irrelevant.

### What Each Decorator Does

| Decorator | Attributes Added |
|-----------|------------------|
| `@lifecycle` | `_dioxide_lifecycle = True` |
| `@service` | `__dioxide_profiles__`, `__dioxide_scope__` |
| `@adapter.for_(Port, ...)` | `__dioxide_port__`, `__dioxide_profiles__`, `__dioxide_scope__`, `__dioxide_multi__`, `__dioxide_priority__` |

Since each decorator only reads the class and adds its own attributes (never modifying or removing others), the decorators can be applied in any sequence with identical results.

### Proof by Example

Both orderings produce identical classes:

```python
# Order A: adapter outer, lifecycle inner
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
@lifecycle
class OrderA:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...
    def send(self, to: str) -> None: ...

# Order B: lifecycle outer, adapter inner
@lifecycle
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class OrderB:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...
    def send(self, to: str) -> None: ...

# Both have identical attributes:
assert OrderA._dioxide_lifecycle == OrderB._dioxide_lifecycle  # True
assert OrderA.__dioxide_port__ == OrderB.__dioxide_port__       # EmailPort
assert OrderA.__dioxide_profiles__ == OrderB.__dioxide_profiles__  # frozenset({'production'})
```

## Recommended Convention

While both orders work, we recommend `@lifecycle` as the **innermost** decorator:

```python
@adapter.for_(Port, profile=Profile.PRODUCTION)
@lifecycle
class MyAdapter:
    async def initialize(self) -> None:
        ...
    async def dispose(self) -> None:
        ...
```

### Why This Convention?

1. **Natural reading order**: "Register an adapter that has lifecycle management" flows better than "Add lifecycle to something that will be registered."

2. **Consistency with other patterns**: In Python, decorators that modify behavior (like `@functools.wraps`) are typically applied closest to the definition. While dioxide decorators don't modify behavior, keeping `@lifecycle` innermost maintains this intuition.

3. **Visual grouping**: Registration decorators (`@service`, `@adapter.for_()`) appear together at the top, making it easy to scan for what's registered with the container.

## Quick Reference

### Adapters with Lifecycle

```python
# Recommended
@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    async def initialize(self) -> None:
        self.pool = await create_pool(...)

    async def dispose(self) -> None:
        await self.pool.close()
```

### Services with Lifecycle

```python
# Recommended
@service
@lifecycle
class CacheWarmer:
    async def initialize(self) -> None:
        await self.warm_cache()

    async def dispose(self) -> None:
        pass
```

### Multiple Profiles

```python
# Recommended
@adapter.for_(CachePort, profile=[Profile.TEST, Profile.DEVELOPMENT])
@lifecycle
class InMemoryCache:
    async def initialize(self) -> None:
        self.data = {}

    async def dispose(self) -> None:
        self.data.clear()
```

## Design Philosophy

dioxide's order-independent decorators reflect the framework's principle of **explicit over clever**. Rather than relying on decorator execution order for behavior (which can be surprising), each decorator simply declares metadata that the container reads at scan time.

This design choice:

- **Reduces cognitive load**: No need to remember "magic" ordering rules
- **Prevents subtle bugs**: No risk of silently broken behavior from wrong order
- **Simplifies debugging**: What you see in the decorator is what gets registered

## See Also

- [Lifecycle Management](../user_guide/architecture.md#lifecycle-management)
- [@lifecycle decorator API](../api/dioxide/lifecycle/index.rst)
- [@adapter.for_() decorator API](../api/dioxide/adapter/index.rst)
- [@service decorator API](../api/dioxide/services/index.rst)
