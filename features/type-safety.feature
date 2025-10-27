Feature: Type Safety and mypy Integration
  As a Python developer
  I want full type safety with mypy
  So that type errors are caught at development time

  Background:
    Given mypy is configured in strict mode
    And the dioxide package is installed

  Scenario: Container.resolve() has proper type hints
    Given UserService is marked as @component
    When I write code: service = container.resolve(UserService)
    Then mypy infers the type of service as UserService
    And no type errors are reported

  Scenario: Type hints work with generic types
    Given Repository[User] is a generic class
    And I register Repository[User] with the container
    When I resolve Repository[User]
    Then mypy understands the generic type parameter
    And type checking passes

  Scenario: Invalid type resolutions are caught by mypy
    Given UserService is registered with the container
    When I write code: db = container.resolve(UserService)
    And I try to call db.execute_query() (a method not in UserService)
    Then mypy reports a type error
    And the code does not pass type checking

  Scenario: Decorator preserves type information
    Given a class ServiceA with methods foo() and bar()
    When I apply @component to ServiceA
    Then mypy still sees foo() and bar() as valid methods
    And autocomplete works in IDEs

  Scenario: Constructor injection is type-safe
    Given UserController has __init__(self, service: UserService)
    And UserService is marked as @component
    When the container resolves UserController
    Then mypy verifies that UserService is compatible
    And mismatched types are caught at type-check time
