@issue-377 @wip
Feature: API stability and migration support builds developer trust
  As a developer who was burned by the v2.0 migration
  I want clear stability policies and migration support
  So that I can trust dioxide for long-term projects

  # This feature verifies that dioxide provides the documentation,
  # tooling, and infrastructure that developers need to confidently
  # adopt the framework for production use. Each scenario maps to
  # a deliverable in Epic #371 (Breaking Change Prevention).

  Scenario: v2.0 migration guide exists and is complete
    Given I search for migration documentation
    When I find the v1.x to v2.0 migration guide
    Then the guide acknowledges the breaking change
    And the guide lists all breaking changes itemized
    And each breaking change has before/after code examples
    And the guide includes find-replace patterns or codemod instructions

  Scenario: API stability policy is documented
    Given I navigate to the documentation directory
    When I look for stability or versioning information
    Then I find an API stability policy document
    And it explains the semantic versioning commitment
    And it lists which APIs are stable versus internal
    And it explains the deprecation process

  Scenario: Stable APIs are clearly marked in documentation
    Given I read the API reference documentation
    When I look at a public API like Container or adapter
    Then it is marked as stable or has no instability warning
    And when I look at internal APIs like _registry
    Then internal APIs are marked with no stability guarantee

  Scenario: Deprecation warnings exist in code infrastructure
    Given the dioxide package is importable
    When I check for deprecation warning infrastructure
    Then a deprecation utility function exists
    And the utility accepts a version and replacement message
    And calling it emits a DeprecationWarning

  Scenario: CHANGELOG marks breaking changes clearly
    Given I read the CHANGELOG file
    When I look at major version entries
    Then breaking changes are marked with a BREAKING indicator
    And each breaking change links to migration instructions
    And the affected API is clearly identified

  Scenario: Future migration has tooling support documentation
    Given a future major version may be released
    When I look for migration support documentation
    Then I find documentation describing automated migration options
    And there are at least find-replace patterns documented
    And codemod tooling is mentioned as an option
