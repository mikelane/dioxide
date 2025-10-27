Feature: Component Decorator Registration
  As a Python developer
  I want to mark classes as components with a decorator
  So that the DI container can auto-discover and manage them

  Background:
    Given the dioxide DI container exists
    And the global component registry is empty

  Scenario: Registering a class with @component decorator
    Given a Python class UserService
    When I apply the @component decorator to UserService
    Then UserService appears in the global component registry
    And UserService has default SINGLETON scope

  Scenario: Specifying FACTORY scope for a component
    Given a Python class RequestHandler
    When I apply @component(scope=Scope.FACTORY) to RequestHandler
    Then RequestHandler appears in the global component registry
    And RequestHandler has FACTORY scope

  Scenario: Multiple classes can be registered as components
    Given three Python classes: ServiceA, ServiceB, ServiceC
    When I apply @component to all three classes
    Then all three classes appear in the global component registry
    And each class retains its scope setting

  Scenario: Component decorator preserves class functionality
    Given a Python class Calculator with methods add() and subtract()
    When I apply the @component decorator to Calculator
    Then Calculator instances can still call add() and subtract()
    And the class behaves identically to an undecorated class

  Scenario: Component decorator works with classes without __init__
    Given a Python class StatelessService without an __init__ method
    When I apply the @component decorator to StatelessService
    Then StatelessService appears in the global component registry
    And StatelessService can be instantiated normally
