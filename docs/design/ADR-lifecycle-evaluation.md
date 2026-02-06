# ADR: Lifecycle Decorator Evaluation

**Status:** Accepted
**Date:** 2026-02-05
**Deciders:** Product-Technical-Lead, Senior-Developer
**Related Issues:** #388 (Evaluate lifecycle decorator alternatives)

---

## Context

A skeptical developer raised a valid concern about the `@lifecycle` decorator:

> "Lifecycle decorator ceremony -- too many decorators, magic method names"

The current approach requires two decorators and methods with names (`initialize`, `dispose`) that
feel arbitrary rather than Pythonic:

```python
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    async def initialize(self) -> None:  # "Magic" name
        self.conn = await aioredis.create_pool(...)

    async def dispose(self) -> None:  # "Magic" name
        await self.conn.close()
```

We need to evaluate whether the current approach is the right one, or whether an alternative
would better serve dioxide's guiding principles (explicit, Pythonic, type-safe, zero ceremony).

### Scope of Impact

The `@lifecycle` decorator is deeply integrated into the container:
- `Container.start()` and `Container.stop()` call `initialize()`/`dispose()` on all `@lifecycle` components
- Dependency-ordered initialization and reverse-ordered disposal
- Rollback on initialization failure
- `ScopedContainer` manages REQUEST-scoped lifecycle components
- 34 test files reference lifecycle behavior
- `_dioxide_lifecycle` attribute is the detection mechanism

Any change to the lifecycle API is a **breaking change** affecting all users who have adopted it.

---

## Options Evaluated

### Option A: Keep Current `@lifecycle` Decorator (Document Better)

```python
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    async def initialize(self) -> None:
        self.conn = await aioredis.create_pool(...)

    async def dispose(self) -> None:
        await self.conn.close()
```

**Strengths:**
- Already implemented and battle-tested across the codebase
- Explicit and visible -- you can see at a glance which components have lifecycle
- No breaking changes required
- Decorator composition is well-understood (order-independent, validated at decoration time)
- Clear separation: `@service`/`@adapter.for_()` handle registration, `@lifecycle` handles resource management
- Consistent with dioxide's decorator-based API (`@service`, `@adapter.for_()`, `@lifecycle`)

**Weaknesses:**
- Method names `initialize`/`dispose` feel arbitrary to newcomers
- Two decorators for one concept (registration + lifecycle)
- Not using Python's standard `__aenter__`/`__aexit__` protocol

**Alignment with Guiding Principles:**
- Type-Checker is Source of Truth: **4/5** -- `.pyi` stub validates method signatures via mypy
- Explicit Over Clever: **5/5** -- Nothing hidden, decorator makes lifecycle explicit
- Fails Fast: **5/5** -- Validates at decoration time that `initialize()` and `dispose()` exist and are async
- Zero Ceremony: **3/5** -- Requires extra decorator + two named methods
- Pythonic: **3/5** -- Custom method names instead of Python protocols
- Testing is Architecture: **5/5** -- Test fakes can skip `@lifecycle` entirely

### Option B: Mixin Base Class with `__aenter__`/`__aexit__`

```python
from dioxide import LifecycleMixin

@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisAdapter(LifecycleMixin):
    async def __aenter__(self):
        self.conn = await aioredis.create_pool(...)
        return self

    async def __aexit__(self, *args):
        await self.conn.close()
```

**Strengths:**
- Uses Python's standard async context manager protocol (`__aenter__`/`__aexit__`)
- Only one decorator needed (`@adapter.for_()`)
- Familiar to Python developers who know `async with`
- IDE support is excellent (standard dunder methods)

**Weaknesses:**
- **Requires inheritance** -- violates dioxide's composition-over-inheritance philosophy
- `__aenter__` must return `self` (or another value) -- semantically different from "initialize and forget"
- `__aexit__` receives exception info `(exc_type, exc_val, tb)` -- unnecessary for resource cleanup
- Mixin creates a coupling between the lifecycle mechanism and the class hierarchy
- Multiple inheritance with other mixins creates MRO complexity
- **Breaking change**: All existing `@lifecycle` users must refactor to inheritance + rename methods
- Detection mechanism changes: checking `isinstance(x, LifecycleMixin)` instead of `hasattr(x, '_dioxide_lifecycle')`
- Context manager semantics imply scoped usage (`async with adapter:`), but lifecycle components are managed by the container, not by individual call sites

**Alignment with Guiding Principles:**
- Type-Checker is Source of Truth: **4/5** -- Inheritance ensures method signatures
- Explicit Over Clever: **3/5** -- Inheritance is implicit (have to check class hierarchy)
- Fails Fast: **3/5** -- No decoration-time validation (errors surface at container.start())
- Zero Ceremony: **4/5** -- One decorator, standard methods
- Pythonic: **5/5** -- Standard Python protocol
- Testing is Architecture: **3/5** -- Test fakes must also inherit from LifecycleMixin or use different detection

### Option C: Protocol Detection (Implicit)

```python
class Lifecycle(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...

# Container auto-detects Lifecycle protocol compliance
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisAdapter:  # Implicitly implements Lifecycle
    async def start(self) -> None:
        self.conn = await aioredis.create_pool(...)

    async def stop(self) -> None:
        await self.conn.close()
```

**Strengths:**
- No extra decorator needed -- container detects protocol compliance automatically
- Type-checkable via `typing.Protocol`
- `start`/`stop` are more intuitive method names than `initialize`/`dispose`

**Weaknesses:**
- **Implicit behavior** -- violates dioxide's "Explicit Over Clever" principle
- Method name collision risk: `start()` and `stop()` are common method names that could conflict with domain logic (e.g., a `TimerService` with its own `start()`/`stop()`)
- Detection at scan time adds complexity: must introspect every class for protocol compliance
- False positives: any class with `start()`/`stop()` methods would trigger lifecycle management
- No opt-out mechanism if a class happens to have matching methods but doesn't want lifecycle management
- **Breaking change**: Rename `initialize`/`dispose` to `start`/`stop` everywhere
- Performance concern: Protocol runtime checking (`isinstance` with `Protocol`) is slower than attribute checks

**Alignment with Guiding Principles:**
- Type-Checker is Source of Truth: **5/5** -- Protocol is fully type-checkable
- Explicit Over Clever: **1/5** -- Completely implicit; user might not realize lifecycle is active
- Fails Fast: **2/5** -- Protocol compliance only checked at scan time, not decoration time
- Zero Ceremony: **5/5** -- No decorator, no inheritance, just implement methods
- Pythonic: **4/5** -- Protocols are Pythonic, but implicit detection is magic
- Testing is Architecture: **2/5** -- Test fakes with `start()`/`stop()` methods would get unwanted lifecycle management

### Option D: Single Decorator with `lifecycle=True` Parameter

```python
@adapter.for_(CachePort, profile=Profile.PRODUCTION, lifecycle=True)
class RedisAdapter:
    async def initialize(self) -> None:
        self.conn = await aioredis.create_pool(...)

    async def dispose(self) -> None:
        await self.conn.close()
```

**Strengths:**
- Single decorator for everything
- Explicit configuration via parameter
- No additional imports needed

**Weaknesses:**
- Method names still "arbitrary" (`initialize`/`dispose`) -- doesn't solve the original complaint
- Overloads `@adapter.for_()` with lifecycle concerns (violates single responsibility)
- Only works for adapters -- `@service` would need a parallel `lifecycle=True` parameter
- Two different decorators (`@adapter.for_()` and `@service`) need the same parameter, creating duplication
- Validation logic for `initialize()`/`dispose()` would live in both `adapter.py` and `services.py`
- **Breaking change**: Existing `@lifecycle` users must add `lifecycle=True` to their `@adapter.for_()` or `@service`
- Less composable: `@lifecycle` works with both `@service` and `@adapter.for_()` through simple composition

**Alignment with Guiding Principles:**
- Type-Checker is Source of Truth: **4/5** -- Same validation as current
- Explicit Over Clever: **4/5** -- Parameter makes intent clear
- Fails Fast: **4/5** -- Can validate at decoration time
- Zero Ceremony: **4/5** -- Single decorator
- Pythonic: **3/5** -- Parameter bag on decorator is less Pythonic than composition
- Testing is Architecture: **4/5** -- Can omit `lifecycle=True` in test adapters

---

## Evaluation Summary

| Criterion | Weight | A: Keep | B: Mixin | C: Protocol | D: Parameter |
|-----------|--------|---------|----------|-------------|--------------|
| Explicit Over Clever | High | 5 | 3 | 1 | 4 |
| Fails Fast | High | 5 | 3 | 2 | 4 |
| Breaking Change Risk | High | 5 | 2 | 2 | 3 |
| Pythonic | High | 3 | 5 | 4 | 3 |
| Zero Ceremony | Medium | 3 | 4 | 5 | 4 |
| Type Safety | Medium | 4 | 4 | 5 | 4 |
| Testing | Medium | 5 | 3 | 2 | 4 |
| IDE Support | Medium | 4 | 5 | 4 | 4 |
| Consistency | Medium | 5 | 3 | 2 | 3 |
| **Weighted Score** | | **39** | **30** | **25** | **31** |

### Scoring Methodology

High-weight criteria (multiplied by 3): Explicit Over Clever, Fails Fast, Breaking Change Risk, Pythonic.
Medium-weight criteria (multiplied by 2): Zero Ceremony, Type Safety, Testing, IDE Support, Consistency.

| Option | High (x3) | Medium (x2) | Total |
|--------|-----------|-------------|-------|
| A: Keep | (5+5+5+3) x 3 = 54 | (3+4+5+4+5) x 2 = 42 | **96** |
| B: Mixin | (3+3+2+5) x 3 = 39 | (4+4+3+5+3) x 2 = 38 | **77** |
| C: Protocol | (1+2+2+4) x 3 = 27 | (5+5+2+4+2) x 2 = 36 | **63** |
| D: Parameter | (4+4+3+3) x 3 = 42 | (4+4+4+4+3) x 2 = 38 | **80** |

---

## Decision

**Keep the current `@lifecycle` decorator (Option A) and improve documentation.**

### Rationale

1. **"Explicit Over Clever" is our highest priority.** The `@lifecycle` decorator makes lifecycle
   management visible at a glance. You can `grep` for `@lifecycle` and immediately find every
   component that has resource management. With Protocol detection (Option C), lifecycle behavior
   would be invisible -- a developer might not realize their `start()`/`stop()` methods are being
   called by the container.

2. **"Fails Fast" is critical.** The current implementation validates at decoration time that
   `initialize()` and `dispose()` exist and are async coroutines. Options B and C defer validation
   to container start time, which is later in the application lifecycle and harder to debug.

3. **Breaking change risk is unjustifiable.** Dioxide is at v1.0.0 (stable). All alternatives
   require a breaking change. The lifecycle API works correctly, has comprehensive test coverage
   (34 test files), and the concern is about aesthetics, not functionality. Breaking a working API
   for cosmetic improvement violates the principle of least surprise.

4. **The "arbitrary method names" concern is addressable with documentation.** The names
   `initialize` and `dispose` were chosen deliberately:
   - `initialize` communicates "set up resources for use" (not `start`, which implies ongoing activity)
   - `dispose` communicates "release resources" (not `close`, which is too specific to connections)
   - They parallel .NET's `IDisposable.Dispose()` pattern, which is well-established in DI literature
   - Unlike `__aenter__`/`__aexit__`, they don't carry context manager semantics that imply scoped usage

5. **Composition > Inheritance.** The `@lifecycle` decorator composes naturally with both
   `@service` and `@adapter.for_()` without coupling. The Mixin approach (Option B) introduces
   inheritance, which is harder to reason about (MRO) and less flexible.

6. **The "two decorators" complaint has a counterargument.** Two decorators actually encode two
   distinct concerns:
   - `@service` or `@adapter.for_()`: "What is this component and how should it be registered?"
   - `@lifecycle`: "Does this component need resource management?"

   Merging them (Option D) violates single responsibility. Most components do NOT need lifecycle
   management -- keeping it separate means most code uses a single, simple decorator.

### Industry Context

The approach aligns with established patterns in the Python DI ecosystem:

- [dependency-injector](https://python-dependency-injector.ets-labs.org/) uses a `Resource` provider
  type with explicit `init`/`shutdown` methods -- separate from the provider registration mechanism.
- FastAPI's lifespan handler uses explicit `startup`/`shutdown` callbacks, not implicit protocol detection.
- Django uses explicit signal-based lifecycle (`pre_init`, `post_init`, `pre_save`, etc.).

The explicit decorator pattern is the norm, not the exception.

---

## Actions

### Documentation Improvements

To address the original concern ("magic method names"), the following documentation updates
should be made:

1. **Add a "Why initialize/dispose?" section** to the lifecycle module docstring explaining the
   method name rationale vs. alternatives (`start/stop`, `__aenter__/__aexit__`, `setup/teardown`)

2. **Add lifecycle patterns guide** showing common patterns (database pools, HTTP sessions,
   message queues) that make the `initialize`/`dispose` names feel natural in context

3. **Add a FAQ entry**: "Why not use `__aenter__`/`__aexit__` for lifecycle?" explaining the
   semantic difference between context manager protocol and container-managed lifecycle

### Future Consideration (Post-v2)

If user feedback continues to indicate that the two-decorator pattern is a pain point,
consider a **non-breaking enhancement** where `@lifecycle` validation is performed lazily:

```python
# Potential future sugar (non-breaking, additive)
@adapter.for_(CachePort, profile=Profile.PRODUCTION, lifecycle=True)
class RedisAdapter:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...

# This would be equivalent to:
@adapter.for_(CachePort, profile=Profile.PRODUCTION)
@lifecycle
class RedisAdapter:
    async def initialize(self) -> None: ...
    async def dispose(self) -> None: ...
```

This would be purely additive -- the existing `@lifecycle` decorator would continue to work.
It should only be pursued if there is demonstrated user demand, not speculatively.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Users continue to find ceremony excessive | Medium | Low | Documentation improvements; future additive sugar |
| Competitor frameworks offer simpler lifecycle | Low | Medium | Monitor ecosystem; additive improvements if needed |
| Method name confusion with domain methods | Low | Low | `initialize`/`dispose` are rarely used as domain method names |

---

## References

- [Dioxide Design Principles](../design-principles.md) -- Canonical design reference
- [ADR-001: Container Architecture](ADR-001-container-architecture.md) -- Container design decisions
- [GitHub Issue #388](https://github.com/mikelane/dioxide/issues/388) -- Original spike issue
- [Python dependency-injector](https://python-dependency-injector.ets-labs.org/) -- Resource provider pattern
- [.NET IDisposable Pattern](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-dispose) -- Inspiration for `dispose` naming

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-05 | Senior-Developer | Initial evaluation and recommendation |
