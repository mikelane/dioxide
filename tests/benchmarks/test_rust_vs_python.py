"""Benchmark suite comparing Rust-backed vs pure Python container performance.

This module provides fair, reproducible benchmarks that compare dioxide's
Rust-backed container (via PyO3) against a pure Python reference implementation.
The goal is to quantify where Rust provides measurable value and where the
Python overhead dominates regardless.

Benchmark Categories:
    1. Container creation time (empty, 10, 100, 1000 types)
    2. Resolution time (singleton vs factory, shallow vs deep chains)
    3. Scan time (small vs large module trees)
    4. Memory usage comparison (non-benchmark, single measurement)
    5. Concurrent resolution correctness and throughput

Running:
    uv run pytest tests/benchmarks/test_rust_vs_python.py --benchmark-only
    uv run pytest tests/benchmarks/test_rust_vs_python.py --benchmark-only --benchmark-json=results.json
    uv run pytest tests/benchmarks/test_rust_vs_python.py -k memory  # memory tests only
"""

from __future__ import annotations

import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from typing import (
    TYPE_CHECKING,
    Any,
)

import pytest

from dioxide import (
    Container,
    Profile,
    _clear_registry,
    service,
)
from tests.benchmarks.pure_python_container import PurePythonContainer

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def clean_registry() -> Any:
    _clear_registry()
    yield
    _clear_registry()


# ============================================================================
# Helpers: Dynamic component creation
# ============================================================================


def create_independent_services(n: int) -> list[type[Any]]:
    """Create N independent @service classes with no dependencies."""
    services = []
    for i in range(n):
        cls = type(f'BenchSvc_{n}_{i}', (), {'run': lambda self: None})
        decorated: type[Any] = service(cls)
        services.append(decorated)
    return services


def create_dependency_chain(depth: int) -> tuple[list[type[Any]], type[Any]]:
    """Create a linear dependency chain of given depth: A -> B -> C -> ...

    Returns (all_services, root_service).
    """
    leaf = type(f'ChainLeaf_{depth}', (), {'run': lambda self: None})
    decorated_leaf: type[Any] = service(leaf)
    chain = [decorated_leaf]

    if depth == 1:
        return chain, decorated_leaf

    previous = decorated_leaf
    for level in range(depth - 1, 0, -1):
        dep_type = previous

        def make_init(dep_cls: type[Any]) -> Any:
            def init_fn(self: Any, dep: Any) -> None:
                self.dep = dep

            init_fn.__annotations__ = {'dep': dep_cls, 'return': None}
            return init_fn

        cls = type(f'ChainNode_{depth}_{level}', (), {'run': lambda self: None})
        cls.__init__ = make_init(dep_type)  # type: ignore[misc]
        decorated: type[Any] = service(cls)
        chain.insert(0, decorated)
        previous = decorated

    return chain, chain[0]


def build_python_container_with_services(services: list[type[Any]]) -> PurePythonContainer:
    """Build a pure Python container pre-loaded with given services."""
    container = PurePythonContainer()
    for svc in services:
        container.register_singleton(svc, svc)
    return container


# ============================================================================
# Benchmark: Container Creation Time
# ============================================================================


class DescribeContainerCreationComparison:
    """Compare container creation time between Rust and pure Python."""

    def it_creates_empty_rust_container(self, benchmark: BenchmarkFixture) -> None:
        result = benchmark(Container)
        assert result is not None

    def it_creates_empty_python_container(self, benchmark: BenchmarkFixture) -> None:
        result = benchmark(PurePythonContainer)
        assert result is not None

    def it_creates_rust_container_with_10_types(self, benchmark: BenchmarkFixture) -> None:
        create_independent_services(10)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        result = benchmark(create_and_scan)
        assert result is not None

    def it_creates_python_container_with_10_types(self, benchmark: BenchmarkFixture) -> None:
        services = create_independent_services(10)

        def create_and_load() -> PurePythonContainer:
            return build_python_container_with_services(services)

        result = benchmark(create_and_load)
        assert result is not None

    def it_creates_rust_container_with_100_types(self, benchmark: BenchmarkFixture) -> None:
        create_independent_services(100)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        result = benchmark(create_and_scan)
        assert result is not None

    def it_creates_python_container_with_100_types(self, benchmark: BenchmarkFixture) -> None:
        services = create_independent_services(100)

        def create_and_load() -> PurePythonContainer:
            return build_python_container_with_services(services)

        result = benchmark(create_and_load)
        assert result is not None

    def it_creates_rust_container_with_1000_types(self, benchmark: BenchmarkFixture) -> None:
        create_independent_services(1000)

        def create_and_scan() -> Container:
            container = Container()
            container.scan(profile=Profile.TEST)
            return container

        result = benchmark(create_and_scan)
        assert result is not None

    def it_creates_python_container_with_1000_types(self, benchmark: BenchmarkFixture) -> None:
        services = create_independent_services(1000)

        def create_and_load() -> PurePythonContainer:
            return build_python_container_with_services(services)

        result = benchmark(create_and_load)
        assert result is not None


# ============================================================================
# Benchmark: Singleton Resolution Speed
# ============================================================================


class DescribeSingletonResolutionComparison:
    """Compare singleton resolution (cached lookup) between Rust and Python."""

    def it_resolves_singleton_via_rust(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        container = Container()
        container.scan(profile=Profile.TEST)
        container.resolve(svc)

        result = benchmark(container.resolve, svc)
        assert result is not None

    def it_resolves_singleton_via_python(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        py_container = build_python_container_with_services([svc])
        py_container.resolve(svc)

        result = benchmark(py_container.resolve, svc)
        assert result is not None

    def it_resolves_10000_singletons_via_rust(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        container = Container()
        container.scan(profile=Profile.TEST)
        container.resolve(svc)

        def resolve_n() -> Any:
            result = None
            for _ in range(10_000):
                result = container.resolve(svc)
            return result

        result = benchmark(resolve_n)
        assert result is not None

    def it_resolves_10000_singletons_via_python(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        py_container = build_python_container_with_services([svc])
        py_container.resolve(svc)

        def resolve_n() -> Any:
            result = None
            for _ in range(10_000):
                result = py_container.resolve(svc)
            return result

        result = benchmark(resolve_n)
        assert result is not None


# ============================================================================
# Benchmark: Factory Resolution Speed
# ============================================================================


class DescribeFactoryResolutionComparison:
    """Compare factory (new instance each time) resolution."""

    def it_resolves_factory_via_rust(self, benchmark: BenchmarkFixture) -> None:
        cls = type('FactoryRust', (), {'run': lambda self: None})
        container = Container()
        container.register_factory(cls, cls)

        result = benchmark(container.resolve, cls)
        assert result is not None

    def it_resolves_factory_via_python(self, benchmark: BenchmarkFixture) -> None:
        cls = type('FactoryPy', (), {'run': lambda self: None})
        py_container = PurePythonContainer()
        py_container.register_factory(cls, cls)

        result = benchmark(py_container.resolve, cls)
        assert result is not None


# ============================================================================
# Benchmark: Dependency Chain Resolution
# ============================================================================


class DescribeDependencyChainComparison:
    """Compare resolution of deep dependency chains."""

    def it_resolves_depth_4_chain_via_rust(self, benchmark: BenchmarkFixture) -> None:
        _all_svcs, root = create_dependency_chain(4)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, root)
        assert result is not None

    def it_resolves_depth_4_chain_via_python(self, benchmark: BenchmarkFixture) -> None:
        all_svcs, root = create_dependency_chain(4)
        py_container = PurePythonContainer()
        for svc in reversed(all_svcs):
            py_container.register_singleton_with_deps(svc)

        result = benchmark(py_container.resolve, root)
        assert result is not None

    def it_resolves_depth_8_chain_via_rust(self, benchmark: BenchmarkFixture) -> None:
        _all_svcs, root = create_dependency_chain(8)
        container = Container()
        container.scan(profile=Profile.TEST)

        result = benchmark(container.resolve, root)
        assert result is not None

    def it_resolves_depth_8_chain_via_python(self, benchmark: BenchmarkFixture) -> None:
        all_svcs, root = create_dependency_chain(8)
        py_container = PurePythonContainer()
        for svc in reversed(all_svcs):
            py_container.register_singleton_with_deps(svc)

        result = benchmark(py_container.resolve, root)
        assert result is not None


# ============================================================================
# Benchmark: Concurrent Resolution
# ============================================================================


class DescribeConcurrentResolutionComparison:
    """Compare thread-safe concurrent resolution throughput and correctness."""

    def it_resolves_concurrently_via_rust(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        container = Container()
        container.scan(profile=Profile.TEST)
        container.resolve(svc)

        pool = ThreadPoolExecutor(max_workers=4)

        def concurrent_resolve() -> list[Any]:
            futures = [pool.submit(container.resolve, svc) for _ in range(100)]
            return [f.result() for f in futures]

        results = benchmark(concurrent_resolve)
        pool.shutdown(wait=False)
        assert len(results) == 100
        assert all(r is results[0] for r in results)

    def it_resolves_concurrently_via_python(self, benchmark: BenchmarkFixture) -> None:
        svc = create_independent_services(1)[0]
        py_container = PurePythonContainer()
        py_container.register_singleton(svc, svc)
        py_container.resolve(svc)

        pool = ThreadPoolExecutor(max_workers=4)

        def concurrent_resolve() -> list[Any]:
            futures = [pool.submit(py_container.resolve, svc) for _ in range(100)]
            return [f.result() for f in futures]

        results = benchmark(concurrent_resolve)
        pool.shutdown(wait=False)
        assert len(results) == 100
        assert all(r is results[0] for r in results)


# ============================================================================
# Memory Usage Comparison (not benchmarked - single measurement)
# ============================================================================


class DescribeMemoryUsageComparison:
    """Compare memory footprint of containers with registered singletons.

    These are regular tests (not benchmarks) because memory measurement
    should be done once with tracemalloc, not repeatedly timed.
    Run with: uv run pytest tests/benchmarks/test_rust_vs_python.py -k memory -v
    """

    def it_measures_rust_container_memory_with_100_singletons(self) -> None:
        services = create_independent_services(100)

        tracemalloc.start()
        before = tracemalloc.take_snapshot()

        container = Container()
        container.scan(profile=Profile.TEST)
        for svc in services:
            container.resolve(svc)

        after = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = after.compare_to(before, 'lineno')
        total_allocated = sum(s.size_diff for s in stats if s.size_diff > 0)
        assert total_allocated > 0

    def it_measures_python_container_memory_with_100_singletons(self) -> None:
        services = create_independent_services(100)

        tracemalloc.start()
        before = tracemalloc.take_snapshot()

        py_container = build_python_container_with_services(services)
        for svc in services:
            py_container.resolve(svc)

        after = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = after.compare_to(before, 'lineno')
        total_allocated = sum(s.size_diff for s in stats if s.size_diff > 0)
        assert total_allocated > 0

    def it_measures_rust_container_memory_with_1000_singletons(self) -> None:
        services = create_independent_services(1000)

        tracemalloc.start()
        before = tracemalloc.take_snapshot()

        container = Container()
        container.scan(profile=Profile.TEST)
        for svc in services:
            container.resolve(svc)

        after = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = after.compare_to(before, 'lineno')
        total_allocated = sum(s.size_diff for s in stats if s.size_diff > 0)
        assert total_allocated > 0

    def it_measures_python_container_memory_with_1000_singletons(self) -> None:
        services = create_independent_services(1000)

        tracemalloc.start()
        before = tracemalloc.take_snapshot()

        py_container = build_python_container_with_services(services)
        for svc in services:
            py_container.resolve(svc)

        after = tracemalloc.take_snapshot()
        tracemalloc.stop()

        stats = after.compare_to(before, 'lineno')
        total_allocated = sum(s.size_diff for s in stats if s.size_diff > 0)
        assert total_allocated > 0
