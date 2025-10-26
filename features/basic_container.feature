Feature: Basic Container Structure
  As a Python developer using dioxide
  I want a reliable dependency injection container
  So that I can manage my application's dependencies safely and efficiently

  # This feature implements the foundational Container structure that will
  # serve as the core of the dioxide dependency injection system. The Container
  # provides thread-safe dependency storage and retrieval, enabling developers
  # to build loosely-coupled Python applications.
  #
  # Key architectural decisions:
  # - Rust-backed implementation for performance and thread safety
  # - HashMap-based storage for O(1) lookup
  # - PyO3 bindings for seamless Python integration
  # - Two-layer API design (Rust core + Python wrapper)

  Scenario: Developer creates a new container
    Given the dioxide library is available
    When a developer creates a new Container instance
    Then the Container exists
    And the Container is ready to accept registrations

  Scenario: Developer checks if new container is empty
    Given a developer has created a new Container
    When the developer checks the container state
    Then the Container reports it is empty
    And the Container has zero registered dependencies

  Scenario: Developer attempts to resolve from empty container
    Given a developer has created a new Container
    When the developer attempts to resolve a dependency "UserService"
    Then the Container raises a DependencyNotFoundError
    And the error message indicates "UserService" is not registered

  Scenario: Developer verifies container thread safety guarantee
    Given a developer has created a new Container
    When the developer accesses the container from multiple threads
    Then the Container maintains data integrity across all threads
    And no race conditions occur during concurrent access

  Scenario: Developer introspects container contents
    Given a developer has created a new Container
    When the developer requests a list of registered dependencies
    Then the Container returns an empty list
    And the response is a valid Python iterable

  Scenario: Developer creates multiple independent containers
    Given a developer has created a Container named "container_a"
    And a developer has created a Container named "container_b"
    When the developer modifies "container_a"
    Then "container_b" remains unchanged
    And the containers maintain independent state
