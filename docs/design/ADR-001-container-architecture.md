# ADR-001: Container Architecture

**Status:** Accepted
**Date:** 2025-10-21
**Deciders:** Product-Technical-Lead, Senior-Developer, Code-Reviewer
**Related Issues:** #10 (Container implementation)

---

## Context

We need to design the core `Container` struct in Rust that will serve as the foundation for dioxide's dependency injection functionality. This is the most critical architectural decision as it affects:

- Performance characteristics of the entire system
- Thread-safety guarantees
- Memory usage patterns
- Extensibility for future features
- Ease of integration with Python via PyO3

The container must:
1. Store registered providers (class, factory, instance)
2. Resolve dependencies by type
3. Be thread-safe (used in multi-threaded Python applications)
4. Have minimal memory overhead
5. Provide clear error messages
6. Be extensible for future features (scopes, lifecycle management)

---

## Decision

We will implement the `Container` using the following architecture:

### Core Design

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use pyo3::prelude::*;

/// Main dependency injection container
pub struct Container {
    /// Provider registry: maps Python type to Provider
    providers: Arc<RwLock<HashMap<TypeKey, Provider>>>,

    /// Singleton instance cache: maps Python type to cached instance
    singletons: Arc<RwLock<HashMap<TypeKey, PyObject>>>,
}

/// Type key for provider registry (Python type object)
#[derive(Debug, Clone, Hash, Eq, PartialEq)]
pub struct TypeKey {
    /// Python type object (class)
    py_type: Py<PyType>,
}

/// Provider variants for different creation strategies
pub enum Provider {
    /// Pre-created instance
    Instance(PyObject),

    /// Class to instantiate (calls __init__)
    Class(Py<PyType>),

    /// Factory function to invoke
    Factory(PyObject),
}
```

### Key Architectural Decisions

#### 1. Provider Registry: `HashMap<TypeKey, Provider>`

**Decision:** Use a HashMap keyed by Python type objects.

**Rationale:**
- **O(1) lookup** for provider resolution
- **Simple and predictable** - no complex indexing
- **Type-safe** - Python type objects are unique
- **Extensible** - easy to add metadata in future

**Alternatives Considered:**
- Vector with linear search: Too slow for large registries
- BTreeMap: Unnecessary ordering overhead
- Custom hash structure: Over-engineering for v0.1

**Trade-offs:**
- ✅ Fast lookup
- ✅ Simple implementation
- ❌ Hash collisions possible (but rare with type objects)
- ❌ No ordering (acceptable for our use case)

#### 2. Thread Safety: `Arc<RwLock<...>>`

**Decision:** Use `Arc<RwLock<HashMap>>` for thread-safe shared access.

**Rationale:**
- **Read-heavy workload:** Resolution far more common than registration
- **Multiple readers:** RwLock allows concurrent reads
- **Shared ownership:** Arc enables cloning container across threads
- **Python GIL consideration:** Python threading will acquire GIL anyway

**Alternatives Considered:**
- `Mutex<HashMap>`: Blocks readers during reads (poor performance)
- Lock-free structures (e.g., dashmap): Overkill for v0.1, harder to debug
- No synchronization: Unsafe, would cause data races

**Trade-offs:**
- ✅ Safe concurrent reads
- ✅ Standard Rust pattern (well-understood)
- ❌ Write locks block all access (acceptable - registration is rare)
- ❌ Small overhead vs. single-threaded (acceptable trade-off)

#### 3. Singleton Cache: Separate from Provider Registry

**Decision:** Keep singleton instances in a separate `HashMap`.

**Rationale:**
- **Separation of concerns:** Registration logic != caching logic
- **Lifecycle clarity:** Easy to see what's cached vs. what's registered
- **Memory efficiency:** Only cache singletons, not all providers
- **Future extensibility:** Can add per-scope caches later

**Alternatives Considered:**
- Cache in Provider enum: Mixes concerns, harder to reason about
- No cache (create each time): Defeats purpose of singletons
- Weak references: Complex, may lead to unexpected re-creation

**Trade-offs:**
- ✅ Clear separation of concerns
- ✅ Easy to implement and test
- ✅ Supports future scoped caching
- ❌ Two separate lookups (but both O(1))

#### 4. TypeKey: Wrapper Around Python Type

**Decision:** Create a newtype wrapper for Python type objects.

**Rationale:**
- **Type safety:** Can't accidentally use wrong key type
- **Implements Hash + Eq:** Required for HashMap
- **Future-proof:** Can add metadata (e.g., qualifiers, names) later
- **Clear intent:** TypeKey communicates purpose

**Implementation:**
```rust
impl TypeKey {
    pub fn new(py_type: Py<PyType>) -> Self {
        TypeKey { py_type }
    }

    pub fn as_py_type(&self) -> &Py<PyType> {
        &self.py_type
    }
}

impl Hash for TypeKey {
    fn hash<H: Hasher>(&self, state: &mut H) {
        // Hash the pointer to the Python type object
        // This is safe because type objects are immortal
        self.py_type.as_ptr().hash(state);
    }
}

impl PartialEq for TypeKey {
    fn eq(&self, other: &Self) -> bool {
        // Compare pointer equality (type objects are unique)
        self.py_type.as_ptr() == other.py_type.as_ptr()
    }
}
```

**Trade-offs:**
- ✅ Type-safe, can't mix up keys
- ✅ Extensible for future features (named tokens)
- ✅ Clear API surface
- ❌ Extra indirection (negligible cost)

#### 5. Error Handling Strategy

**Decision:** Use custom error types with context.

**Design:**
```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ContainerError {
    #[error("Dependency not registered: {type_name}\n\n\
             The container does not have a provider for type '{type_name}'.\n\n\
             Possible solutions:\n\
             1. Register a provider:\n   \
                container.register_class({type_name}, {type_name})\n\
             2. Check for typos in the type name")]
    DependencyNotRegistered {
        type_name: String,
    },

    #[error("Provider registration failed: {type_name}\n\
             Reason: {reason}")]
    ProviderRegistrationFailed {
        type_name: String,
        reason: String,
    },

    #[error("Dependency resolution failed: {type_name}\n\
             Reason: {reason}\n\
             Dependency chain: {chain}")]
    ResolutionFailed {
        type_name: String,
        reason: String,
        chain: String,
    },

    #[error("Duplicate provider registration: {type_name}\n\
             A provider for '{type_name}' is already registered.\n\n\
             Hint: You cannot register the same type twice.")]
    DuplicateRegistration {
        type_name: String,
    },
}
```

**Rationale:**
- **Actionable messages:** Tell user what's wrong AND how to fix
- **Context-rich:** Include type names, chains, suggestions
- **thiserror:** Standard Rust error handling library
- **PyO3 conversion:** Easy to convert to Python exceptions

**Trade-offs:**
- ✅ Excellent developer experience
- ✅ Easy to debug issues
- ✅ Standard Rust pattern
- ❌ Slightly larger binary (worth it for DX)

---

## Implementation Details

### Container Methods

```rust
impl Container {
    /// Create a new empty container
    pub fn new() -> Self {
        Container {
            providers: Arc::new(RwLock::new(HashMap::new())),
            singletons: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Register a provider for a type
    pub fn register(
        &self,
        type_key: TypeKey,
        provider: Provider,
    ) -> Result<(), ContainerError> {
        let mut providers = self.providers.write().unwrap();

        // Check for duplicate registration
        if providers.contains_key(&type_key) {
            return Err(ContainerError::DuplicateRegistration {
                type_name: type_key.type_name(),
            });
        }

        providers.insert(type_key, provider);
        Ok(())
    }

    /// Resolve a dependency by type
    pub fn resolve(
        &self,
        py: Python,
        type_key: &TypeKey,
    ) -> Result<PyObject, ContainerError> {
        // Check singleton cache first
        {
            let singletons = self.singletons.read().unwrap();
            if let Some(instance) = singletons.get(type_key) {
                return Ok(instance.clone_ref(py));
            }
        }

        // Get provider
        let provider = {
            let providers = self.providers.read().unwrap();
            providers
                .get(type_key)
                .cloned()
                .ok_or_else(|| ContainerError::DependencyNotRegistered {
                    type_name: type_key.type_name(),
                })?
        };

        // Create instance based on provider type
        let instance = match provider {
            Provider::Instance(obj) => obj.clone_ref(py),
            Provider::Class(cls) => {
                cls.call0(py)
                    .map_err(|e| ContainerError::ResolutionFailed {
                        type_name: type_key.type_name(),
                        reason: format!("Failed to instantiate class: {}", e),
                        chain: type_key.type_name(),
                    })?
                    .into()
            }
            Provider::Factory(factory) => {
                factory.call0(py)
                    .map_err(|e| ContainerError::ResolutionFailed {
                        type_name: type_key.type_name(),
                        reason: format!("Factory function failed: {}", e),
                        chain: type_key.type_name(),
                    })?
                    .into()
            }
        };

        Ok(instance)
    }
}
```

### Memory Management

**Python Object Ownership:**
- Use `Py<PyType>` for type objects (immortal, never freed)
- Use `PyObject` for instances (reference counted)
- Clone via `clone_ref(py)` to increment refcount
- Rust container doesn't own Python objects, just holds references

**Container Lifecycle:**
- Container lives as long as Arc refcount > 0
- Dropping container releases locks
- Cached singletons keep Python objects alive
- Python GC handles cleanup when container is dropped

**Thread Safety:**
- RwLock ensures safe concurrent access
- Python GIL ensures Python object safety
- No data races possible

---

## Performance Characteristics

### Time Complexity

| Operation | Best Case | Average Case | Worst Case |
|-----------|-----------|--------------|------------|
| register() | O(1) | O(1) | O(1) |
| resolve() - cached singleton | O(1) | O(1) | O(1) |
| resolve() - uncached | O(1) + creation | O(1) + creation | O(1) + creation |

### Memory Overhead

- **Per Container:** 2 × HashMap overhead (~48 bytes on 64-bit)
- **Per Provider:** HashMap entry (~24 bytes) + Provider enum (~24 bytes)
- **Per Singleton:** HashMap entry (~24 bytes) + Python object reference (~8 bytes)
- **Total:** ~50 bytes + ~48 bytes per registered provider

**Example:** Container with 100 providers = ~50 + (100 × 48) = ~4.9 KB

This is well within our <1KB per provider target.

### Concurrency Performance

- **Reads (resolve):** Fully concurrent, no blocking
- **Writes (register):** Exclusive lock, blocks all access
- **Expected ratio:** 99%+ reads, <1% writes
- **Conclusion:** RwLock is optimal for this workload

---

## Testing Strategy

### Unit Tests (Rust)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_container_new() {
        let container = Container::new();
        assert!(container.providers.read().unwrap().is_empty());
        assert!(container.singletons.read().unwrap().is_empty());
    }

    #[test]
    fn test_duplicate_registration_error() {
        let container = Container::new();
        let key = TypeKey::new(/* ... */);

        container.register(key.clone(), Provider::Instance(/* ... */)).unwrap();

        let result = container.register(key.clone(), Provider::Instance(/* ... */));
        assert!(matches!(result, Err(ContainerError::DuplicateRegistration { .. })));
    }

    // More tests...
}
```

### Integration Tests (Python via PyO3)

```python
def test_container_thread_safety():
    """Test concurrent access from multiple threads."""
    container = Container()
    container.register_instance(Config, config_instance)

    def resolve_config():
        for _ in range(100):
            config = container.resolve(Config)
            assert config is config_instance

    threads = [threading.Thread(target=resolve_config) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
```

---

## Future Considerations

### Scoped Containers (v0.2)

When adding scoped containers, we'll extend this architecture:

```rust
pub struct ScopedContainer {
    /// Parent container (for shared singletons)
    parent: Arc<Container>,

    /// Scoped instance cache
    scoped_instances: Arc<RwLock<HashMap<TypeKey, PyObject>>>,
}
```

This preserves our current design while adding scope hierarchy.

### Lifecycle Hooks (v0.2)

We can add lifecycle management without changing the core:

```rust
pub enum Provider {
    Instance(PyObject),
    Class(Py<PyType>),
    Factory(PyObject),

    // v0.2: Add lifecycle support
    LifecycleManaged {
        provider: Box<Provider>,
        on_create: Option<PyObject>,
        on_destroy: Option<PyObject>,
    },
}
```

### Named Tokens (v0.2)

TypeKey can be extended to support qualifiers:

```rust
#[derive(Debug, Clone, Hash, Eq, PartialEq)]
pub struct TypeKey {
    py_type: Py<PyType>,
    qualifier: Option<String>,  // v0.2: Named tokens
}
```

---

## Risks and Mitigations

### Risk 1: Lock Contention Under High Load

**Risk:** If many threads resolve simultaneously, RwLock read lock acquisition could slow down.

**Likelihood:** Low (Python GIL limits true parallelism)

**Mitigation:**
- Monitor lock contention in benchmarks
- Consider lock-free alternatives in v0.3 if needed
- For v0.1, RwLock is sufficient

### Risk 2: Memory Leaks from Circular References

**Risk:** Python objects in container could create reference cycles.

**Likelihood:** Medium (depends on user code)

**Mitigation:**
- Document that container holds strong references
- Provide `clear()` method to release all cached instances
- User must manage object lifecycles appropriately
- Future: Add weak reference support

### Risk 3: HashMap Hash Collisions

**Risk:** Type object pointer hash could collide.

**Likelihood:** Very Low (64-bit pointers, birthday paradox requires ~4 billion types)

**Mitigation:**
- Python type objects are unique per interpreter
- Hash collisions resolve via equality check
- Acceptable risk for v0.1

---

## Alternatives Considered

### Alternative 1: Single Mutex for Everything

**Considered:** Use `Mutex<ContainerState>` wrapping all state.

**Rejected Because:**
- Blocks readers during reads (poor performance)
- RwLock provides better concurrency

### Alternative 2: Lock-Free Concurrent HashMap

**Considered:** Use `dashmap` or similar lock-free structure.

**Rejected Because:**
- Over-engineering for v0.1
- Harder to debug
- Unclear performance benefit with Python GIL
- Can revisit in v0.3 if benchmarks show need

### Alternative 3: Per-Type Locks

**Considered:** Fine-grained locking per provider.

**Rejected Because:**
- Complex implementation
- Higher memory overhead
- Unnecessary for current workload
- Premature optimization

---

## Decision Outcome

**We will implement the Container with:**
- `HashMap<TypeKey, Provider>` for provider registry
- `Arc<RwLock<...>>` for thread safety
- Separate singleton cache
- Custom error types with actionable messages
- TypeKey newtype wrapper

**This design provides:**
- ✅ O(1) registration and resolution
- ✅ Thread-safe concurrent reads
- ✅ Clear separation of concerns
- ✅ Excellent error messages
- ✅ Extensible for future features
- ✅ Minimal memory overhead (~48 bytes per provider)

**Next Steps:**
1. Implement Container struct in `src/domain/container.rs`
2. Write comprehensive unit tests
3. Create PyO3 bindings in `src/adapters/python_container.rs`
4. Integration test with BDD scenarios

---

## References

- [Rust HashMap documentation](https://doc.rust-lang.org/std/collections/struct.HashMap.html)
- [Rust RwLock documentation](https://doc.rust-lang.org/std/sync/struct.RwLock.html)
- [PyO3 documentation](https://pyo3.rs/)
- [thiserror documentation](https://docs.rs/thiserror/)
- docs/PRD.md - Technical requirements
- docs/SPRINT_PLAN.md - Feature 1.1 (Container structure)

---

**Document History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-21 | Product-Technical-Lead + Senior-Developer | Initial ADR |
