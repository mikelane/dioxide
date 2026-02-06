@issue-376 @wip
Feature: Fakes philosophy is convincingly documented
  As a developer skeptical of "fakes in production code"
  I want clear explanations and compelling examples
  So that I can understand and adopt the pattern

  Scenario: Mock vs Fake comparison exists and is fair
    Given I navigate to the testing documentation
    When I look for mock vs fake comparison
    Then I find a dedicated comparison section
    And the section shows at least 3 concrete problems with mocks
    And each problem has a before mock and after fake code example
    And the comparison acknowledges when mocks are still appropriate

  Scenario: Problems with mocks are demonstrated not asserted
    Given I read the mock problems section
    When I examine each problem description
    Then each includes runnable code showing the problem
    And the mock examples demonstrate real failure modes
    And the examples are not strawman intentionally bad mock usage

  Scenario: Fakes in production code deployment concern is explained
    Given I read about fakes in production code
    When I look for deployment concerns
    Then I find an explanation of how Profile.PRODUCTION excludes fakes
    And I see that fake code exists but is never instantiated in production
    And I understand the trade-off of code present vs code executed

  Scenario: Writing good fakes guide exists
    Given I want to write my first fake adapter
    When I search for writing fakes guidance
    Then I find a guide with common patterns
    And the guide covers the InMemoryRepository pattern
    And the guide covers the FakeClock pattern
    And the guide covers the FakeHttpClient pattern

  Scenario: Migration from mocks to fakes is documented
    Given I have an existing codebase using mocks
    When I search for migration guidance
    Then I find a step-by-step migration guide
    And the guide shows before mock and after fake test code
    And the migration is incremental not all-or-nothing

  Scenario: FAQ addresses common skepticism
    Given I have doubts about the fakes approach
    When I look at the FAQ section
    Then I find an answer for "Why not just use @patch?"
    And I find an answer for "Don't fakes require more work?"
    And I find an answer for "What about external APIs I can't fake?"
    And each answer is substantive not dismissive
