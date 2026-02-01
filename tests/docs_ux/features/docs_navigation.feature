@docs_ux
Feature: Developers find answers quickly through unified documentation
  As a developer evaluating or using dioxide
  I want documentation that answers my questions quickly
  So that I can be productive without frustration

  Background:
    Given the dioxide documentation site is available

  @quickstart
  Scenario: New user finds quickstart in under 30 seconds
    When I arrive at the documentation homepage
    Then I see a prominent "Quick Start" link in the navigation
    And clicking "Quick Start" loads within 2 seconds
    And the quick start page shows working code within the first viewport
    And each code block has a "Copy" button

  @service_adapter
  Scenario: Developer finds @service vs @adapter guidance
    When I use the documentation search for "service adapter"
    Then the search results include "services-vs-adapters" guide
    And the guide appears in the top 3 results
    And the guide includes a decision tree diagram
    And the decision tree fits within 2 scroll lengths

  @why_dioxide
  Scenario: Skeptic finds "why dioxide" justification
    When I navigate to the documentation homepage
    And I look for comparison or "why" content
    Then I find a "Why dioxide?" page within 2 clicks from home
    And the page compares dioxide to at least dependency-injector
    And the page includes an "Anti-goals" or "What dioxide doesn't do" section

  @testing
  Scenario: Tester finds testing patterns
    When I use the documentation search for "testing"
    Then the search results include the testing guide
    And the testing guide explains "fakes at the seams" philosophy
    And the guide includes pytest fixture code examples
    And the examples are complete and copy-pasteable

  @contributing
  Scenario: Contributor understands design decisions
    When I navigate to the documentation homepage
    And I look for architecture or design content
    Then I find design principles within 3 clicks from home
    And I can find ADRs (Architecture Decision Records)
    And the design section clearly marks internal vs public docs

  @error_messages
  Scenario: Error messages link to troubleshooting
    When I see an error message from dioxide
    Then the error includes a URL to documentation
    And that URL leads to relevant troubleshooting content
    And the troubleshooting page provides actionable steps
