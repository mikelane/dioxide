@issue-373 @wip
Feature: Package scanning is fast, predictable, and controllable
  As a developer using dioxide
  I want scanning to be fast and not import unnecessary modules
  So that my application starts quickly and predictably

  Background:
    Given a fresh dioxide container
    And a test package "scan_perf_pkg" with multiple modules

  Scenario: Lazy scanning avoids importing unused modules
    Given "scan_perf_pkg.expensive" contains a decorator that tracks when it is imported
    And "scan_perf_pkg.cheap" contains a simple adapter
    When I scan "scan_perf_pkg" with lazy loading enabled
    And I only resolve components from "scan_perf_pkg.cheap"
    Then "scan_perf_pkg.expensive" has not been imported

  Scenario: Scan plan shows modules without importing
    Given "scan_perf_pkg" contains 5 modules with adapters
    When I call container.scan_plan for "scan_perf_pkg"
    Then I receive a list of 5 module paths
    And no adapters are registered yet
    And calling scan afterward registers the adapters

  Scenario: Narrow scanning only imports specified packages
    Given I have "scan_perf_pkg.adapters.prod" with a ProductionAdapter
    And I have "scan_perf_pkg.adapters.dev" with a DevelopmentAdapter
    When I scan only "scan_perf_pkg.adapters.prod"
    Then ProductionAdapter is registered
    And DevelopmentAdapter is not registered
    And "scan_perf_pkg.adapters.dev" has not been imported

  Scenario: Scan statistics report what was registered
    Given I have a package with 3 services and 5 adapters
    When I scan the package with statistics enabled
    Then the statistics show 3 services registered
    And the statistics show 5 adapters registered
    And the statistics include scan duration in milliseconds

  Scenario: Strict mode warns about module-level side effects
    Given "scan_perf_pkg.side_effect" has module-level code that prints to stdout
    When I scan "scan_perf_pkg" with strict mode enabled
    Then I see a warning mentioning "scan_perf_pkg.side_effect"
    And the warning mentions "module-level side effect"

  Scenario: Scanning without package parameter uses pre-imported modules
    Given I have already imported "scan_perf_pkg.explicit" containing ExplicitAdapter
    And "scan_perf_pkg.not_imported" is not imported
    When I call container.scan with profile TEST and no package parameter
    Then ExplicitAdapter is registered
    And adapters in "scan_perf_pkg.not_imported" are not registered

  Scenario: Large package scanning meets performance target
    Given I have a package with 100 modules containing adapters
    When I scan the package
    Then the scan completes in under 500 milliseconds
