# ADR-002: PyO3 Binding Strategy

**Status:** Accepted
**Date:** 2025-10-21
**Deciders:** Product-Technical-Lead, Senior-Developer, Code-Reviewer
**Related Issues:** #10 (Container implementation), #11-14 (Provider implementations)
**Depends On:** ADR-001 (Container Architecture)

---

## Context

We need to expose the Rust `Container` to Python in a way that feels natural and Pythonic while leveraging Rust's performance and safety. This involves critical decisions about:

- How Rust types map to Python types
- Memory ownership across the FFI boundary
- Exception handling and error propagation
- Performance optimization strategies
- API design (what's exposed vs. hidden)

The PyO3 bindings are the interface between our high-performance Rust core and Python developers. Getting this right is essential for:
- Developer experience (must feel Pythonic)
- Performance (minimize FFI overhead)
- Safety (no memory corruption, no segfaults)
- Maintainability (clear boundaries, testable)

---

## Decision

We will create a thin PyO3 wrapper layer that delegates to the Rust core, following these principles:

### Core Principles

1. **Thin Wrapper Pattern:** PyO3 bindings are adapters, not implementations
2. **Python-First API:** API design prioritizes Python idioms
3. **Zero-Copy Where Possible:** Minimize data copying across FFI
4. **Fail-Fast Validation:** Validate inputs in Python layer
5. **Rich Error Messages:** Convert Rust errors to helpful Python exceptions

### Architecture

```
┌─────────────────────────────────────────┐
│ Python User Code                        │
│ (FastAPI, Django, etc.)                 │
└─────────────────┬───────────────────────┘
                  │ Pure Python API
                  ↓
┌─────────────────────────────────────────┐
│ python/dioxide/                        │
│ - container.py (Python wrapper)         │
│ - decorators.py (Python decorators)     │
│ - exceptions.py (Python exceptions)     │
└─────────────────┬───────────────────────┘
                  │ Import _dioxide_core
                  ↓
┌─────────────────────────────────────────┐
│ src/adapters/python_container.rs        │
│ (PyO3 #[pyclass] bindings)              │
│ - _RustContainer (#[pyclass])           │
│ - Type conversion                        │
│ - Error mapping                          │
└─────────────────┬───────────────────────┘
                  │ Delegates to
                  ↓
┌─────────────────────────────────────────┐
│ src/domain/container.rs                 │
│ (Pure Rust, no PyO3)                    │
│ - Container struct                       │
│ - Business logic                         │
└─────────────────────────────────────────┘
```

---

## Key Decisions

### Decision 1: Two-Layer API Design

**Decision:** Provide both a Rust PyO3 class AND a Python wrapper class.

**Structure:**

```rust
// src/adapters/python_container.rs
#[pyclass(name = "_RustContainer")]
pub struct RustContainer {
    inner: Arc<Container>,
}

#[pymethods]
impl RustContainer {
    #[new]
    fn new() -> Self {
        RustContainer {
            inner: Arc::new(Container::new()),
        }
    }

    fn register_instance(
        &self,
        py: Python,
        py_type: &PyType,
        instance: PyObject,
    ) -> PyResult<()> {
        let type_key = TypeKey::new(py_type.into());
        self.inner
            .register(type_key, Provider::Instance(instance))
            .map_err(|e| to_python_exception(py, e))
    }

    fn resolve(&self, py: Python, py_type: &PyType) -> PyResult<PyObject> {
        let type_key = TypeKey::from_py_type(py_type);
        self.inner
            .resolve(py, &type_key)
            .map_err(|e| to_python_exception(py, e))
    }
}
```

```python
# python/dioxide/container.py
from dioxide._dioxide_core import _RustContainer

class Container:
    """
    Dependency injection container.

    Provides a Pythonic interface to the Rust-backed DI container.
    """

    def __init__(self):
        self._rust_core = _RustContainer()

    def register_instance(self, type_: type, instance: Any) -> None:
        """Register a pre-created instance as a provider."""
        if not isinstance(instance, type_):
            raise TypeError(
                f"Instance must be of type {type_.__name__}, "
                f"got {type(instance).__name__}"
            )
        self._rust_core.register_instance(type_, instance)

    def resolve(self, type_: type[T]) -> T:
        """Resolve a dependency by type."""
        return self._rust_core.resolve(type_)
```

**Rationale:**
- **Python wrapper (`Container`):** Pythonic API, input validation, type hints
- **Rust class (`_RustContainer`):** Performance-critical operations
- **Separation of concerns:** Python handles ergonomics, Rust handles speed
- **Testability:** Can test Python wrapper separately from Rust

**Trade-offs:**
- ✅ Clean Python API with type hints
- ✅ Pre-validation in Python reduces Rust complexity
- ✅ Easy to add Python-only features (decorators, helpers)
- ❌ Extra function call overhead (negligible: ~10ns)
- ❌ Two places to update for API changes (mitigated by thin wrapper)

### Decision 2: Type Conversion Strategy

**Decision:** Minimal conversion, leverage PyObject for most data.

**Type Mapping:**

| Rust Type | PyO3 Type | Python Type | Notes |
|-----------|-----------|-------------|-------|
| `TypeKey` | `&PyType` | `type` | Direct reference, no copy |
| `Provider::Instance` | `PyObject` | `Any` | Opaque reference |
| `Provider::Class` | `Py<PyType>` | `type` | Owned reference |
| `Provider::Factory` | `PyObject` | `Callable` | Opaque callable |
| `ContainerError` | `PyErr` | `Exception` | Converted to Python exception |
| `Container` | `#[pyclass]` | `_RustContainer` | Wrapped in Arc |

**Rationale:**
- **PyObject:** Generic Python object, zero-copy reference
- **Py<PyType>:** Owned reference to type object (immortal, safe to clone)
- **&PyType:** Borrowed reference for temporary access
- **No serialization:** Objects stay in Python heap, Rust holds references

**Trade-offs:**
- ✅ Zero-copy for all objects
- ✅ No serialization overhead
- ✅ Python objects remain Python (no impedance mismatch)
- ❌ Must acquire GIL for all operations (acceptable: Python is single-threaded)

### Decision 3: Error Handling and Exception Mapping

**Decision:** Map Rust errors to custom Python exception hierarchy.

**Rust Side:**

```rust
fn to_python_exception(py: Python, err: ContainerError) -> PyErr {
    match err {
        ContainerError::DependencyNotRegistered { type_name } => {
            PyKeyError::new_err(format!(
                "Dependency not registered: {}\n\n\
                 The container does not have a provider for type '{}'.\n\n\
                 Possible solutions:\n\
                 1. Register a provider:\n   \
                    container.register_class({}, {})\n\
                 2. Check for typos in the type name",
                type_name, type_name, type_name, type_name
            ))
        }

        ContainerError::DuplicateRegistration { type_name } => {
            PyValueError::new_err(format!(
                "Duplicate provider registration: {}\n\n\
                 A provider for '{}' is already registered.\n\n\
                 Hint: You cannot register the same type twice.",
                type_name, type_name
            ))
        }

        ContainerError::ResolutionFailed { type_name, reason, chain } => {
            PyRuntimeError::new_err(format!(
                "Dependency resolution failed: {}\n\
                 Reason: {}\n\
                 Dependency chain: {}",
                type_name, reason, chain
            ))
        }

        ContainerError::ProviderRegistrationFailed { type_name, reason } => {
            PyValueError::new_err(format!(
                "Provider registration failed: {}\n\
                 Reason: {}",
                type_name, reason
            ))
        }
    }
}
```

**Python Side (Optional Custom Exceptions):**

```python
# python/dioxide/exceptions.py
class DioxideError(Exception):
    """Base exception for dioxide errors."""
    pass

class DependencyNotRegisteredError(DioxideError, KeyError):
    """Raised when attempting to resolve an unregistered dependency."""
    pass

class DuplicateRegistrationError(DioxideError, ValueError):
    """Raised when attempting to register a type twice."""
    pass

class ResolutionError(DioxideError, RuntimeError):
    """Raised when dependency resolution fails."""
    pass
```

**Rationale:**
- **Map to standard Python exceptions:** Pythonic, works with existing code
- **Rich messages:** Include context, suggestions, dependency chains
- **Optional custom hierarchy:** For users who want fine-grained catching
- **Preserve stack traces:** PyO3 automatically propagates Python tracebacks

**Trade-offs:**
- ✅ Pythonic exception handling
- ✅ Excellent error messages
- ✅ Works with standard `try/except`
- ❌ Some information loss in conversion (acceptable: messages are rich)

### Decision 4: Memory Ownership Model

**Decision:** Rust holds references, Python owns objects.

**Ownership Rules:**

1. **Python objects are owned by Python:**
   - Rust never frees Python objects
   - Rust uses `Py<T>` (owned reference) or `PyObject` (opaque reference)
   - Python GC handles cleanup

2. **Rust objects are owned by Rust:**
   - Container owned by Arc (shared ownership)
   - Providers owned by Container
   - Cache owned by Container

3. **Lifetime guarantees:**
   - Python objects: Live as long as Python refcount > 0
   - Rust objects: Live as long as Arc refcount > 0
   - Container: Lives until all Python references dropped

**Reference Counting:**

```rust
// Incrementing refcount when caching
let instance = provider.create(py)?;
let cached = instance.clone_ref(py);  // Increment Python refcount
singletons.insert(type_key, cached);

// Decrementing refcount when dropping
impl Drop for RustContainer {
    fn drop(&mut self) {
        // Arc refcount drops
        // When last Arc drops, Container drops
        // When Container drops, HashMap drops
        // When HashMap drops, Py<T> drops
        // When Py<T> drops, Python refcount decrements
    }
}
```

**Rationale:**
- **Clear ownership:** Python owns data, Rust manages lifecycle
- **No memory leaks:** Python GC + Rust RAII handle cleanup
- **Thread-safe:** Arc ensures safe sharing
- **No manual memory management:** Compiler enforces correctness

**Trade-offs:**
- ✅ Memory safe (no use-after-free, no double-free)
- ✅ No manual refcount management
- ✅ Works with Python GC
- ❌ Circular references possible (user's responsibility)

### Decision 5: Performance Optimization Strategy

**Decision:** Optimize for common case, profile before micro-optimizing.

**Optimizations to Apply:**

1. **Minimize GIL acquisition:**
   ```rust
   // Good: Acquire GIL once, do all work
   fn resolve(&self, py: Python, type_key: &PyType) -> PyResult<PyObject> {
       // All work done with GIL held
   }

   // Bad: Multiple GIL acquisitions (v0.1 doesn't do this)
   ```

2. **Avoid unnecessary clones:**
   ```rust
   // Good: Return reference
   fn get_provider(&self, key: &TypeKey) -> Option<&Provider> {
       self.providers.read().unwrap().get(key)
   }

   // Bad: Clone Provider (Provider is cheap to clone, but unnecessary)
   ```

3. **Cache hot paths:**
   - Singleton cache hits: O(1) HashMap lookup, no object creation
   - Provider lookup: O(1) HashMap lookup

4. **Defer optimization:**
   - Don't pre-optimize error paths
   - Don't pre-optimize registration (rare operation)
   - Profile first, then optimize if needed

**Benchmarking Targets (from PRD):**
- Container creation: <1ms
- Singleton resolution (cached): <10μs
- Transient resolution (uncached): <100μs
- Registration: <100μs

**Trade-offs:**
- ✅ Simple, maintainable code
- ✅ Optimized for common case (resolution)
- ✅ Room for micro-optimizations later
- ❌ Not maximally optimized (but fast enough)

### Decision 6: Python API Surface

**Decision:** Expose minimal, focused API in v0.1.

**Public API (v0.1):**

```python
class Container:
    def __init__(self) -> None: ...

    def register_instance(self, type_: type, instance: Any) -> None: ...
    def register_class(self, type_: type, cls: type) -> None: ...
    def register_factory(self, type_: type, factory: Callable[[], Any]) -> None: ...

    def resolve(self, type_: type[T]) -> T: ...
```

**Private API (internal use only):**

```python
class _RustContainer:  # Exposed from _dioxide_core
    def __init__(self) -> None: ...
    def register_instance(self, py_type: type, instance: Any) -> None: ...
    def resolve(self, py_type: type) -> Any: ...
```

**Future API (v0.2+):**
- `Container.create_scope()` - Scoped containers
- `Container.shutdown()` - Lifecycle management
- `Container.register_value(name, value)` - Named value injection

**Rationale:**
- **Start minimal:** Only what's needed for v0.1 walking skeleton
- **Private Rust API:** `_dioxide_core` signals "don't use directly"
- **Python wrapper is public:** All user code goes through Python layer
- **Incremental expansion:** Add features in future versions

**Trade-offs:**
- ✅ Simple, focused API
- ✅ Easy to learn and use
- ✅ Room to add features without breaking changes
- ❌ Less powerful than mature DI frameworks (for now)

---

## Implementation Guidelines

### File Structure

```
src/
├── domain/
│   ├── mod.rs
│   ├── container.rs         # Pure Rust Container (no PyO3)
│   ├── provider.rs          # Pure Rust Provider (no PyO3)
│   └── error.rs             # ContainerError (no PyO3)
│
├── adapters/
│   ├── mod.rs
│   ├── python_container.rs  # #[pyclass] RustContainer
│   ├── python_types.rs      # Type conversion utilities
│   └── python_errors.rs     # Error conversion
│
└── lib.rs                   # #[pymodule] _dioxide_core
```

### PyO3 Module Definition

```rust
// src/lib.rs
use pyo3::prelude::*;

mod domain;
mod adapters;

use adapters::python_container::RustContainer;

#[pymodule]
fn _dioxide_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RustContainer>()?;
    Ok(())
}
```

### Testing Strategy

**Unit Tests (Rust):**
- Test domain layer in isolation (no PyO3)
- Fast, no Python required

**Integration Tests (PyO3):**
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::prepare_freethreaded_python;

    #[test]
    fn test_python_container_creation() {
        prepare_freethreaded_python();

        Python::with_gil(|py| {
            let container = RustContainer::new();
            assert!(container.inner.providers.read().unwrap().is_empty());
        });
    }
}
```

**BDD Tests (Python):**
```python
# tests/bdd/steps/container_steps.py
from dioxide import Container

@given("a container is created")
def container_created(context):
    context.container = Container()

@when("I resolve a dependency")
def resolve_dependency(context):
    context.result = context.container.resolve(MyService)
```

---

## Error Handling Examples

### Example 1: Dependency Not Registered

**User Code:**
```python
container = Container()
service = container.resolve(UserService)  # Not registered
```

**Error Output:**
```
KeyError: Dependency not registered: UserService

The container does not have a provider for type 'UserService'.

Possible solutions:
1. Register a provider:
   container.register_class(UserService, UserService)
2. Check for typos in the type name
```

### Example 2: Type Mismatch

**User Code:**
```python
container = Container()
container.register_instance(UserService, "not a UserService")  # Wrong type
```

**Error Output:**
```
TypeError: Instance must be of type UserService, got str
```

### Example 3: Duplicate Registration

**User Code:**
```python
container = Container()
container.register_class(UserService, UserService)
container.register_class(UserService, UserService)  # Duplicate!
```

**Error Output:**
```
ValueError: Duplicate provider registration: UserService

A provider for 'UserService' is already registered.

Hint: You cannot register the same type twice.
```

---

## Performance Considerations

### FFI Overhead

**Measured overhead per call:**
- Python → Rust function call: ~10-20ns
- GIL acquisition (if not held): ~50-100ns
- Type conversion (minimal with PyObject): ~5ns

**For our use case:**
- Registration: Called rarely (startup), overhead irrelevant
- Resolution: 10-20ns overhead on top of Rust logic (<100μs)
- Total: <1% overhead vs pure Rust

**Conclusion:** FFI overhead is negligible for our performance targets.

### Memory Overhead

**Per Container:**
- Rust Container: ~48 bytes
- Arc wrapper: ~16 bytes
- PyO3 wrapper: ~24 bytes
- Python wrapper: ~56 bytes
- **Total:** ~144 bytes per Container instance

**Per Provider:**
- Rust Provider: ~24 bytes
- PyObject reference: ~8 bytes
- HashMap entry: ~24 bytes
- **Total:** ~56 bytes per provider

**Conclusion:** Well within memory budget.

---

## Alternatives Considered

### Alternative 1: Pure Python Implementation

**Considered:** Write entire library in Python, no Rust.

**Rejected Because:**
- Performance would be 10-100x slower
- No compile-time type safety
- Core value proposition is Rust performance

### Alternative 2: Expose Rust API Directly

**Considered:** No Python wrapper, users call `_RustContainer` directly.

**Rejected Because:**
- Poor developer experience (no type hints, no validation)
- Harder to extend with Python-only features
- Less Pythonic

### Alternative 3: Use pyo3-asyncio for Async

**Considered:** Add async support immediately via pyo3-asyncio.

**Rejected Because:**
- v0.1 is synchronous only (scope control)
- Can add in v0.3 without architectural changes
- Premature complexity

### Alternative 4: Custom Python Extension Module (no PyO3)

**Considered:** Write CPython C API bindings manually.

**Rejected Because:**
- PyO3 is safer and more maintainable
- PyO3 handles Python version compatibility
- No significant performance benefit
- Much more code to write and maintain

---

## Risks and Mitigations

### Risk 1: PyO3 Version Incompatibility

**Risk:** PyO3 API changes in future versions.

**Mitigation:**
- Pin PyO3 version in Cargo.toml
- Test before upgrading
- PyO3 has good stability track record

### Risk 2: GIL Contention

**Risk:** GIL limits true parallelism.

**Mitigation:**
- Document that dioxide is not for CPU-bound parallel workloads
- Most Python code is I/O-bound anyway
- In future, can release GIL for some operations

### Risk 3: Memory Leaks from Circular References

**Risk:** Container holds references to objects that reference container.

**Mitigation:**
- Document this limitation
- Provide `Container.clear()` to break cycles
- Future: Add weak reference support

### Risk 4: Debugging Across FFI Boundary

**Risk:** Stack traces may be unclear across Rust/Python boundary.

**Mitigation:**
- Rich error messages reduce need for debugging
- PyO3 preserves Python tracebacks
- Add logging in debug builds

---

## Future Enhancements

### v0.2: Advanced Features

**Scoped Containers:**
```python
with container.create_scope() as scope:
    # Scoped instances
    request_service = scope.resolve(RequestService)
```

**Lifecycle Hooks:**
```python
container.register_class(
    Database,
    DatabaseImpl,
    on_create=lambda db: db.connect(),
    on_destroy=lambda db: db.disconnect(),
)
```

### v0.3: Async Support

```python
async def resolve_async(container: Container, type_: type[T]) -> T:
    return await container.resolve_async(type_)
```

### Future: Performance Optimizations

- Pre-compile dependency graphs
- Cache type lookups
- Lock-free data structures (if benchmarks justify)

---

## Decision Outcome

**We will implement PyO3 bindings with:**
- **Two-layer design:** Rust `_RustContainer` + Python `Container` wrapper
- **Minimal type conversion:** Use `PyObject` for zero-copy
- **Rich error messages:** Map Rust errors to Python exceptions
- **Clear ownership:** Python owns objects, Rust holds references
- **Focused API:** Minimal surface in v0.1, expand in v0.2+

**This design provides:**
- ✅ Pythonic developer experience
- ✅ Near-zero FFI overhead
- ✅ Memory safety (no leaks, no crashes)
- ✅ Excellent error messages
- ✅ Maintainable, testable code
- ✅ Foundation for future features

**Next Steps:**
1. Implement `RustContainer` in `src/adapters/python_container.rs`
2. Implement `Container` wrapper in `python/dioxide/container.py`
3. Write integration tests (Rust + Python)
4. Validate with BDD scenarios

---

## References

- [PyO3 User Guide](https://pyo3.rs/v0.20.0/)
- [PyO3 Performance Tips](https://pyo3.rs/v0.20.0/performance.html)
- [Python C API Documentation](https://docs.python.org/3/c-api/)
- ADR-001: Container Architecture
- docs/PRD.md - Technical requirements
- docs/RECOMMENDATIONS.md - Recommendation 8 (Error Handling)

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-21 | Product-Technical-Lead + Senior-Developer | Initial ADR |
