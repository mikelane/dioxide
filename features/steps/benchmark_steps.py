"""Step definitions for Rust backend benchmark acceptance tests.

These steps define the acceptance criteria for benchmarks that compare
the Rust-backed container against a pure Python implementation. All steps
are expected to FAIL until the benchmark infrastructure and pure Python
comparison container are implemented (see Epic #369).

The steps validate that:
1. A benchmark suite exists and produces statistical results
2. A pure Python container exists as a comparison baseline
3. Results include standard latency percentiles (p50, p95, p99)
4. Memory, startup, and concurrency are all measured
5. A documented recommendation is produced
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from behave import given, then, when

from dioxide import Container

if TYPE_CHECKING:
    from behave.runner import Context

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _import_benchmark_suite() -> Any:
    """Import the benchmark comparison suite module.

    Raises ImportError if the module does not exist yet.
    """
    try:
        from tests.benchmarks import rust_vs_python_benchmarks

        return rust_vs_python_benchmarks
    except ImportError as exc:
        raise ImportError(
            'Benchmark comparison suite not yet implemented. See Epic #369 for implementation plan.'
        ) from exc


def _import_pure_python_container() -> Any:
    """Import the pure Python container used as a comparison baseline.

    Raises ImportError if the module does not exist yet.
    """
    try:
        from dioxide import _pure_python_container

        return _pure_python_container
    except ImportError as exc:
        raise ImportError(
            'Pure Python comparison container not yet implemented. See Epic #369 for implementation plan.'
        ) from exc


# ---------------------------------------------------------------------------
# Given steps
# ---------------------------------------------------------------------------


@given('a benchmark suite comparing Rust and pure Python containers')
def step_benchmark_suite_exists(context: Context) -> None:
    """Verify the benchmark comparison suite is importable and ready."""
    suite = _import_benchmark_suite()
    context.benchmark_suite = suite

    pure_python = _import_pure_python_container()
    context.pure_python_container_module = pure_python

    context.rust_container = Container()
    context.python_container = pure_python.PurePythonContainer()


@given('both containers have a singleton service registered')
def step_both_containers_have_singleton(context: Context) -> None:
    """Register an identical singleton service in both containers."""
    suite = context.benchmark_suite
    suite.register_singleton_service(context.rust_container)
    suite.register_singleton_service(context.python_container)


@given('both containers have a dependency chain of depth {depth:d}')
def step_both_containers_have_depth_chain(context: Context, depth: int) -> None:
    """Register a dependency chain of the given depth in both containers."""
    suite = context.benchmark_suite
    suite.register_dependency_chain(context.rust_container, depth=depth)
    suite.register_dependency_chain(context.python_container, depth=depth)
    context.chain_depth = depth


@given('both containers have {count:d} singletons registered')
def step_both_containers_have_n_singletons(context: Context, count: int) -> None:
    """Register N singletons in both containers."""
    suite = context.benchmark_suite
    suite.register_n_singletons(context.rust_container, count=count)
    suite.register_n_singletons(context.python_container, count=count)
    context.singleton_count = count


@given('both containers have {count:d} adapters to discover')
def step_both_containers_have_n_adapters(context: Context, count: int) -> None:
    """Register N adapters for scanning in both containers."""
    suite = context.benchmark_suite
    suite.register_n_adapters(context.rust_container, count=count)
    suite.register_n_adapters(context.python_container, count=count)
    context.adapter_count = count


@given('both containers have singletons registered')
def step_both_containers_have_singletons(context: Context) -> None:
    """Register singletons in both containers for concurrency testing."""
    suite = context.benchmark_suite
    suite.register_singleton_service(context.rust_container)
    suite.register_singleton_service(context.python_container)


@given('a FastAPI application with {count:d} adapters')
def step_fastapi_app_with_adapters(context: Context, count: int) -> None:
    """Create a FastAPI application wired with the given number of adapters."""
    suite = _import_benchmark_suite()
    context.benchmark_suite = suite
    context.fastapi_app = suite.create_fastapi_benchmark_app(adapter_count=count)


@given('it can use either the Rust or pure Python container')
def step_fastapi_supports_both_backends(context: Context) -> None:
    """Verify the FastAPI app can be configured with either backend."""
    suite = context.benchmark_suite
    assert suite.fastapi_supports_backend_switch(context.fastapi_app)


@given('all benchmark scenarios have been executed')
def step_all_benchmarks_executed(context: Context) -> None:
    """Verify that all benchmark scenarios have produced results."""
    results_path = PROJECT_ROOT / 'docs' / 'benchmark-results.md'
    assert results_path.exists(), (
        f'Benchmark results document not found at {results_path}. Run the full benchmark suite first.'
    )
    context.results_path = results_path


@given('benchmark results have been collected')
def step_benchmark_results_collected(context: Context) -> None:
    """Verify that benchmark results contain data for all categories."""
    content = context.results_path.read_text()
    required_sections = [
        'Resolution Speed',
        'Nested Dependencies',
        'Memory Usage',
        'Startup Time',
        'Concurrent Resolution',
        'FastAPI Integration',
    ]
    for section in required_sections:
        assert section in content, f"Benchmark results missing section: '{section}'"


# ---------------------------------------------------------------------------
# When steps
# ---------------------------------------------------------------------------


@when('I run singleton resolution {count:d} times on each container')
def step_run_resolution_n_times(context: Context, count: int) -> None:
    """Run resolution benchmarks on both containers."""
    suite = context.benchmark_suite
    context.rust_results = suite.benchmark_resolution(context.rust_container, iterations=count)
    context.python_results = suite.benchmark_resolution(context.python_container, iterations=count)


@when('I resolve the top-level service {count:d} times on each container')
def step_resolve_top_level_n_times(context: Context, count: int) -> None:
    """Resolve the top-level service in a dependency chain."""
    suite = context.benchmark_suite
    context.rust_results = suite.benchmark_nested_resolution(context.rust_container, iterations=count)
    context.python_results = suite.benchmark_nested_resolution(context.python_container, iterations=count)


@when('I measure memory after resolving all singletons on each container')
def step_measure_memory(context: Context) -> None:
    """Measure memory usage after resolving all singletons."""
    suite = context.benchmark_suite
    context.rust_results = suite.measure_memory(context.rust_container)
    context.python_results = suite.measure_memory(context.python_container)


@when('I measure container scan time on each container')
def step_measure_scan_time(context: Context) -> None:
    """Measure container.scan() time on both containers."""
    suite = context.benchmark_suite
    context.rust_results = suite.benchmark_scan(context.rust_container)
    context.python_results = suite.benchmark_scan(context.python_container)


@when('I run {thread_count:d} threads resolving singletons simultaneously for {duration:d} second')
def step_run_concurrent_resolution(context: Context, thread_count: int, duration: int) -> None:
    """Run concurrent resolution on both containers."""
    suite = context.benchmark_suite
    context.rust_results = suite.benchmark_concurrent_resolution(
        context.rust_container, threads=thread_count, duration_seconds=duration
    )
    context.python_results = suite.benchmark_concurrent_resolution(
        context.python_container, threads=thread_count, duration_seconds=duration
    )


@when('I measure request latency with dependency resolution')
def step_measure_fastapi_latency(context: Context) -> None:
    """Measure request latency with DI resolution in the FastAPI app."""
    suite = context.benchmark_suite
    context.rust_results = suite.benchmark_fastapi_latency(context.fastapi_app, backend='rust')
    context.python_results = suite.benchmark_fastapi_latency(context.fastapi_app, backend='python')


@when('I review the benchmark results document')
def step_review_results_document(context: Context) -> None:
    """Read and parse the benchmark results document."""
    context.results_content = context.results_path.read_text()


# ---------------------------------------------------------------------------
# Then steps: Latency percentiles
# ---------------------------------------------------------------------------


@then('I receive p50, p95, and p99 latencies for the Rust container')
def step_rust_has_percentiles(context: Context) -> None:
    """Verify Rust results include standard latency percentiles."""
    results = context.rust_results
    assert 'p50' in results, 'Rust results missing p50 latency'
    assert 'p95' in results, 'Rust results missing p95 latency'
    assert 'p99' in results, 'Rust results missing p99 latency'
    assert all(isinstance(results[k], (int, float)) for k in ('p50', 'p95', 'p99')), (
        'Latency percentiles must be numeric values'
    )


@then('I receive p50, p95, and p99 latencies for the pure Python container')
def step_python_has_percentiles(context: Context) -> None:
    """Verify pure Python results include standard latency percentiles."""
    results = context.python_results
    assert 'p50' in results, 'Python results missing p50 latency'
    assert 'p95' in results, 'Python results missing p95 latency'
    assert 'p99' in results, 'Python results missing p99 latency'
    assert all(isinstance(results[k], (int, float)) for k in ('p50', 'p95', 'p99')), (
        'Latency percentiles must be numeric values'
    )


@then('the results include a Rust-to-Python speed ratio')
def step_results_include_speed_ratio(context: Context) -> None:
    """Verify results include a speed ratio comparison."""
    rust_p50 = context.rust_results['p50']
    python_p50 = context.python_results['p50']
    speed_ratio = python_p50 / rust_p50 if rust_p50 > 0 else float('inf')
    context.speed_ratio = speed_ratio
    assert speed_ratio > 0, 'Speed ratio must be positive'


@then('the benchmark methodology is documented')
def step_methodology_documented(context: Context) -> None:
    """Verify benchmark methodology is documented."""
    methodology_path = PROJECT_ROOT / 'docs' / 'benchmark-methodology.md'
    assert methodology_path.exists(), f'Benchmark methodology document not found at {methodology_path}'
    content = methodology_path.read_text()
    assert len(content) > 100, 'Methodology document appears to be a stub'
    assert 'warm-up' in content.lower() or 'warmup' in content.lower(), 'Methodology should describe warm-up strategy'


# ---------------------------------------------------------------------------
# Then steps: Nested resolution
# ---------------------------------------------------------------------------


@then('I receive latency comparison for nested resolution')
def step_receive_nested_comparison(context: Context) -> None:
    """Verify nested resolution latency is available for both containers."""
    assert 'nested_latency_us' in context.rust_results, 'Rust results missing nested resolution latency'
    assert 'nested_latency_us' in context.python_results, 'Python results missing nested resolution latency'


@then('the benchmark covers cold cache scenarios')
def step_benchmark_covers_cold_cache(context: Context) -> None:
    """Verify cold cache (first resolution) is measured."""
    assert 'cold_latency_us' in context.rust_results, 'Rust results missing cold cache latency'
    assert 'cold_latency_us' in context.python_results, 'Python results missing cold cache latency'


@then('the benchmark covers warm cache scenarios')
def step_benchmark_covers_warm_cache(context: Context) -> None:
    """Verify warm cache (subsequent resolution) is measured."""
    assert 'warm_latency_us' in context.rust_results, 'Rust results missing warm cache latency'
    assert 'warm_latency_us' in context.python_results, 'Python results missing warm cache latency'


# ---------------------------------------------------------------------------
# Then steps: Memory
# ---------------------------------------------------------------------------


@then('I receive memory usage for the Rust container')
def step_receive_rust_memory(context: Context) -> None:
    """Verify memory usage is reported for the Rust container."""
    assert 'memory_bytes' in context.rust_results, 'Rust results missing memory measurement'
    assert isinstance(context.rust_results['memory_bytes'], (int, float))
    assert context.rust_results['memory_bytes'] > 0


@then('I receive memory usage for the pure Python container')
def step_receive_python_memory(context: Context) -> None:
    """Verify memory usage is reported for the pure Python container."""
    assert 'memory_bytes' in context.python_results, 'Python results missing memory measurement'
    assert isinstance(context.python_results['memory_bytes'], (int, float))
    assert context.python_results['memory_bytes'] > 0


@then('the measurement excludes Python object overhead')
def step_measurement_excludes_object_overhead(context: Context) -> None:
    """Verify memory measurement isolates container overhead from Python objects."""
    assert 'container_overhead_bytes' in context.rust_results, 'Rust results missing container overhead measurement'
    assert 'container_overhead_bytes' in context.python_results, 'Python results missing container overhead measurement'


@then('both containers use the same test data')
def step_same_test_data(context: Context) -> None:
    """Verify both containers were populated with identical test data."""
    assert context.rust_results.get('singleton_count') == context.python_results.get('singleton_count'), (
        'Containers should have the same number of singletons'
    )


# ---------------------------------------------------------------------------
# Then steps: Startup / scan
# ---------------------------------------------------------------------------


@then('I receive scan duration for the Rust container')
def step_receive_rust_scan_duration(context: Context) -> None:
    """Verify scan duration is reported for the Rust container."""
    assert 'scan_duration_ms' in context.rust_results, 'Rust results missing scan duration'
    assert isinstance(context.rust_results['scan_duration_ms'], (int, float))


@then('I receive scan duration for the pure Python container')
def step_receive_python_scan_duration(context: Context) -> None:
    """Verify scan duration is reported for the pure Python container."""
    assert 'scan_duration_ms' in context.python_results, 'Python results missing scan duration'
    assert isinstance(context.python_results['scan_duration_ms'], (int, float))


@then('graph construction time is reported separately')
def step_graph_construction_separate(context: Context) -> None:
    """Verify graph construction time is broken out from scan time."""
    assert 'graph_construction_ms' in context.rust_results, 'Rust results missing graph construction time'
    assert 'graph_construction_ms' in context.python_results, 'Python results missing graph construction time'


# ---------------------------------------------------------------------------
# Then steps: Concurrency
# ---------------------------------------------------------------------------


@then('both containers produce correct results')
def step_both_produce_correct_results(context: Context) -> None:
    """Verify concurrent resolution produces correct instances."""
    assert context.rust_results.get('all_correct') is True, (
        'Rust container produced incorrect results under concurrency'
    )
    assert context.python_results.get('all_correct') is True, (
        'Python container produced incorrect results under concurrency'
    )


@then('neither container has race conditions')
def step_no_race_conditions(context: Context) -> None:
    """Verify no race conditions were detected during concurrent resolution."""
    assert context.rust_results.get('race_conditions_detected') is False, 'Rust container had race conditions'
    assert context.python_results.get('race_conditions_detected') is False, 'Python container had race conditions'


@then('throughput is compared between the two containers')
def step_throughput_compared(context: Context) -> None:
    """Verify throughput (resolutions per second) is available for both."""
    assert 'throughput_rps' in context.rust_results, 'Rust results missing throughput measurement'
    assert 'throughput_rps' in context.python_results, 'Python results missing throughput measurement'
    assert context.rust_results['throughput_rps'] > 0
    assert context.python_results['throughput_rps'] > 0


# ---------------------------------------------------------------------------
# Then steps: FastAPI integration
# ---------------------------------------------------------------------------


@then('I receive p99 request latency for the Rust container')
def step_rust_fastapi_p99(context: Context) -> None:
    """Verify p99 request latency is available for the Rust backend."""
    assert 'p99_request_ms' in context.rust_results, 'Rust results missing p99 request latency'
    assert isinstance(context.rust_results['p99_request_ms'], (int, float))


@then('I receive p99 request latency for the pure Python container')
def step_python_fastapi_p99(context: Context) -> None:
    """Verify p99 request latency is available for the pure Python backend."""
    assert 'p99_request_ms' in context.python_results, 'Python results missing p99 request latency'
    assert isinstance(context.python_results['p99_request_ms'], (int, float))


@then('the latency difference is quantified in milliseconds')
def step_latency_difference_quantified(context: Context) -> None:
    """Verify the latency difference is explicitly calculated."""
    rust_p99 = context.rust_results['p99_request_ms']
    python_p99 = context.python_results['p99_request_ms']
    difference_ms = python_p99 - rust_p99
    context.latency_difference_ms = difference_ms
    assert isinstance(difference_ms, (int, float)), 'Latency difference should be a numeric value in milliseconds'


# ---------------------------------------------------------------------------
# Then steps: Results document
# ---------------------------------------------------------------------------


@then('it includes a clear "Keep Rust" or "Remove Rust" recommendation')
def step_includes_recommendation(context: Context) -> None:
    """Verify the results document includes a clear recommendation."""
    content = context.results_content
    has_keep = 'Keep Rust' in content
    has_remove = 'Remove Rust' in content
    assert has_keep or has_remove, "Results document must include 'Keep Rust' or 'Remove Rust' recommendation"


@then('the decision criteria are explicitly stated')
def step_decision_criteria_stated(context: Context) -> None:
    """Verify the results document states the decision criteria."""
    content = context.results_content
    assert 'Decision Criteria' in content or 'decision criteria' in content, (
        'Results document must include decision criteria section'
    )


@then('the document includes the acceptance thresholds table')
def step_includes_thresholds_table(context: Context) -> None:
    """Verify the results document includes the acceptance thresholds."""
    content = context.results_content
    required_metrics = [
        'Resolution speed',
        'Memory usage',
        'Startup time',
        'Concurrent throughput',
    ]
    for metric in required_metrics:
        assert metric.lower() in content.lower(), f"Results document missing threshold for: '{metric}'"
