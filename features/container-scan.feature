Feature: Container Auto-Discovery via scan()
  As a Python developer
  I want the container to automatically discover @component classes
  So that I don't have to manually register every dependency

  Background:
    Given the dioxide DI container exists
    And several classes are decorated with @component

  Scenario: Container discovers all @component classes
    Given three classes marked with @component: UserService, EmailService, Logger
    When I call container.scan()
    Then the container has providers for UserService, EmailService, and Logger
    And each provider is registered with the correct scope

  Scenario: Container inspects constructor dependencies
    Given UserController depends on UserService (via __init__ type hints)
    And UserService is marked with @component
    And UserController is marked with @component
    When I call container.scan()
    Then the container can resolve UserController
    And UserService is automatically injected into UserController's constructor

  Scenario: Container handles classes without dependencies
    Given StatelessService has no __init__ parameters
    And StatelessService is marked with @component
    When I call container.scan()
    Then the container can resolve StatelessService
    And a valid StatelessService instance is returned

  Scenario: Container respects scope annotations during scan
    Given SingletonService is marked @component (default SINGLETON)
    And FactoryService is marked @component(scope=Scope.FACTORY)
    When I call container.scan()
    Then resolving SingletonService twice returns the same instance
    And resolving FactoryService twice returns different instances

  Scenario: Scanning multiple times is idempotent
    Given several @component classes exist
    When I call container.scan() twice
    Then no duplicate providers are registered
    And the container state is identical to scanning once
