"""Honest benchmark comparison: dioxide vs dependency-injector.

NO SPIN. NO CHERRY-PICKING. This benchmark suite measures real-world performance
characteristics of both frameworks to identify strengths and weaknesses.

Philosophy:
    - If dependency-injector wins a benchmark, REPORT IT
    - Use equivalent patterns in both frameworks
    - No warm-up tricks - both frameworks get same treatment
    - Statistical rigor via pytest-benchmark

Framework Versions (at time of creation):
    - dioxide: 0.2.1 (Rust-backed)
    - dependency-injector: 4.48.2 (Cython-optimized)

Benchmark Categories:
    1. Simple Resolution - singleton with 0-3 dependencies
    2. Deep Dependency Chains - 5 and 10 levels deep
    3. Wide Dependency Graphs - 10 and 20 dependencies
    4. Concurrent Resolution - asyncio.gather with 100/1000 resolves
    5. Container Startup Time - scan/wire 10, 50, 100 components
    6. Memory Usage - tracemalloc measurements
    7. Real-World Simulation - FastAPI-like request patterns

Usage:
    # Run all benchmarks
    uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-sort=mean

    # Run specific category
    uv run pytest benchmarks/compare_di_frameworks.py -k "simple_resolution" --benchmark-only

    # Save results to JSON
    uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-json=results.json
"""

from __future__ import annotations

import asyncio
import gc
import tracemalloc
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
)

from dependency_injector import (
    containers,
    providers,
)

from dioxide import (
    Container,
    Profile,
    _clear_registry,
    service,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

# ============================================================================
# VERSION INFO
# ============================================================================

DIOXIDE_VERSION = '0.2.1'
DEPENDENCY_INJECTOR_VERSION = '4.48.2'


# ============================================================================
# SHARED PROTOCOL DEFINITIONS
# ============================================================================


class PortA(Protocol):
    """Port A for benchmarking."""

    def do_work(self) -> str: ...


class PortB(Protocol):
    """Port B for benchmarking."""

    def do_work(self) -> str: ...


class PortC(Protocol):
    """Port C for benchmarking."""

    def do_work(self) -> str: ...


# ============================================================================
# DEPENDENCY-INJECTOR SETUP
# ============================================================================


# Simple classes for dependency-injector
class DI_SimpleService:
    """Simple service with no dependencies."""

    def do_work(self) -> str:
        return 'work'


class DI_ServiceWith1Dep:
    """Service with 1 dependency."""

    def __init__(self, dep: DI_SimpleService) -> None:
        self.dep = dep

    def do_work(self) -> str:
        return self.dep.do_work()


class DI_ServiceWith2Deps:
    """Service with 2 dependencies."""

    def __init__(self, dep1: DI_SimpleService, dep2: DI_ServiceWith1Dep) -> None:
        self.dep1 = dep1
        self.dep2 = dep2


class DI_ServiceWith3Deps:
    """Service with 3 dependencies."""

    def __init__(self, dep1: DI_SimpleService, dep2: DI_ServiceWith1Dep, dep3: DI_ServiceWith2Deps) -> None:
        self.dep1 = dep1
        self.dep2 = dep2
        self.dep3 = dep3


# Deep chain for dependency-injector (5 levels)
class DI_Level1:
    pass


class DI_Level2:
    def __init__(self, dep: DI_Level1) -> None:
        self.dep = dep


class DI_Level3:
    def __init__(self, dep: DI_Level2) -> None:
        self.dep = dep


class DI_Level4:
    def __init__(self, dep: DI_Level3) -> None:
        self.dep = dep


class DI_Level5:
    def __init__(self, dep: DI_Level4) -> None:
        self.dep = dep


# Deep chain for dependency-injector (10 levels)
class DI_Deep1:
    pass


class DI_Deep2:
    def __init__(self, dep: DI_Deep1) -> None:
        self.dep = dep


class DI_Deep3:
    def __init__(self, dep: DI_Deep2) -> None:
        self.dep = dep


class DI_Deep4:
    def __init__(self, dep: DI_Deep3) -> None:
        self.dep = dep


class DI_Deep5:
    def __init__(self, dep: DI_Deep4) -> None:
        self.dep = dep


class DI_Deep6:
    def __init__(self, dep: DI_Deep5) -> None:
        self.dep = dep


class DI_Deep7:
    def __init__(self, dep: DI_Deep6) -> None:
        self.dep = dep


class DI_Deep8:
    def __init__(self, dep: DI_Deep7) -> None:
        self.dep = dep


class DI_Deep9:
    def __init__(self, dep: DI_Deep8) -> None:
        self.dep = dep


class DI_Deep10:
    def __init__(self, dep: DI_Deep9) -> None:
        self.dep = dep


# Wide dependencies for dependency-injector
class DI_Dep1:
    pass


class DI_Dep2:
    pass


class DI_Dep3:
    pass


class DI_Dep4:
    pass


class DI_Dep5:
    pass


class DI_Dep6:
    pass


class DI_Dep7:
    pass


class DI_Dep8:
    pass


class DI_Dep9:
    pass


class DI_Dep10:
    pass


class DI_Dep11:
    pass


class DI_Dep12:
    pass


class DI_Dep13:
    pass


class DI_Dep14:
    pass


class DI_Dep15:
    pass


class DI_Dep16:
    pass


class DI_Dep17:
    pass


class DI_Dep18:
    pass


class DI_Dep19:
    pass


class DI_Dep20:
    pass


class DI_Wide10:
    """Service with 10 dependencies."""

    def __init__(
        self,
        d1: DI_Dep1,
        d2: DI_Dep2,
        d3: DI_Dep3,
        d4: DI_Dep4,
        d5: DI_Dep5,
        d6: DI_Dep6,
        d7: DI_Dep7,
        d8: DI_Dep8,
        d9: DI_Dep9,
        d10: DI_Dep10,
    ) -> None:
        self.deps = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10]


class DI_Wide20:
    """Service with 20 dependencies."""

    def __init__(
        self,
        d1: DI_Dep1,
        d2: DI_Dep2,
        d3: DI_Dep3,
        d4: DI_Dep4,
        d5: DI_Dep5,
        d6: DI_Dep6,
        d7: DI_Dep7,
        d8: DI_Dep8,
        d9: DI_Dep9,
        d10: DI_Dep10,
        d11: DI_Dep11,
        d12: DI_Dep12,
        d13: DI_Dep13,
        d14: DI_Dep14,
        d15: DI_Dep15,
        d16: DI_Dep16,
        d17: DI_Dep17,
        d18: DI_Dep18,
        d19: DI_Dep19,
        d20: DI_Dep20,
    ) -> None:
        self.deps = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20]


# Dependency-injector containers
class DISimpleContainer(containers.DeclarativeContainer):
    """Container for simple resolution benchmarks."""

    simple = providers.Singleton(DI_SimpleService)
    with_1_dep = providers.Singleton(DI_ServiceWith1Dep, dep=simple)
    with_2_deps = providers.Singleton(DI_ServiceWith2Deps, dep1=simple, dep2=with_1_dep)
    with_3_deps = providers.Singleton(DI_ServiceWith3Deps, dep1=simple, dep2=with_1_dep, dep3=with_2_deps)


class DIDeepContainer(containers.DeclarativeContainer):
    """Container for deep dependency chain benchmarks."""

    level1 = providers.Singleton(DI_Level1)
    level2 = providers.Singleton(DI_Level2, dep=level1)
    level3 = providers.Singleton(DI_Level3, dep=level2)
    level4 = providers.Singleton(DI_Level4, dep=level3)
    level5 = providers.Singleton(DI_Level5, dep=level4)


class DIDeep10Container(containers.DeclarativeContainer):
    """Container for 10-level deep dependency chain."""

    deep1 = providers.Singleton(DI_Deep1)
    deep2 = providers.Singleton(DI_Deep2, dep=deep1)
    deep3 = providers.Singleton(DI_Deep3, dep=deep2)
    deep4 = providers.Singleton(DI_Deep4, dep=deep3)
    deep5 = providers.Singleton(DI_Deep5, dep=deep4)
    deep6 = providers.Singleton(DI_Deep6, dep=deep5)
    deep7 = providers.Singleton(DI_Deep7, dep=deep6)
    deep8 = providers.Singleton(DI_Deep8, dep=deep7)
    deep9 = providers.Singleton(DI_Deep9, dep=deep8)
    deep10 = providers.Singleton(DI_Deep10, dep=deep9)


class DIWideContainer(containers.DeclarativeContainer):
    """Container for wide dependency graph benchmarks."""

    dep1 = providers.Singleton(DI_Dep1)
    dep2 = providers.Singleton(DI_Dep2)
    dep3 = providers.Singleton(DI_Dep3)
    dep4 = providers.Singleton(DI_Dep4)
    dep5 = providers.Singleton(DI_Dep5)
    dep6 = providers.Singleton(DI_Dep6)
    dep7 = providers.Singleton(DI_Dep7)
    dep8 = providers.Singleton(DI_Dep8)
    dep9 = providers.Singleton(DI_Dep9)
    dep10 = providers.Singleton(DI_Dep10)
    dep11 = providers.Singleton(DI_Dep11)
    dep12 = providers.Singleton(DI_Dep12)
    dep13 = providers.Singleton(DI_Dep13)
    dep14 = providers.Singleton(DI_Dep14)
    dep15 = providers.Singleton(DI_Dep15)
    dep16 = providers.Singleton(DI_Dep16)
    dep17 = providers.Singleton(DI_Dep17)
    dep18 = providers.Singleton(DI_Dep18)
    dep19 = providers.Singleton(DI_Dep19)
    dep20 = providers.Singleton(DI_Dep20)

    wide10 = providers.Singleton(
        DI_Wide10,
        d1=dep1,
        d2=dep2,
        d3=dep3,
        d4=dep4,
        d5=dep5,
        d6=dep6,
        d7=dep7,
        d8=dep8,
        d9=dep9,
        d10=dep10,
    )

    wide20 = providers.Singleton(
        DI_Wide20,
        d1=dep1,
        d2=dep2,
        d3=dep3,
        d4=dep4,
        d5=dep5,
        d6=dep6,
        d7=dep7,
        d8=dep8,
        d9=dep9,
        d10=dep10,
        d11=dep11,
        d12=dep12,
        d13=dep13,
        d14=dep14,
        d15=dep15,
        d16=dep16,
        d17=dep17,
        d18=dep18,
        d19=dep19,
        d20=dep20,
    )


# ============================================================================
# DIOXIDE SETUP HELPER
# ============================================================================


def setup_dioxide_simple() -> tuple[Container, type, type, type, type]:
    """Set up dioxide container for simple resolution tests."""
    _clear_registry()

    @service
    class SimpleService:
        def do_work(self) -> str:
            return 'work'

    @service
    class ServiceWith1Dep:
        def __init__(self, dep: SimpleService) -> None:
            self.dep = dep

    @service
    class ServiceWith2Deps:
        def __init__(self, dep1: SimpleService, dep2: ServiceWith1Dep) -> None:
            self.dep1 = dep1
            self.dep2 = dep2

    @service
    class ServiceWith3Deps:
        def __init__(self, dep1: SimpleService, dep2: ServiceWith1Dep, dep3: ServiceWith2Deps) -> None:
            self.dep1 = dep1
            self.dep2 = dep2
            self.dep3 = dep3

    container = Container()
    container.scan(profile=Profile.ALL)

    return container, SimpleService, ServiceWith1Dep, ServiceWith2Deps, ServiceWith3Deps


def setup_dioxide_deep5() -> tuple[Container, type]:
    """Set up dioxide container for 5-level deep chain."""
    _clear_registry()

    @service
    class Level1:
        pass

    @service
    class Level2:
        def __init__(self, dep: Level1) -> None:
            self.dep = dep

    @service
    class Level3:
        def __init__(self, dep: Level2) -> None:
            self.dep = dep

    @service
    class Level4:
        def __init__(self, dep: Level3) -> None:
            self.dep = dep

    @service
    class Level5:
        def __init__(self, dep: Level4) -> None:
            self.dep = dep

    container = Container()
    container.scan(profile=Profile.ALL)

    return container, Level5


def setup_dioxide_deep10() -> tuple[Container, type]:
    """Set up dioxide container for 10-level deep chain."""
    _clear_registry()

    @service
    class Deep1:
        pass

    @service
    class Deep2:
        def __init__(self, dep: Deep1) -> None:
            self.dep = dep

    @service
    class Deep3:
        def __init__(self, dep: Deep2) -> None:
            self.dep = dep

    @service
    class Deep4:
        def __init__(self, dep: Deep3) -> None:
            self.dep = dep

    @service
    class Deep5:
        def __init__(self, dep: Deep4) -> None:
            self.dep = dep

    @service
    class Deep6:
        def __init__(self, dep: Deep5) -> None:
            self.dep = dep

    @service
    class Deep7:
        def __init__(self, dep: Deep6) -> None:
            self.dep = dep

    @service
    class Deep8:
        def __init__(self, dep: Deep7) -> None:
            self.dep = dep

    @service
    class Deep9:
        def __init__(self, dep: Deep8) -> None:
            self.dep = dep

    @service
    class Deep10:
        def __init__(self, dep: Deep9) -> None:
            self.dep = dep

    container = Container()
    container.scan(profile=Profile.ALL)

    return container, Deep10


def setup_dioxide_wide() -> tuple[Container, type, type]:
    """Set up dioxide container for wide dependency graph."""
    _clear_registry()

    @service
    class Dep1:
        pass

    @service
    class Dep2:
        pass

    @service
    class Dep3:
        pass

    @service
    class Dep4:
        pass

    @service
    class Dep5:
        pass

    @service
    class Dep6:
        pass

    @service
    class Dep7:
        pass

    @service
    class Dep8:
        pass

    @service
    class Dep9:
        pass

    @service
    class Dep10:
        pass

    @service
    class Dep11:
        pass

    @service
    class Dep12:
        pass

    @service
    class Dep13:
        pass

    @service
    class Dep14:
        pass

    @service
    class Dep15:
        pass

    @service
    class Dep16:
        pass

    @service
    class Dep17:
        pass

    @service
    class Dep18:
        pass

    @service
    class Dep19:
        pass

    @service
    class Dep20:
        pass

    @service
    class Wide10:
        def __init__(
            self,
            d1: Dep1,
            d2: Dep2,
            d3: Dep3,
            d4: Dep4,
            d5: Dep5,
            d6: Dep6,
            d7: Dep7,
            d8: Dep8,
            d9: Dep9,
            d10: Dep10,
        ) -> None:
            self.deps = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10]

    @service
    class Wide20:
        def __init__(
            self,
            d1: Dep1,
            d2: Dep2,
            d3: Dep3,
            d4: Dep4,
            d5: Dep5,
            d6: Dep6,
            d7: Dep7,
            d8: Dep8,
            d9: Dep9,
            d10: Dep10,
            d11: Dep11,
            d12: Dep12,
            d13: Dep13,
            d14: Dep14,
            d15: Dep15,
            d16: Dep16,
            d17: Dep17,
            d18: Dep18,
            d19: Dep19,
            d20: Dep20,
        ) -> None:
            self.deps = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20]

    container = Container()
    container.scan(profile=Profile.ALL)

    return container, Wide10, Wide20


# ============================================================================
# CATEGORY 1: SIMPLE RESOLUTION
# ============================================================================


class DescribeSimpleResolution:
    """Benchmarks for simple service resolution (cached singletons)."""

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_dioxide_singleton_no_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: singleton with no dependencies."""
        container, SimpleService, *_ = setup_dioxide_simple()
        # Warm up - first resolution creates the singleton
        _ = container.resolve(SimpleService)

        result = benchmark(container.resolve, SimpleService)
        assert result is not None

    def it_resolves_dioxide_singleton_1_dep(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: singleton with 1 dependency."""
        container, _, ServiceWith1Dep, *_ = setup_dioxide_simple()
        _ = container.resolve(ServiceWith1Dep)

        result = benchmark(container.resolve, ServiceWith1Dep)
        assert result is not None

    def it_resolves_dioxide_singleton_2_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: singleton with 2 dependencies."""
        container, _, _, ServiceWith2Deps, _ = setup_dioxide_simple()
        _ = container.resolve(ServiceWith2Deps)

        result = benchmark(container.resolve, ServiceWith2Deps)
        assert result is not None

    def it_resolves_dioxide_singleton_3_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: singleton with 3 dependencies."""
        container, *_, ServiceWith3Deps = setup_dioxide_simple()
        _ = container.resolve(ServiceWith3Deps)

        result = benchmark(container.resolve, ServiceWith3Deps)
        assert result is not None

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_di_singleton_no_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: singleton with no dependencies."""
        container = DISimpleContainer()
        # Warm up
        _ = container.simple()

        result = benchmark(container.simple)
        assert result is not None

    def it_resolves_di_singleton_1_dep(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: singleton with 1 dependency."""
        container = DISimpleContainer()
        _ = container.with_1_dep()

        result = benchmark(container.with_1_dep)
        assert result is not None

    def it_resolves_di_singleton_2_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: singleton with 2 dependencies."""
        container = DISimpleContainer()
        _ = container.with_2_deps()

        result = benchmark(container.with_2_deps)
        assert result is not None

    def it_resolves_di_singleton_3_deps(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: singleton with 3 dependencies."""
        container = DISimpleContainer()
        _ = container.with_3_deps()

        result = benchmark(container.with_3_deps)
        assert result is not None


# ============================================================================
# CATEGORY 2: DEEP DEPENDENCY CHAINS
# ============================================================================


class DescribeDeepDependencyChains:
    """Benchmarks for deep dependency chain resolution."""

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_dioxide_5_level_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: 5-level deep dependency chain."""
        container, Level5 = setup_dioxide_deep5()
        _ = container.resolve(Level5)

        result = benchmark(container.resolve, Level5)
        assert result is not None

    def it_resolves_dioxide_10_level_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: 10-level deep dependency chain."""
        container, Deep10 = setup_dioxide_deep10()
        _ = container.resolve(Deep10)

        result = benchmark(container.resolve, Deep10)
        assert result is not None

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_di_5_level_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: 5-level deep dependency chain."""
        container = DIDeepContainer()
        _ = container.level5()

        result = benchmark(container.level5)
        assert result is not None

    def it_resolves_di_10_level_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: 10-level deep dependency chain."""
        container = DIDeep10Container()
        _ = container.deep10()

        result = benchmark(container.deep10)
        assert result is not None


# ============================================================================
# CATEGORY 3: WIDE DEPENDENCY GRAPHS
# ============================================================================


class DescribeWideDependencyGraphs:
    """Benchmarks for wide dependency graph resolution (many deps)."""

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_dioxide_10_dependencies(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: service with 10 dependencies."""
        container, Wide10, _ = setup_dioxide_wide()
        _ = container.resolve(Wide10)

        result = benchmark(container.resolve, Wide10)
        assert result is not None

    def it_resolves_dioxide_20_dependencies(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: service with 20 dependencies."""
        container, _, Wide20 = setup_dioxide_wide()
        _ = container.resolve(Wide20)

        result = benchmark(container.resolve, Wide20)
        assert result is not None

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_di_10_dependencies(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: service with 10 dependencies."""
        container = DIWideContainer()
        _ = container.wide10()

        result = benchmark(container.wide10)
        assert result is not None

    def it_resolves_di_20_dependencies(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: service with 20 dependencies."""
        container = DIWideContainer()
        _ = container.wide20()

        result = benchmark(container.wide20)
        assert result is not None


# ============================================================================
# CATEGORY 4: CONCURRENT RESOLUTION
# ============================================================================


class DescribeConcurrentResolution:
    """Benchmarks for concurrent resolution under load."""

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_dioxide_100_concurrent(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: 100 concurrent resolutions."""
        container, _, _, ServiceWith2Deps, _ = setup_dioxide_simple()
        _ = container.resolve(ServiceWith2Deps)

        async def resolve_many() -> list[Any]:
            return await asyncio.gather(*[asyncio.to_thread(container.resolve, ServiceWith2Deps) for _ in range(100)])

        result = benchmark(lambda: asyncio.run(resolve_many()))
        assert len(result) == 100

    def it_resolves_dioxide_1000_concurrent(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: 1000 concurrent resolutions."""
        container, _, _, ServiceWith2Deps, _ = setup_dioxide_simple()
        _ = container.resolve(ServiceWith2Deps)

        async def resolve_many() -> list[Any]:
            return await asyncio.gather(*[asyncio.to_thread(container.resolve, ServiceWith2Deps) for _ in range(1000)])

        result = benchmark(lambda: asyncio.run(resolve_many()))
        assert len(result) == 1000

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_resolves_di_100_concurrent(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: 100 concurrent resolutions."""
        container = DISimpleContainer()
        _ = container.with_2_deps()

        async def resolve_many() -> list[Any]:
            return await asyncio.gather(*[asyncio.to_thread(container.with_2_deps) for _ in range(100)])

        result = benchmark(lambda: asyncio.run(resolve_many()))
        assert len(result) == 100

    def it_resolves_di_1000_concurrent(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: 1000 concurrent resolutions."""
        container = DISimpleContainer()
        _ = container.with_2_deps()

        async def resolve_many() -> list[Any]:
            return await asyncio.gather(*[asyncio.to_thread(container.with_2_deps) for _ in range(1000)])

        result = benchmark(lambda: asyncio.run(resolve_many()))
        assert len(result) == 1000


# ============================================================================
# CATEGORY 5: CONTAINER STARTUP TIME
# ============================================================================


class DescribeContainerStartupTime:
    """Benchmarks for container initialization/wiring time.

    NOTE: This is where dependency-injector may have an advantage since
    dioxide requires Rust compilation on first import. We measure only
    the scan/wire time here, not import time.
    """

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_measures_dioxide_scan_10_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: scan time for 10 components."""

        def setup_and_scan() -> Container:
            _clear_registry()

            # Define 10 simple services
            @service
            class S1:
                pass

            @service
            class S2:
                pass

            @service
            class S3:
                pass

            @service
            class S4:
                pass

            @service
            class S5:
                pass

            @service
            class S6:
                pass

            @service
            class S7:
                pass

            @service
            class S8:
                pass

            @service
            class S9:
                pass

            @service
            class S10:
                pass

            container = Container()
            container.scan(profile=Profile.ALL)
            return container

        result = benchmark(setup_and_scan)
        assert len(result) == 10

    def it_measures_dioxide_scan_50_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: scan time for 50 components."""

        def setup_and_scan() -> Container:
            _clear_registry()

            # Define 50 simple services dynamically
            services = []
            for i in range(50):

                @service
                class DynamicService:
                    pass

                DynamicService.__name__ = f'Service{i}'
                DynamicService.__qualname__ = f'Service{i}'
                services.append(DynamicService)

            container = Container()
            container.scan(profile=Profile.ALL)
            return container

        result = benchmark(setup_and_scan)
        assert len(result) == 50

    def it_measures_dioxide_scan_100_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: scan time for 100 components."""

        def setup_and_scan() -> Container:
            _clear_registry()

            # Define 100 simple services dynamically
            services = []
            for i in range(100):

                @service
                class DynamicService:
                    pass

                DynamicService.__name__ = f'Service{i}'
                DynamicService.__qualname__ = f'Service{i}'
                services.append(DynamicService)

            container = Container()
            container.scan(profile=Profile.ALL)
            return container

        result = benchmark(setup_and_scan)
        assert len(result) == 100

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_measures_di_wire_10_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: wire time for 10 components."""

        def setup_and_wire() -> containers.DeclarativeContainer:
            class S1:
                pass

            class S2:
                pass

            class S3:
                pass

            class S4:
                pass

            class S5:
                pass

            class S6:
                pass

            class S7:
                pass

            class S8:
                pass

            class S9:
                pass

            class S10:
                pass

            class DIContainer(containers.DeclarativeContainer):
                s1 = providers.Singleton(S1)
                s2 = providers.Singleton(S2)
                s3 = providers.Singleton(S3)
                s4 = providers.Singleton(S4)
                s5 = providers.Singleton(S5)
                s6 = providers.Singleton(S6)
                s7 = providers.Singleton(S7)
                s8 = providers.Singleton(S8)
                s9 = providers.Singleton(S9)
                s10 = providers.Singleton(S10)

            return DIContainer()

        result = benchmark(setup_and_wire)
        assert result is not None

    def it_measures_di_wire_50_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: wire time for 50 components."""

        def setup_and_wire() -> Any:
            # Create classes dynamically
            service_classes = [type(f'S{i}', (), {}) for i in range(50)]

            # Create container class with providers
            provider_dict = {f's{i}': providers.Singleton(cls) for i, cls in enumerate(service_classes)}
            # Dynamic type() returns Any, so container type is not statically known
            DIContainer = type('DIContainer', (containers.DeclarativeContainer,), provider_dict)

            return DIContainer()

        result = benchmark(setup_and_wire)
        assert result is not None

    def it_measures_di_wire_100_components(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: wire time for 100 components."""

        def setup_and_wire() -> Any:
            # Create classes dynamically
            service_classes = [type(f'S{i}', (), {}) for i in range(100)]

            # Create container class with providers
            provider_dict = {f's{i}': providers.Singleton(cls) for i, cls in enumerate(service_classes)}
            # Dynamic type() returns Any, so container type is not statically known
            DIContainer = type('DIContainer', (containers.DeclarativeContainer,), provider_dict)

            return DIContainer()

        result = benchmark(setup_and_wire)
        assert result is not None


# ============================================================================
# CATEGORY 6: MEMORY USAGE
# ============================================================================


class DescribeMemoryUsage:
    """Benchmarks for memory footprint.

    Note: These use tracemalloc for measurement, not pytest-benchmark.
    Results are printed to stdout for manual comparison.
    """

    def it_measures_dioxide_memory_100_singletons(self) -> None:
        """Measure dioxide memory footprint with 100 singletons."""
        gc.collect()
        tracemalloc.start()

        _clear_registry()

        # Create 100 services
        services = []
        for i in range(100):
            # Capture loop variable in closure to avoid B023
            data_value = f'service_{i}'

            @service
            class DynamicService:
                _data = data_value  # Capture at class definition time

                def __init__(self) -> None:
                    self.data = self._data

            DynamicService.__name__ = f'Service{i}'
            DynamicService.__qualname__ = f'Service{i}'
            services.append(DynamicService)

        container = Container()
        container.scan(profile=Profile.ALL)

        # Resolve all services to populate cache
        for svc in services:
            container.resolve(svc)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print('\nDioxide memory (100 singletons):')
        print(f'  Current: {current / 1024:.2f} KB')
        print(f'  Peak: {peak / 1024:.2f} KB')

        # Just verify it doesn't crash - memory is logged above
        assert container is not None

    def it_measures_di_memory_100_singletons(self) -> None:
        """Measure dependency-injector memory footprint with 100 singletons."""
        gc.collect()
        tracemalloc.start()

        # Create classes dynamically
        service_classes = []
        for i in range(100):
            # Capture loop variable in closure to avoid B023
            data_value = f'service_{i}'

            class DynamicService:
                _data = data_value  # Capture at class definition time

                def __init__(self) -> None:
                    self.data = self._data

            DynamicService.__name__ = f'Service{i}'
            service_classes.append(DynamicService)

        # Create container class with providers
        provider_dict = {f's{i}': providers.Singleton(cls) for i, cls in enumerate(service_classes)}
        DIContainer = type('DIContainer', (containers.DeclarativeContainer,), provider_dict)
        container = DIContainer()

        # Resolve all services to populate cache
        for i in range(100):
            getattr(container, f's{i}')()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print('\nDependency-injector memory (100 singletons):')
        print(f'  Current: {current / 1024:.2f} KB')
        print(f'  Peak: {peak / 1024:.2f} KB')

        # Just verify it doesn't crash - memory is logged above
        assert container is not None


# ============================================================================
# CATEGORY 7: REAL-WORLD SIMULATION
# ============================================================================


class DescribeRealWorldSimulation:
    """Benchmarks simulating real-world usage patterns (FastAPI-like)."""

    # -------------------------------------------------------------------------
    # dioxide benchmarks
    # -------------------------------------------------------------------------

    def it_simulates_dioxide_1000_requests(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: simulate 1000 web requests resolving 5 services each."""
        container, SimpleService, ServiceWith1Dep, ServiceWith2Deps, ServiceWith3Deps = setup_dioxide_simple()

        # Warm up
        _ = container.resolve(SimpleService)
        _ = container.resolve(ServiceWith1Dep)
        _ = container.resolve(ServiceWith2Deps)
        _ = container.resolve(ServiceWith3Deps)

        def simulate_request() -> None:
            # Typical request: resolve multiple services
            container.resolve(SimpleService)
            container.resolve(ServiceWith1Dep)
            container.resolve(ServiceWith2Deps)
            container.resolve(ServiceWith3Deps)
            container.resolve(SimpleService)  # Some overlap

        def simulate_1000_requests() -> None:
            for _ in range(1000):
                simulate_request()

        benchmark(simulate_1000_requests)

    def it_simulates_dioxide_100_concurrent_requests(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: simulate 100 concurrent requests."""
        container, SimpleService, ServiceWith1Dep, ServiceWith2Deps, ServiceWith3Deps = setup_dioxide_simple()

        # Warm up
        _ = container.resolve(SimpleService)
        _ = container.resolve(ServiceWith1Dep)
        _ = container.resolve(ServiceWith2Deps)
        _ = container.resolve(ServiceWith3Deps)

        async def simulate_request() -> None:
            await asyncio.to_thread(container.resolve, SimpleService)
            await asyncio.to_thread(container.resolve, ServiceWith1Dep)
            await asyncio.to_thread(container.resolve, ServiceWith2Deps)
            await asyncio.to_thread(container.resolve, ServiceWith3Deps)

        async def simulate_concurrent_requests() -> None:
            await asyncio.gather(*[simulate_request() for _ in range(100)])

        benchmark(lambda: asyncio.run(simulate_concurrent_requests()))

    # -------------------------------------------------------------------------
    # dependency-injector benchmarks
    # -------------------------------------------------------------------------

    def it_simulates_di_1000_requests(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: simulate 1000 web requests resolving 5 services each."""
        container = DISimpleContainer()

        # Warm up
        _ = container.simple()
        _ = container.with_1_dep()
        _ = container.with_2_deps()
        _ = container.with_3_deps()

        def simulate_request() -> None:
            container.simple()
            container.with_1_dep()
            container.with_2_deps()
            container.with_3_deps()
            container.simple()

        def simulate_1000_requests() -> None:
            for _ in range(1000):
                simulate_request()

        benchmark(simulate_1000_requests)

    def it_simulates_di_100_concurrent_requests(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: simulate 100 concurrent requests."""
        container = DISimpleContainer()

        # Warm up
        _ = container.simple()
        _ = container.with_1_dep()
        _ = container.with_2_deps()
        _ = container.with_3_deps()

        async def simulate_request() -> None:
            await asyncio.to_thread(container.simple)
            await asyncio.to_thread(container.with_1_dep)
            await asyncio.to_thread(container.with_2_deps)
            await asyncio.to_thread(container.with_3_deps)

        async def simulate_concurrent_requests() -> None:
            await asyncio.gather(*[simulate_request() for _ in range(100)])

        benchmark(lambda: asyncio.run(simulate_concurrent_requests()))


# ============================================================================
# CATEGORY 8: FIRST RESOLUTION (COLD START)
# ============================================================================


class DescribeFirstResolution:
    """Benchmarks for first-time resolution (before caching).

    This measures the actual instantiation cost, not cached lookup.
    """

    def it_measures_dioxide_first_resolution_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dioxide: first resolution of dependency chain (no cache)."""

        def fresh_resolution() -> Any:
            container, Level5 = setup_dioxide_deep5()
            return container.resolve(Level5)

        result = benchmark(fresh_resolution)
        assert result is not None

    def it_measures_di_first_resolution_chain(self, benchmark: BenchmarkFixture) -> None:
        """Benchmark dependency-injector: first resolution of dependency chain (no cache)."""

        def fresh_resolution() -> Any:
            container = DIDeepContainer()
            return container.level5()

        result = benchmark(fresh_resolution)
        assert result is not None


# ============================================================================
# SUMMARY HELPER (run manually)
# ============================================================================


def print_summary() -> None:
    """Print a summary of what each benchmark measures.

    Run this manually: python -c "from benchmarks.compare_di_frameworks import print_summary; print_summary()"
    """
    print(
        """
    ============================================================================
    BENCHMARK COMPARISON: dioxide vs dependency-injector
    ============================================================================

    Framework Versions:
    - dioxide: 0.2.1 (Rust-backed with PyO3)
    - dependency-injector: 4.48.2 (Cython-optimized)

    Categories:

    1. SIMPLE RESOLUTION (cached singletons)
       - Tests: 0, 1, 2, 3 dependencies
       - What it measures: Singleton cache lookup speed
       - Expected: Both should be fast (simple hash lookup)

    2. DEEP DEPENDENCY CHAINS
       - Tests: 5-level, 10-level chains
       - What it measures: Recursive resolution overhead
       - Expected: dioxide may have advantage with Rust recursion

    3. WIDE DEPENDENCY GRAPHS
       - Tests: 10, 20 dependencies
       - What it measures: Parameter injection overhead
       - Expected: Both should be similar

    4. CONCURRENT RESOLUTION
       - Tests: 100, 1000 concurrent resolves
       - What it measures: Thread safety overhead
       - Expected: Rust may provide better concurrency

    5. CONTAINER STARTUP TIME
       - Tests: 10, 50, 100 components
       - What it measures: Scan/wire time
       - Expected: dependency-injector may win (no Rust overhead)

    6. MEMORY USAGE
       - Tests: 100 singletons
       - What it measures: Memory footprint
       - Expected: Comparable

    7. REAL-WORLD SIMULATION
       - Tests: 1000 sequential, 100 concurrent "requests"
       - What it measures: Realistic web server patterns
       - Expected: Most representative benchmark

    8. FIRST RESOLUTION (cold start)
       - Tests: Fresh container, first resolve
       - What it measures: Full instantiation cost
       - Expected: dependency-injector may win (simpler setup)

    Run benchmarks:
        uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-sort=mean

    Save results:
        uv run pytest benchmarks/compare_di_frameworks.py --benchmark-only --benchmark-json=results.json
    """
    )
