@issue-374
Feature: dioxide API feels natural and has minimal ceremony
  As a Python developer
  I want dioxide's API to feel Pythonic and lightweight
  So that I can use dependency injection without fighting the framework

  # These scenarios define acceptance criteria for developer ergonomics.
  # The epic (#368) tracks improvements to make dioxide feel natural,
  # minimize ceremony, and provide clear guidance when things go wrong.

  Scenario: Simple adapter syntax fits on one line
    Given I define a Protocol called EmailPort
    When I apply the @adapter.for_ decorator with a profile
    Then the full decorator fits on one line
    And the syntax reads as @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
    And no other decorators are required for basic usage

  Scenario: Lifecycle decorator is optional for adapters without resource needs
    Given I have an adapter for EmailPort without lifecycle needs
    When I register and resolve the adapter
    Then the adapter works without @lifecycle decorator
    And the adapter works without initialize() or dispose() methods

  Scenario: Lifecycle decorator works with standard async context manager protocol
    Given I have a class with __aenter__ and __aexit__ methods
    When I check how @lifecycle integrates with async context managers
    Then @lifecycle requires custom initialize() and dispose() methods
    And there is clear documentation explaining the lifecycle protocol

  @wip
  Scenario: Profile.ALL displays cleanly in error messages and repr
    Given I have the Profile.ALL constant
    When I check its string representations
    Then repr shows "Profile.ALL" rather than the raw wildcard
    And str conversion in error messages avoids showing raw "*"

  Scenario: @service docstring explains its purpose for IDE hover
    When I inspect the @service decorator docstring
    Then the docstring mentions "core business logic"
    And the docstring includes a usage example
    And the docstring mentions "profile-agnostic" behavior

  @wip
  Scenario: @adapter.for_ docstring explains its purpose for IDE hover
    When I inspect the @adapter.for_ decorator docstring
    Then the docstring mentions "swappable implementations"
    And the docstring includes an example with profile parameter
    And the docstring mentions implementing a port

  @wip
  Scenario: Wrong decorator usage produces a helpful error message
    Given I accidentally use @service on a class that implements a port
    And a separate adapter exists for the same port
    When I try to resolve the port from the container
    Then the error message provides guidance about the correct decorator
    And the error message mentions @adapter.for_ as an alternative

  @wip
  Scenario: Profile class provides IDE-friendly autocomplete descriptions
    When I inspect the Profile class and its constants
    Then each built-in profile constant has a descriptive docstring or annotation
    And none of the descriptions expose the raw "*" implementation detail
    And Profile.ALL description refers to "all profiles" or "universal"
