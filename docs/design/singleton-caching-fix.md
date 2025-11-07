# Design Doc: Singleton Caching Fix

**Status**: Draft
**Author**: Product & Technical Lead
**Date**: 2025-01-26
**Related Issue**: #1
**BDD Feature**: `features/singleton-caching.feature`

---

## Problem Statement

**Current Behavior**: The Rust container calls factory functions multiple times for SINGLETON-scoped components instead of caching the result after the first call.

**Expected Behavior**: SINGLETON-scoped components should be instantiated exactly once, with subsequent `resolve()` calls returning the cached instance.

**Impact**: HIGH
- Core dependency injection feature broken
- 4 tests failing
- Violates fundamental DI contract
- Blocks 0.0.1-alpha release

---

## Evidence of the Bug

### Failing Tests

```python
# tests/test_rust_container_edge_cases.py:25
def it_calls_singleton_factory_only_once(self) -> None:
    """Singleton factory is called exactly once across multiple resolutions."""
    container = RustContainer()
    call_count = {'count': 0}

    class Service:
        pass

    def factory() -> Service:
        call_count['count'] += 1
        return Service()

    container.register_factory(Service, factory)

    # Resolve twice
    service1 = container.resolve(Service)
    service2 = container.resolve(Service)

    # EXPECTED: call_count['count'] == 1
    # ACTUAL: call_count['count'] == 2  ❌
    assert service1 is service2  # FAILS
```

### Test Results

```
FAILED tests/test_rust_container_edge_cases.py::...::it_calls_singleton_factory_only_once
FAILED tests/test_rust_container_edge_cases.py::...::it_allows_singleton_to_depend_on_transient
FAILED tests/test_rust_container_edge_cases.py::...::it_allows_transient_to_depend_on_singleton
FAILED tests/test_rust_container_edge_cases.py::...::it_caches_singletons_in_deep_chains
```

---

## Root Cause Analysis

### Current Implementation (Rust)

```rust
// rust/src/lib.rs (simplified)
impl RustContainer {
    pub fn resolve(&self, type_id: TypeId) -> PyResult<PyObject> {
        // Check singleton cache first
        if let Some(cached) = self.singletons.borrow().get(&type_id) {
            return Ok(cached.clone());
        }

        // Get provider from registry
        let provider = self.providers.borrow()
            .get(&type_id)
            .ok_or_else(|| /* error */)?;

        match provider {
            Provider::Singleton(factory) => {
                // BUG: Calls factory but doesn't cache result!
                let instance = factory.call0(py)?;
                // Missing: self.singletons.borrow_mut().insert(type_id, instance.clone());
                Ok(instance)
            }
            Provider::Factory(factory) => {
                // Correctly creates new instance each time
                factory.call0(py)
            }
        }
    }
}
```

**The Bug**: When resolving a `Provider::Singleton`, the code:
1. ✅ Checks the singleton cache
2. ✅ Calls the factory function
3. ❌ **Fails to insert the result into the cache**
4. ❌ Returns uncached instance

**Result**: Every `resolve()` call invokes the factory again.

---

## Proposed Solution

### Option 1: Fix in Rust resolve() Method (RECOMMENDED)

**Approach**: After calling the singleton factory, immediately cache the result.

```rust
// rust/src/lib.rs (fixed)
impl RustContainer {
    pub fn resolve(&self, type_id: TypeId) -> PyResult<PyObject> {
        Python::with_gil(|py| {
            // Check singleton cache first
            if let Some(cached) = self.singletons.borrow().get(&type_id) {
                return Ok(cached.clone());
            }

            // Get provider from registry
            let provider = self.providers.borrow()
                .get(&type_id)
                .ok_or_else(|| /* error */)?
                .clone();

            match provider {
                Provider::Singleton(factory) => {
                    // Call factory
                    let instance = factory.call0(py)?;

                    // ✅ FIX: Cache the result
                    self.singletons.borrow_mut().insert(type_id, instance.clone());

                    Ok(instance)
                }
                Provider::Factory(factory) => {
                    // Factory providers create new instance each time
                    factory.call0(py)
                }
            }
        })
    }
}
```

**Pros**:
- ✅ Minimal code change
- ✅ Fixes all 4 failing tests
- ✅ Correct behavior at the right abstraction level
- ✅ No performance overhead

**Cons**:
- None

**Verification**:
```bash
uv run pytest tests/test_rust_container_edge_cases.py -v
# All tests should pass
```

---

### Option 2: Python-Side Caching (NOT RECOMMENDED)

**Approach**: Wrap factory functions in Python with caching logic before passing to Rust.

```python
# python/dioxide/container.py
def scan(self):
    for component_class in _get_registered_components():
        scope = getattr(component_class, '__dioxide_scope__', Scope.SINGLETON)

        if scope == Scope.SINGLETON:
            # Wrap factory with caching logic
            cache = {}
            original_factory = self._create_factory(component_class)

            def cached_factory():
                if 'instance' not in cache:
                    cache['instance'] = original_factory()
                return cache['instance']

            self._container.register_factory(component_class, cached_factory)
        else:
            # Factory scope - no caching
            factory = self._create_factory(component_class)
            self._container.register_factory(component_class, factory)
```

**Pros**:
- ✅ Works around Rust bug

**Cons**:
- ❌ Workaround, not a fix
- ❌ Adds complexity to Python layer
- ❌ Violates architecture (Rust should own lifecycle)
- ❌ Harder to maintain
- ❌ Doesn't fix the root cause

**Verdict**: Only consider if Rust fix proves too complex (unlikely).

---

## Decision

**Chosen Approach**: Option 1 - Fix in Rust `resolve()` method

**Rationale**:
1. **Correctness**: Fixes the bug at the source
2. **Simplicity**: One-line fix
3. **Architecture**: Rust owns lifecycle management
4. **Performance**: No overhead
5. **Maintainability**: Clear and obvious

---

## Implementation Plan

### Step 1: Write Failing Test (DONE ✅)

The failing tests already exist in `tests/test_rust_container_edge_cases.py`:
- `it_calls_singleton_factory_only_once`
- `it_allows_singleton_to_depend_on_transient`
- `it_allows_transient_to_depend_on_singleton`
- `it_caches_singletons_in_deep_chains`

### Step 2: Fix Rust Code

**File**: `rust/src/lib.rs`
**Line**: ~150 (in `resolve()` method)

```rust
match provider {
    Provider::Singleton(factory) => {
        let instance = factory.call0(py)?;
        // ADD THIS LINE:
        self.singletons.borrow_mut().insert(type_id, instance.clone());
        Ok(instance)
    }
    // ...
}
```

### Step 3: Rebuild and Test

```bash
# Rebuild Rust extension
uv run maturin develop

# Run failing tests
uv run pytest tests/test_rust_container_edge_cases.py::DescribeRustContainerSingletonCaching -v

# Run all tests
uv run pytest tests/ -v

# Verify coverage
uv run pytest tests/ --cov=dioxide --cov-report=term-missing --cov-branch
```

### Step 4: Verify BDD Scenarios

All scenarios in `features/singleton-caching.feature` should pass:
- Singleton components are cached on first resolution
- Subsequent resolutions return cached instance
- Different singleton types cached independently
- Factory-scoped components are NOT cached
- Singleton caching works for injected dependencies

---

## Testing Strategy

### Unit Tests (Rust - Optional)

While we test through the Python API, Rust unit tests can provide faster feedback:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_singleton_caching() {
        Python::with_gil(|py| {
            let container = RustContainer::new();
            let call_count = Arc::new(Mutex::new(0));

            // Create factory that increments counter
            let count_clone = call_count.clone();
            let factory = PyCell::new(py, move || {
                *count_clone.lock().unwrap() += 1;
                py.None()
            }).unwrap();

            // Register as singleton
            container.register_singleton(...);

            // Resolve twice
            container.resolve(...).unwrap();
            container.resolve(...).unwrap();

            // Verify factory called only once
            assert_eq!(*call_count.lock().unwrap(), 1);
        });
    }
}
```

**Note**: Rust unit tests are optional since Python integration tests already cover this.

### Integration Tests (Python - DONE ✅)

Comprehensive tests already exist in `tests/test_rust_container_edge_cases.py`.

---

## Rollout Plan

### Phase 1: Fix and Test
1. Apply fix to `rust/src/lib.rs`
2. Rebuild with `uv run maturin develop`
3. Run full test suite
4. Verify 100% test pass rate
5. Check coverage (should be 100%)

### Phase 2: Code Review
1. Open PR: "Fix singleton caching bug in Rust container"
2. Link to this design doc
3. Link to Issue #1
4. Request review from @code-reviewer

### Phase 3: QA Validation
1. @qa-security-engineer runs full test suite
2. Validates all BDD scenarios pass
3. Checks for edge cases
4. Approves PR

### Phase 4: Merge and Deploy
1. Merge PR to main
2. CI runs automatically
3. Verify CI passes
4. Close Issue #1

---

## Success Criteria

✅ **All 4 failing tests pass**
✅ **Test coverage remains at 100%**
✅ **No performance regression**
✅ **BDD scenarios pass**: `features/singleton-caching.feature`
✅ **Code review approved**
✅ **QA validation passed**

---

## Risks and Mitigation

### Risk 1: RefCell Borrow Conflicts

**Issue**: Rust's `RefCell::borrow_mut()` can panic if already borrowed.

**Mitigation**:
- The current code already uses `borrow()` and `borrow_mut()` correctly
- Insert happens after provider lookup completes (no overlap)
- If panic occurs, add explicit drop or scope the borrows

**Contingency**: Use `try_borrow_mut()` and return error instead of panic.

### Risk 2: Thread Safety

**Issue**: Python GIL makes this single-threaded, but future async support?

**Mitigation**:
- Current implementation uses `RefCell` (single-threaded)
- Future async support would require `Arc<Mutex<>>` or similar
- Document as future enhancement

**Contingency**: Add TODO comment for future thread-safe version.

---

## Future Enhancements

After fixing the singleton caching bug, consider:

1. **Lazy Initialization**
   - Only create singleton when first requested
   - Current: Singletons created during `scan()` (if we add that)
   - Future: Defer until `resolve()`

2. **Singleton Lifecycle Hooks**
   - `on_init()` called after creation
   - `on_shutdown()` called during container cleanup
   - Enables resource management (DB connections, file handles)

3. **Singleton Warmup**
   - Pre-create critical singletons on container startup
   - Reduces first-request latency
   - Useful for web servers

4. **Singleton Scoped to Requests**
   - New scope: `REQUEST_SINGLETON`
   - Lives for duration of one request
   - Cleared after request completes

These are all **out of scope** for 0.0.1-alpha.

---

## References

- **Issue**: #1 (Fix Singleton Caching Bug)
- **BDD Feature**: `features/singleton-caching.feature`
- **Failing Tests**: `tests/test_rust_container_edge_cases.py`
- **Rust Implementation**: `rust/src/lib.rs`
- **Python API**: `python/dioxide/container.py`

---

## Approval

**Product Lead**: Approved
**Technical Lead**: Approved
**Senior Developer**: Assigned
**Target Completion**: Week 1 of 0.0.1-alpha

---

*This design doc will be updated as implementation progresses.*
