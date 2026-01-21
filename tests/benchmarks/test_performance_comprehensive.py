"""Comprehensive performance benchmarks justifying Rust backend.

This module provides a comprehensive benchmark suite to demonstrate where
the Rust-backed container provides performance benefits over pure Python
implementations. These benchmarks justify the Rust dependency to developers
evaluating dioxide.

Performance Characteristics Measured:
=====================================

1. **Resolution Performance at Scale**
   - Single resolution (N=1): Baseline operation
   - Bulk resolution (N=100, 1000, 10000): Demonstrates O(1) resolution

2. **Dependency Graph Complexity**
   - Shallow dependencies (depth=1): Direct injection
   - Deep dependencies (depth=5, 10): Transitive resolution
   - Validates graph traversal efficiency

3. **Wide Dependencies**
   - Services with many direct dependencies (N=5, 10, 20)
   - Tests parameter collection overhead

4. **Registration/Scan Performance**
   - Measuring scan() time for N adapters/services
   - Registration overhead per component

Why Rust Matters:
=================

The Rust backend (via PyO3) provides:
- O(1) singleton lookup (hash-based instance cache)
- Efficient graph representation (petgraph)
- Zero-copy resolution metadata
- Compile-time memory safety guarantees

These benchmarks quantify the benefits at realistic application scales.

Running Benchmarks:
==================

    # Run all benchmarks
    uv run pytest tests/benchmarks/test_performance_comprehensive.py --benchmark-only

    # Compare with specific rounds
    uv run pytest tests/benchmarks/test_performance_comprehensive.py --benchmark-only --benchmark-min-rounds=100

    # Save benchmark results
    uv run pytest tests/benchmarks/test_performance_comprehensive.py \\
        --benchmark-only --benchmark-json=benchmark_results.json
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    _clear_registry,
    adapter,
    service,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

# ============================================================================
# Dynamic Component Factories
# ============================================================================


def create_protocol(name: str) -> type[Any]:
    """Dynamically create a Protocol class for benchmarking."""
    # Dynamic Protocol creation for benchmarking purposes
    protocol: type[Any] = type(
        name,
        (Protocol,),  # type: ignore[arg-type]
        {'execute': lambda self: None},
    )
    return protocol


def create_adapter_for_protocol(
    protocol: type[Any],
    adapter_name: str,
    profile: str = 'test',
) -> type[Any]:
    """Create an adapter implementation for a protocol."""

    class DynamicAdapter:
        def execute(self) -> None:
            pass

    DynamicAdapter.__name__ = adapter_name
    DynamicAdapter.__qualname__ = adapter_name

    # Apply the adapter decorator
    decorated = adapter.for_(protocol, profile=profile)(DynamicAdapter)
    return decorated


def create_service_with_no_deps(name: str) -> type[Any]:
    """Create a service with no dependencies."""

    class DynamicService:
        def execute(self) -> None:
            pass

    DynamicService.__name__ = name
    DynamicService.__qualname__ = name

    decorated = service(DynamicService)
    return decorated


def create_deep_dependency_chain(depth: int) -> tuple[list[type[Any]], type[Any]]:
    """Create a chain of services A -> B -> C -> ... of given depth.

    Returns:
        Tuple of (all_services, root_service) where root_service depends on
        all others transitively (root -> ... -> leaf).
    """
    services: list[type[Any]] = []

    # Create leaf service first (no dependencies)
    leaf_cls = create_service_with_no_deps(f'DepthLeaf_{depth}')
    services.append(leaf_cls)

    if depth == 1:
        return services, leaf_cls

    # Build chain backwards from leaf to root
    previous_cls = leaf_cls
    for i in range(depth - 1, 0, -1):
        # Capture the dependency type in a factory function
        dep_type = previous_cls

        # Create new class dynamically with proper __init__ and annotations
        cls_name = f'Depth{i}_of_{depth}'

        # Create a new class with proper dependency injection
        # We need to set __init__.__annotations__ properly for the container
        new_cls = type(cls_name, (), {'execute': lambda self: None})

        # Create __init__ that accepts the dependency
        def make_init_for(dep_cls: type[Any]) -> Any:
            def init_fn(self: Any, dep: Any) -> None:
                self.dep = dep

            # Set annotations on the function itself
            init_fn.__annotations__ = {'dep': dep_cls, 'return': None}
            return init_fn

        new_cls.__init__ = make_init_for(dep_type)  # type: ignore[misc]

        decorated: type[Any] = service(new_cls)
        services.insert(0, decorated)
        previous_cls = decorated

    return services, services[0]


def create_wide_dependency_service(
    num_deps: int,
) -> tuple[list[type[Any]], type[Any]]:
    """Create a service with N direct dependencies.

    Returns:
        Tuple of (dependency_services, main_service)
    """
    import inspect
    import types

    dep_services: list[type[Any]] = []

    # Create N independent services
    for i in range(num_deps):
        dep_cls = create_service_with_no_deps(f'WideDep_{i}_of_{num_deps}')
        dep_services.append(dep_cls)

    # Create main service that depends on all of them
    param_names = [f'dep_{i}' for i in range(num_deps)]

    def make_wide_init(names: list[str], deps: list[type[Any]]) -> Any:
        # Create init function that accepts keyword args and stores them
        def init_fn(self: Any, **kwargs: Any) -> None:
            for name in names:
                if name in kwargs:
                    setattr(self, name, kwargs[name])

        # Build proper signature with typed parameters
        params = [inspect.Parameter('self', inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        for i, dep_cls in enumerate(deps):
            params.append(
                inspect.Parameter(
                    f'dep_{i}',
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=dep_cls,
                )
            )

        # Create new function with custom globals that include the dependency types
        custom_globals = dict(init_fn.__globals__)
        for i, dep_cls in enumerate(deps):
            custom_globals[f'dep_{i}'] = dep_cls

        new_init = types.FunctionType(
            init_fn.__code__,
            custom_globals,
            init_fn.__name__,
            init_fn.__defaults__,
            init_fn.__closure__,
        )
        new_init.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]

        # Set annotations for get_type_hints() to work
        init_annotations: dict[str, type[Any]] = {'return': type(None)}
        for i, dep_cls in enumerate(deps):
            init_annotations[f'dep_{i}'] = dep_cls
        new_init.__annotations__ = init_annotations

        return new_init

    init_fn = make_wide_init(param_names, dep_services)

    cls_name = f'WideService_{num_deps}_deps'
    wide_cls = type(cls_name, (), {'execute': lambda self: None})
    wide_cls.__init__ = init_fn  # type: ignore[misc]

    decorated: type[Any] = service(wide_cls)
    return dep_services, decorated


def create_n_independent_services(n: int) -> list[type[Any]]:
    """Create N independent services with no dependencies."""
    services = []
    for i in range(n):
        svc = create_service_with_no_deps(f'IndependentService_{i}')
        services.append(svc)
    return services


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def clean_registry() -> Any:
    """Clean registry before and after each test."""
    _clear_registry()
    yield
    _clear_registry()


# ============================================================================
# Benchmark: Resolution Performance at Scale
# ============================================================================


class DescribeBulkResolutionPerformance:
    """Benchmarks demonstrating O(1) singleton resolution at scale.

    These benchmarks show that resolution time is constant regardless of
    how many times resolve() is called, proving efficient singleton caching.
    """

    def it_resolves_single_service_baseline(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Baseline: single resolution of a simple service.

        This establishes the baseline cost of a single resolve() call.
        Target: < 10 microseconds
        """
        svc_cls = create_service_with_no_deps('SingleBaseline')
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, svc_cls)

        assert result is not None

    def it_resolves_100_times_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve the same singleton 100 times.

        Should be ~100x the baseline (linear), but each resolution is O(1).
        Tests singleton cache hit performance.
        """
        svc_cls = create_service_with_no_deps('Bulk100')
        container = Container()
        container.scan(profile=Profile.TEST)

        # Warm up - ensure singleton exists
        container.resolve(svc_cls)

        def resolve_100_times() -> Any:
            result = None
            for _ in range(100):
                result = container.resolve(svc_cls)
            return result

        result = benchmark(resolve_100_times)
        assert result is not None

    def it_resolves_1000_times_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve the same singleton 1000 times.

        Tests that resolution scales linearly (O(1) per call).
        """
        svc_cls = create_service_with_no_deps('Bulk1000')
        container = Container()
        container.scan(profile=Profile.TEST)

        # Warm up
        container.resolve(svc_cls)

        def resolve_1000_times() -> Any:
            result = None
            for _ in range(1000):
                result = container.resolve(svc_cls)
            return result

        result = benchmark(resolve_1000_times)
        assert result is not None

    def it_resolves_10000_times_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve the same singleton 10000 times.

        Stress test for cache hit performance at scale.
        Target: < 1ms total for 10000 resolutions (< 100ns each)
        """
        svc_cls = create_service_with_no_deps('Bulk10000')
        container = Container()
        container.scan(profile=Profile.TEST)

        # Warm up
        container.resolve(svc_cls)

        def resolve_10000_times() -> Any:
            result = None
            for _ in range(10000):
                result = container.resolve(svc_cls)
            return result

        result = benchmark(resolve_10000_times)
        assert result is not None


# ============================================================================
# Benchmark: Dependency Depth Performance
# ============================================================================


class DescribeDependencyDepthPerformance:
    """Benchmarks for dependency graph traversal at various depths.

    These benchmarks test how resolution time scales with dependency
    chain depth. Efficient graph traversal is critical for real apps.
    """

    def it_resolves_depth_1_quickly(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with depth=1 (no transitive dependencies).

        Baseline for dependency graph traversal.
        """
        _services, root_svc = create_deep_dependency_chain(1)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, root_svc)

        assert result is not None

    def it_resolves_depth_5_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with depth=5 (A->B->C->D->E).

        Tests transitive dependency resolution at moderate depth.
        Common in layered architecture (Controller->Service->Repository->...).
        """
        _services, root_svc = create_deep_dependency_chain(5)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, root_svc)

        assert result is not None
        # Verify chain is correct
        current = result
        depth = 1
        while hasattr(current, 'dep'):
            current = current.dep
            depth += 1
        assert depth == 5

    def it_resolves_depth_10_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with depth=10 (deep transitive chain).

        Tests that deep dependency chains don't degrade performance
        significantly due to efficient topological sorting.
        """
        _services, root_svc = create_deep_dependency_chain(10)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, root_svc)

        assert result is not None
        # Verify chain is correct
        current = result
        depth = 1
        while hasattr(current, 'dep'):
            current = current.dep
            depth += 1
        assert depth == 10


# ============================================================================
# Benchmark: Wide Dependencies Performance
# ============================================================================


class DescribeWideDependencyPerformance:
    """Benchmarks for services with many direct dependencies.

    Tests parameter collection and injection overhead when a service
    depends on many other services directly.
    """

    def it_resolves_5_direct_deps_quickly(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with 5 direct dependencies.

        Common in application services that orchestrate multiple ports.
        """
        _deps, main_svc = create_wide_dependency_service(5)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, main_svc)

        assert result is not None
        assert hasattr(result, 'dep_0')
        assert hasattr(result, 'dep_4')

    def it_resolves_10_direct_deps_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with 10 direct dependencies.

        Tests parameter collection at larger scale.
        """
        _deps, main_svc = create_wide_dependency_service(10)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, main_svc)

        assert result is not None
        assert hasattr(result, 'dep_0')
        assert hasattr(result, 'dep_9')

    def it_resolves_20_direct_deps_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Resolve a service with 20 direct dependencies.

        Stress test for wide dependency graphs.
        While 20 deps is unusual, it tests the upper bounds.
        """
        _deps, main_svc = create_wide_dependency_service(20)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, main_svc)

        assert result is not None
        assert hasattr(result, 'dep_0')
        assert hasattr(result, 'dep_19')


# ============================================================================
# Benchmark: Scan/Registration Performance
# ============================================================================


class DescribeScanPerformance:
    """Benchmarks for container.scan() with varying component counts.

    Registration performance matters for application startup time.
    """

    def it_scans_10_services_quickly(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Scan container with 10 services.

        Baseline for small applications.
        Target: < 5ms
        """
        services = create_n_independent_services(10)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        container = benchmark(create_and_scan)

        # Verify all services are resolvable
        for svc in services:
            assert container.resolve(svc) is not None

    def it_scans_50_services_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Scan container with 50 services.

        Medium-sized application (microservice scale).
        Target: < 25ms
        """
        services = create_n_independent_services(50)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        container = benchmark(create_and_scan)

        # Spot-check some services
        assert container.resolve(services[0]) is not None
        assert container.resolve(services[25]) is not None
        assert container.resolve(services[49]) is not None

    def it_scans_100_services_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Scan container with 100 services.

        Large application scale.
        Target: < 50ms
        """
        services = create_n_independent_services(100)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        container = benchmark(create_and_scan)

        # Spot-check some services
        assert container.resolve(services[0]) is not None
        assert container.resolve(services[50]) is not None
        assert container.resolve(services[99]) is not None

    def it_scans_200_services_efficiently(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Scan container with 200 services.

        Monolith-scale application.
        Target: < 100ms
        """
        services = create_n_independent_services(200)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        container = benchmark(create_and_scan)

        # Spot-check some services
        assert container.resolve(services[0]) is not None
        assert container.resolve(services[100]) is not None
        assert container.resolve(services[199]) is not None


# ============================================================================
# Benchmark: Cold vs Warm Resolution
# ============================================================================


class DescribeColdVsWarmResolution:
    """Benchmarks comparing first resolution (cold) vs subsequent (warm).

    Demonstrates singleton caching effectiveness.
    """

    def it_performs_cold_resolution(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """First-time resolution (singleton creation).

        Includes instantiation cost.
        """

        def cold_resolve() -> Any:
            # Fresh registry and container each time
            _clear_registry()
            svc = create_service_with_no_deps('ColdService')
            container = Container()
            container.scan(profile=Profile.TEST)
            return container.resolve(svc)

        result = benchmark(cold_resolve)
        assert result is not None

    def it_performs_warm_resolution(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Subsequent resolution (cached singleton lookup).

        Should be significantly faster than cold.
        """
        svc = create_service_with_no_deps('WarmService')
        container = Container()
        container.scan(profile=Profile.TEST)

        # Warm up the cache
        container.resolve(svc)

        result = benchmark(container.resolve, svc)
        assert result is not None


# ============================================================================
# Benchmark: Real-World Scenario
# ============================================================================


class DescribeRealWorldScenario:
    """Benchmark simulating realistic application patterns.

    Tests a dependency graph representative of actual applications
    with mixed depths and widths.
    """

    def it_resolves_realistic_application_graph(
        self,
        benchmark: BenchmarkFixture,
    ) -> None:
        """Simulate a realistic application with mixed dependencies.

        Structure:
        - 3 ports with adapters (Email, Database, Cache)
        - 5 services with various dependency patterns
        - Mix of deep and wide dependencies

        This represents a typical microservice architecture.
        """
        # Create ports
        email_port = create_protocol('EmailPortRealistic')
        db_port = create_protocol('DatabasePortRealistic')
        cache_port = create_protocol('CachePortRealistic')

        # Create adapters
        create_adapter_for_protocol(email_port, 'EmailAdapterRealistic')
        create_adapter_for_protocol(db_port, 'DatabaseAdapterRealistic')
        create_adapter_for_protocol(cache_port, 'CacheAdapterRealistic')

        # Create services with realistic dependencies

        # UserRepository - depends on db and cache
        @service
        class UserRepositoryRealistic:
            def __init__(self, db: db_port, cache: cache_port) -> None:  # type: ignore[valid-type]
                self.db = db
                self.cache = cache

        # NotificationService - depends on email
        @service
        class NotificationServiceRealistic:
            def __init__(self, email: email_port) -> None:  # type: ignore[valid-type]
                self.email = email

        # UserService - depends on repo and notifications
        @service
        class UserServiceRealistic:
            def __init__(
                self,
                repo: UserRepositoryRealistic,
                notifications: NotificationServiceRealistic,
            ) -> None:
                self.repo = repo
                self.notifications = notifications

        # OrderService - depends on user service and cache
        @service
        class OrderServiceRealistic:
            def __init__(
                self,
                users: UserServiceRealistic,
                cache: cache_port,  # type: ignore[valid-type]
            ) -> None:
                self.users = users
                self.cache = cache

        # Application facade - top-level entry point
        @service
        class ApplicationFacadeRealistic:
            def __init__(
                self,
                users: UserServiceRealistic,
                orders: OrderServiceRealistic,
                notifications: NotificationServiceRealistic,
            ) -> None:
                self.users = users
                self.orders = orders
                self.notifications = notifications

        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, ApplicationFacadeRealistic)

        # Verify correct wiring
        assert result is not None
        assert result.users is not None
        assert result.orders is not None
        assert result.notifications is not None
        assert result.users.repo.db is not None
        assert result.orders.cache is not None
