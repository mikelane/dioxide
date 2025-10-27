Feature: Constructor Dependency Injection
  As a Python developer
  I want constructor parameters to be auto-injected
  So that I can write loosely-coupled, testable code

  Background:
    Given the dioxide DI container exists
    And container.scan() has discovered all @component classes

  Scenario: Simple constructor injection
    Given UserService is marked as @component
    And UserController depends on UserService (via __init__ type hint)
    When I resolve UserController from the container
    Then UserController receives a UserService instance automatically
    And I did not manually create UserService

  Scenario: Multi-level dependency chains
    Given Logger is marked as @component
    And EmailService depends on Logger
    And UserService depends on EmailService
    When I resolve UserService from the container
    Then UserService receives EmailService with Logger injected
    And the entire dependency chain is resolved automatically

  Scenario: Multiple dependencies in a single constructor
    Given Logger, Database, and Cache are all @component
    And UserRepository depends on all three (via __init__ type hints)
    When I resolve UserRepository from the container
    Then UserRepository receives all three dependencies
    And each dependency is properly initialized

  Scenario: Resolving the same dependency multiple times
    Given UserService is marked @component with SINGLETON scope
    And ControllerA and ControllerB both depend on UserService
    When I resolve both controllers from the container
    Then both controllers receive the SAME UserService instance
    And UserService was only instantiated once

  Scenario: Factory-scoped dependencies create new instances
    Given RequestHandler is marked @component(scope=Scope.FACTORY)
    And ControllerA and ControllerB both depend on RequestHandler
    When I resolve both controllers from the container
    Then each controller receives a DIFFERENT RequestHandler instance
    And RequestHandler was instantiated twice
