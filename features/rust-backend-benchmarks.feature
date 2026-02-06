@issue-375 @wip
Feature: Rust backend performance is clearly measured and documented
  As a project maintainer
  I want objective benchmarks comparing Rust vs pure Python
  So that I can justify keeping or removing the Rust backend

  Scenario: Resolution speed is benchmarked fairly
    Given a benchmark suite comparing Rust and pure Python containers
    And both containers have a singleton service registered
    When I run singleton resolution 10000 times on each container
    Then I receive p50, p95, and p99 latencies for the Rust container
    And I receive p50, p95, and p99 latencies for the pure Python container
    And the results include a Rust-to-Python speed ratio
    And the benchmark methodology is documented

  Scenario: Nested dependency resolution is benchmarked
    Given a benchmark suite comparing Rust and pure Python containers
    And both containers have a dependency chain of depth 4
    When I resolve the top-level service 1000 times on each container
    Then I receive latency comparison for nested resolution
    And the benchmark covers cold cache scenarios
    And the benchmark covers warm cache scenarios

  Scenario: Memory usage is compared
    Given a benchmark suite comparing Rust and pure Python containers
    And both containers have 1000 singletons registered
    When I measure memory after resolving all singletons on each container
    Then I receive memory usage for the Rust container
    And I receive memory usage for the pure Python container
    And the measurement excludes Python object overhead
    And both containers use the same test data

  Scenario: Startup time is measured
    Given a benchmark suite comparing Rust and pure Python containers
    And both containers have 100 adapters to discover
    When I measure container scan time on each container
    Then I receive scan duration for the Rust container
    And I receive scan duration for the pure Python container
    And graph construction time is reported separately

  Scenario: Concurrent resolution is tested
    Given a benchmark suite comparing Rust and pure Python containers
    And both containers have singletons registered
    When I run 10 threads resolving singletons simultaneously for 1 second
    Then both containers produce correct results
    And neither container has race conditions
    And throughput is compared between the two containers

  Scenario: Real-world FastAPI benchmark exists
    Given a FastAPI application with 50 adapters
    And it can use either the Rust or pure Python container
    When I measure request latency with dependency resolution
    Then I receive p99 request latency for the Rust container
    And I receive p99 request latency for the pure Python container
    And the latency difference is quantified in milliseconds

  Scenario: Results are documented with recommendation
    Given all benchmark scenarios have been executed
    And benchmark results have been collected
    When I review the benchmark results document
    Then it includes a clear "Keep Rust" or "Remove Rust" recommendation
    And the decision criteria are explicitly stated
    And the document includes the acceptance thresholds table
