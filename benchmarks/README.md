# Benchmark Comparison: dioxide vs dependency-injector

**Philosophy: NO SPIN. NO CHERRY-PICKING.**

This benchmark suite provides an honest comparison between dioxide and dependency-injector. If dependency-injector wins a benchmark, we report it. The goal is truth, not marketing.

## Framework Versions

| Framework | Version | Backend |
|-----------|---------|---------|
| dioxide | 0.2.1 | Rust (PyO3) |
| dependency-injector | 4.48.2 | Cython |

## Quick Start

```bash
# Run all benchmarks
uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-sort=mean

# Run specific category
uv run pytest benchmarks/compare_di_frameworks.py -k "simple_resolution" --benchmark-only

# Save results to JSON
uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-json=results.json

# Verbose output with statistics
uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only -v --benchmark-columns=min,max,mean,stddev,median,ops
```

## Methodology

### Fair Comparison Principles

1. **Equivalent Patterns**: Both frameworks use their idiomatic patterns
   - dioxide: `@service` decorator with auto-injection via type hints
   - dependency-injector: `DeclarativeContainer` with explicit provider wiring

2. **Same Warm-up**: Both get singleton warm-up before measurement

3. **Statistical Rigor**: pytest-benchmark runs multiple iterations and reports statistics

4. **No Optimization Tricks**: Neither framework gets special treatment

### What We Measure

Each benchmark measures **resolution time** - the time to call `container.resolve(Type)` or `container.provider()`.

For container startup, we measure the time to create and scan/wire the container.

## Benchmark Categories

### 1. Simple Resolution (Cached Singletons)

**What**: Time to resolve a cached singleton instance.

**Tests**:
- Singleton with 0 dependencies
- Singleton with 1 dependency
- Singleton with 2 dependencies
- Singleton with 3 dependencies

**Why it matters**: This is the most common operation in a running application. Most DI lookups are cache hits.

### 2. Deep Dependency Chains

**What**: Time to resolve through a deep dependency tree.

**Tests**:
- 5-level chain: A -> B -> C -> D -> E
- 10-level chain: deeper nesting

**Why it matters**: Real applications have deep dependency trees. Tests recursive resolution overhead.

### 3. Wide Dependency Graphs

**What**: Time to resolve a service with many direct dependencies.

**Tests**:
- Service with 10 dependencies
- Service with 20 dependencies

**Why it matters**: Some services (controllers, handlers) have many dependencies.

### 4. Concurrent Resolution

**What**: Time to resolve under concurrent load.

**Tests**:
- 100 concurrent resolutions
- 1000 concurrent resolutions

**Why it matters**: Web servers handle many requests concurrently. Thread safety has overhead.

### 5. Container Startup Time

**What**: Time to create and wire the container.

**Tests**:
- 10 components
- 50 components
- 100 components

**Why it matters**: Cold start time affects serverless and test setup.

**Known bias**: dioxide requires Rust FFI calls which may add overhead here.

### 6. Memory Usage

**What**: Memory footprint of container with resolved singletons.

**Tests**:
- 100 resolved singletons

**Why it matters**: Memory efficiency affects scalability.

**Note**: Uses tracemalloc, not pytest-benchmark. Results printed to stdout.

### 7. Real-World Simulation

**What**: Simulate typical web application usage patterns.

**Tests**:
- 1000 sequential "requests" (5 resolves each)
- 100 concurrent "requests"

**Why it matters**: Most representative of actual production use.

### 8. First Resolution (Cold Start)

**What**: Time for first resolution including instantiation.

**Tests**:
- First resolution of 5-level chain (fresh container each time)

**Why it matters**: Measures actual object creation, not just cache lookup.

## Interpreting Results

### pytest-benchmark Output

```
Name                                    Mean        StdDev      Median
--------------------------------------------------------------------
it_resolves_dioxide_singleton_no_deps   1.234 us    0.123 us    1.200 us
it_resolves_di_singleton_no_deps        1.567 us    0.234 us    1.500 us
```

- **Mean**: Average time per operation
- **StdDev**: Standard deviation (lower = more consistent)
- **Median**: Middle value (less affected by outliers)
- **ops**: Operations per second (higher = faster)

### What "Winning" Means

- **< 10% difference**: Effectively equivalent
- **10-50% difference**: Notable but may not matter in practice
- **> 50% difference**: Significant performance gap
- **> 2x difference**: Strong advantage

## Known Trade-offs

### dioxide Advantages (Expected)
- Rust backend for CPU-bound operations
- GIL-free operations in Rust
- Type safety enforced at resolution time

### dependency-injector Advantages (Expected)
- Simpler container startup (no FFI overhead)
- More mature optimization (been around longer)
- Cython provides good Python integration

## Running Your Own Benchmarks

### Add New Benchmark

1. Create a new `Describe*` class in `compare_di_frameworks.py`
2. Add paired tests: `it_*_dioxide_*` and `it_*_di_*`
3. Use identical setups and assertions

### Compare Specific Scenarios

```python
# Custom benchmark
def it_measures_your_scenario(self, benchmark):
    # Setup both frameworks
    # Run benchmark
    # Assert results
```

## Reproducing Results

For reproducibility:

1. Use same machine/environment
2. Close other applications
3. Run multiple times
4. Report hardware specs

```bash
# Report system info
python -c "import platform; print(platform.platform())"
python -c "import sys; print(f'Python {sys.version}')"
```

## Contributing

When adding benchmarks:

1. **Be fair**: Use idiomatic patterns for each framework
2. **Be honest**: Report all results, even unfavorable ones
3. **Be specific**: Document what each benchmark measures
4. **Be reproducible**: Include setup and teardown

## Results Summary

**Test Environment**: macOS Darwin 25.2.0, Python 3.14.0, Apple Silicon

### Overall Results Table

| Category | Winner | dioxide | dependency-injector | Speedup |
|----------|--------|---------|---------------------|---------|
| Simple Resolution (cached) | **d-i** | 114 ns | 69 ns | d-i 1.65x faster |
| Deep Chains (cached) | **d-i** | 114 ns | 69 ns | d-i 1.65x faster |
| Wide Graphs (cached) | **d-i** | 114 ns | 69 ns | d-i 1.65x faster |
| Concurrent (100) | **tie** | 3.6 ms | 3.7 ms | ~same |
| Concurrent (1000) | **dioxide** | 21.5 ms | 22.6 ms | dioxide 1.05x faster |
| Startup (10 components) | **d-i** | 762 us | 334 us | d-i 2.3x faster |
| Startup (50 components) | **d-i** | 2.3 ms | 1.5 ms | d-i 1.5x faster |
| Startup (100 components) | **d-i** | 4.4 ms | 3.0 ms | d-i 1.5x faster |
| Memory (100 singletons) | **dioxide** | 383 KB | 448 KB | dioxide 15% less |
| Real-World (1000 req) | **d-i** | 391 us | 275 us | d-i 1.4x faster |
| Real-World (100 concurrent) | **tie** | 8.5 ms | 8.5 ms | ~same |
| First Resolution (cold) | **d-i** | 316 us | 141 us | d-i 2.2x faster |

### Detailed Analysis

#### Category 1: Simple Resolution (Cached Singletons)

**WINNER: dependency-injector** - 1.65x faster for cached lookups

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 0 deps | 114 ns | 69 ns |
| 1 dep | 114 ns | 69 ns |
| 2 deps | 114 ns | 69 ns |
| 3 deps | 114 ns | 69 ns |

**Analysis**: dependency-injector's Cython-optimized singleton cache is faster than dioxide's PyO3 boundary crossing. Both are extremely fast (~70-115 ns), which is negligible for real applications.

#### Category 2: Deep Dependency Chains (Cached)

**WINNER: dependency-injector** - 1.65x faster

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 5-level | 115 ns | 69 ns |
| 10-level | 114 ns | 69 ns |

**Analysis**: Same pattern as simple resolution - these are cached lookups so chain depth doesn't affect performance once cached.

#### Category 3: Wide Dependency Graphs (Cached)

**WINNER: dependency-injector** - 1.65x faster

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 10 deps | 114 ns | 69 ns |
| 20 deps | 114 ns | 69 ns |

**Analysis**: Width doesn't matter for cached singletons - both return cached instances.

#### Category 4: Concurrent Resolution

**WINNER: tie/slight dioxide advantage at scale**

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 100 concurrent | 3.6 ms | 3.7 ms |
| 1000 concurrent | 21.5 ms | 22.6 ms |

**Analysis**: Nearly identical performance under concurrent load. Dioxide has a slight advantage (5%) at 1000 concurrent operations, possibly due to better Rust threading characteristics.

#### Category 5: Container Startup Time

**WINNER: dependency-injector** - 1.5-2.3x faster

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 10 components | 762 us | 334 us |
| 50 components | 2.3 ms | 1.5 ms |
| 100 components | 4.4 ms | 3.0 ms |

**Analysis**: dioxide's decorator-based registration and scan() process has more overhead than dependency-injector's declarative container definition. This is a known trade-off - dioxide prioritizes developer ergonomics (decorators, auto-discovery) over startup speed.

#### Category 6: Memory Usage

**WINNER: dioxide** - 15% less memory

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 100 singletons | 383 KB | 448 KB |

**Analysis**: Rust backend uses less memory than Cython. This advantage grows with application size.

#### Category 7: Real-World Simulation

**WINNER: dependency-injector for sequential, tie for concurrent**

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| 1000 sequential requests | 391 us | 275 us |
| 100 concurrent requests | 8.5 ms | 8.5 ms |

**Analysis**: For sequential operations, d-i's faster cache lookup matters. For concurrent workloads (more realistic for web servers), both frameworks perform identically.

#### Category 8: First Resolution (Cold Start)

**WINNER: dependency-injector** - 2.2x faster

| Test | dioxide | dependency-injector |
|------|---------|---------------------|
| First 5-level chain | 316 us | 141 us |

**Analysis**: dioxide's decorator-based setup and scan() process adds cold start overhead. This matters for:
- Serverless functions
- Test setup (creating fresh containers per test)
- CLI tools

### Key Takeaways

1. **For cached singleton lookups**: dependency-injector is ~1.65x faster, but both are extremely fast (70-114 ns). At these speeds, this difference is **negligible in practice**.

2. **For concurrent workloads**: Both frameworks perform identically. dioxide has a slight edge at scale.

3. **For memory efficiency**: dioxide uses 15% less memory.

4. **For startup time**: dependency-injector is 1.5-2.3x faster. This matters for:
   - Serverless (each invocation pays startup cost)
   - Test suites (many container setups)
   - CLI tools

5. **For developer experience**: dioxide provides:
   - Cleaner decorator-based API
   - Auto-discovery via scan()
   - Type-safe resolution
   - Profile-based configuration

   These DX benefits may justify the ~40ns slower cached lookups.

### When to Choose Each

**Choose dioxide when**:
- Memory efficiency matters (large applications)
- Clean hexagonal architecture API is important
- Profile-based adapter switching is needed
- You value developer ergonomics

**Choose dependency-injector when**:
- Startup time is critical (serverless, CLI)
- You have thousands of container instantiations
- Maximum raw performance for cached lookups is needed
- You prefer explicit provider wiring

### Honest Assessment

dependency-injector wins on pure speed for the most common operation (cached singleton lookup). However:

1. The absolute difference is ~40 nanoseconds - you'd need millions of resolutions per second for this to matter.

2. dioxide's advantages (memory, API, profiles) may outweigh the nanosecond-level performance difference for most applications.

3. For realistic web server workloads (concurrent requests), both frameworks perform identically.

**Bottom line**: If you're choosing between these frameworks, choose based on API preference and features, not raw performance. Both are fast enough for any practical use case.
