"""Performance benchmarks for dioxide dependency injection framework.

This module benchmarks dioxide's core operations to validate performance
characteristics align with MLP Vision goals.

Performance targets (from MLP_VISION.md):
- Dependency resolution should be "instant" (aspirational < 1μs, realistic < 10μs)
- Container initialization should be fast (< 10ms for 100 components)
- Zero runtime overhead compared to manual DI
"""

from typing import (
    Any,
    Protocol,
)

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)

# ============================================================================
# Test Fixtures and Helper Classes
# ============================================================================


class EmailPort(Protocol):
    """Simple email port for benchmarking."""

    def send(self, to: str, subject: str, body: str) -> None: ...


class DatabasePort(Protocol):
    """Simple database port for benchmarking."""

    def query(self, sql: str) -> list[dict[str, str]]: ...


class CachePort(Protocol):
    """Simple cache port for benchmarking."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


@pytest.fixture
def benchmark_container() -> Container:
    """Create a container with all benchmark components registered."""

    # Clear registry and define components fresh for each benchmark
    # to avoid interference from autouse fixture

    # Define adapters
    @adapter.for_(EmailPort, profile=Profile.TEST)
    class FakeEmailAdapter:
        """Fake email adapter for benchmark tests."""

        def send(self, to: str, subject: str, body: str) -> None:
            pass

    @adapter.for_(DatabasePort, profile=Profile.TEST)
    class FakeDatabaseAdapter:
        """Fake database adapter for benchmark tests."""

        def query(self, sql: str) -> list[dict[str, str]]:
            return []

    @adapter.for_(CachePort, profile=Profile.TEST)
    class FakeCacheAdapter:
        """Fake cache adapter for benchmark tests."""

        def __init__(self) -> None:
            self.store: dict[str, str] = {}

        def get(self, key: str) -> str | None:
            return self.store.get(key)

        def set(self, key: str, value: str) -> None:
            self.store[key] = value

    # Define services
    @service
    class SimpleService:
        """Service with no dependencies for benchmarking."""

        def do_work(self) -> str:
            return 'work done'

    @service
    class ServiceWith1Dependency:
        """Service with one dependency for benchmarking."""

        def __init__(self, email: EmailPort):
            self.email = email

        def do_work(self) -> str:
            return 'work done'

    @service
    class ServiceWith5Dependencies:
        """Service with five dependencies for benchmarking."""

        def __init__(
            self,
            email: EmailPort,
            db: DatabasePort,
            cache: CachePort,
            simple1: SimpleService,
            dep1: ServiceWith1Dependency,
        ):
            self.email = email
            self.db = db
            self.cache = cache
            self.simple1 = simple1
            self.dep1 = dep1

        def do_work(self) -> str:
            return 'work done'

    @service
    class ServiceWith10Dependencies:
        """Service with ten dependencies for benchmarking (includes transitive deps)."""

        def __init__(
            self,
            email: EmailPort,
            db: DatabasePort,
            cache: CachePort,
            simple1: SimpleService,
            dep1: ServiceWith1Dependency,
            dep5: ServiceWith5Dependencies,
        ):
            self.email = email
            self.db = db
            self.cache = cache
            self.simple1 = simple1
            self.dep1 = dep1
            self.dep5 = dep5

        def do_work(self) -> str:
            return 'work done'

    @service
    @lifecycle
    class LifecycleService1:
        """Lifecycle service for benchmarking."""

        async def initialize(self) -> None:
            """Initialize service."""
            pass

        async def dispose(self) -> None:
            """Dispose service."""
            pass

    @service
    @lifecycle
    class LifecycleService2:
        """Lifecycle service for benchmarking."""

        async def initialize(self) -> None:
            """Initialize service."""
            pass

        async def dispose(self) -> None:
            """Dispose service."""
            pass

    @service
    @lifecycle
    class LifecycleService3:
        """Lifecycle service for benchmarking."""

        async def initialize(self) -> None:
            """Initialize service."""
            pass

        async def dispose(self) -> None:
            """Dispose service."""
            pass

    # Create and scan container
    container = Container()
    container.scan(profile=Profile.TEST)

    # Store service classes on container for easy access
    container._simple_service = SimpleService  # pyright: ignore[reportAttributeAccessIssue]
    container._service_1_dep = ServiceWith1Dependency  # pyright: ignore[reportAttributeAccessIssue]
    container._service_5_deps = ServiceWith5Dependencies  # pyright: ignore[reportAttributeAccessIssue]
    container._service_10_deps = ServiceWith10Dependencies  # pyright: ignore[reportAttributeAccessIssue]

    return container


# ============================================================================
# Benchmark: Resolution Performance
# ============================================================================


class DescribeResolutionPerformance:
    """Benchmarks for dependency resolution speed."""

    def it_resolves_simple_service_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark resolving a service with no dependencies.

        Target: < 10μs per resolution (singleton, cached)
        """
        simple_service_cls = benchmark_container._simple_service  # pyright: ignore[reportAttributeAccessIssue]

        # Benchmark the resolution (should be cached after first call)
        result = benchmark(benchmark_container.resolve, simple_service_cls)

        assert result is not None

    def it_resolves_service_with_1_dependency_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark resolving a service with 1 dependency.

        Target: < 10μs per resolution (singleton, all deps cached)
        """
        service_cls = benchmark_container._service_1_dep  # pyright: ignore[reportAttributeAccessIssue]

        result = benchmark(benchmark_container.resolve, service_cls)

        assert result is not None

    def it_resolves_service_with_5_dependencies_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark resolving a service with 5 dependencies.

        Target: < 10μs per resolution (singleton, all deps cached)
        """
        service_cls = benchmark_container._service_5_deps  # pyright: ignore[reportAttributeAccessIssue]

        result = benchmark(benchmark_container.resolve, service_cls)

        assert result is not None

    def it_resolves_service_with_10_dependencies_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark resolving a service with 10 dependencies (including transitive).

        Target: < 10μs per resolution (singleton, all deps cached)
        """
        service_cls = benchmark_container._service_10_deps  # pyright: ignore[reportAttributeAccessIssue]

        result = benchmark(benchmark_container.resolve, service_cls)

        assert result is not None


# ============================================================================
# Benchmark: Container Initialization Performance
# ============================================================================


class DescribeContainerInitializationPerformance:
    """Benchmarks for container.scan() performance."""

    def it_scans_with_10_components_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark container.scan() with 10 components.

        Target: < 10ms for container initialization
        """

        def scan_container() -> None:
            # Use the pre-scanned container's scan to simulate rescanning
            new_container = Container()
            new_container.scan(profile=Profile.TEST)

        benchmark(scan_container)

    def it_scans_with_50_components_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark container.scan() with 50 components.

        Note: We only have ~10 components currently, so this simulates
        a larger application by repeatedly scanning.

        Target: < 50ms for larger applications
        """

        def scan_container() -> None:
            new_container = Container()
            # Scan 5 times to simulate ~50 components
            for _ in range(5):
                new_container.scan(profile=Profile.TEST)

        benchmark(scan_container)

    def it_scans_with_100_components_quickly(self, benchmark: Any, benchmark_container: Container) -> None:
        """Benchmark container.scan() with 100 components.

        Note: We only have ~10 components currently, so this simulates
        a larger application by repeatedly scanning.

        Target: < 100ms for large applications
        """

        def scan_container() -> None:
            new_container = Container()
            # Scan 10 times to simulate ~100 components
            for _ in range(10):
                new_container.scan(profile=Profile.TEST)

        benchmark(scan_container)


# ============================================================================
# Benchmark: Lifecycle Performance
# ============================================================================


class DescribeLifecyclePerformance:
    """Benchmarks for lifecycle management performance."""

    @pytest.mark.asyncio
    async def it_starts_container_with_lifecycle_components_quickly(
        self, benchmark: Any, benchmark_container: Container
    ) -> None:
        """Benchmark container.start() with lifecycle components.

        Target: < 10ms for initialization (excluding I/O)
        """

        async def start_container() -> None:
            await benchmark_container.start()

        await benchmark(start_container)

    @pytest.mark.asyncio
    async def it_stops_container_with_lifecycle_components_quickly(
        self, benchmark: Any, benchmark_container: Container
    ) -> None:
        """Benchmark container.stop() with lifecycle components.

        Target: < 10ms for cleanup (excluding I/O)
        """
        await benchmark_container.start()

        async def stop_container() -> None:
            await benchmark_container.stop()

        await benchmark(stop_container)


# ============================================================================
# Benchmark: Comparison with Manual DI
# ============================================================================


class DescribeComparisonWithManualDI:
    """Benchmarks comparing dioxide with manual dependency injection."""

    def it_has_minimal_overhead_vs_manual_di(self, benchmark: Any, benchmark_container: Container) -> None:
        """Compare dioxide resolution vs manual instantiation.

        Target: < 2x overhead compared to manual DI
        (Manual DI is just `ServiceWith5Dependencies(...manual args...)`)
        """
        service_cls = benchmark_container._service_5_deps  # pyright: ignore[reportAttributeAccessIssue]

        # Benchmark dioxide resolution
        result = benchmark(benchmark_container.resolve, service_cls)

        assert result is not None

    def it_matches_manual_di_for_simple_cases(self, benchmark: Any) -> None:
        """Benchmark manual instantiation (baseline).

        This establishes the baseline for manual DI performance.
        dioxide should be within 2x of this baseline for singleton resolution.
        """

        class SimpleManualService:
            """Simple service for manual instantiation baseline."""

            def do_work(self) -> str:
                return 'work done'

        def manual_instantiation() -> SimpleManualService:
            return SimpleManualService()

        result = benchmark(manual_instantiation)
        assert result is not None
