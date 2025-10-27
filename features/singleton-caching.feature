Feature: Singleton Scope Caching
  As a Python developer
  I want SINGLETON-scoped components to be cached
  So that expensive initialization happens only once

  Background:
    Given the dioxide DI container exists
    And container.scan() has discovered all @component classes

  Scenario: Singleton components are cached on first resolution
    Given ExpensiveService is marked @component (default SINGLETON)
    When I resolve ExpensiveService for the first time
    Then ExpensiveService.__init__ is called once
    And the instance is stored in the singleton cache

  Scenario: Subsequent resolutions return cached instance
    Given ExpensiveService is marked @component (default SINGLETON)
    And I have already resolved ExpensiveService once
    When I resolve ExpensiveService again
    Then ExpensiveService.__init__ is NOT called again
    And I receive the same instance as before

  Scenario: Different singleton types are cached independently
    Given ServiceA and ServiceB are both SINGLETON-scoped
    When I resolve ServiceA and then ServiceB
    Then each service is cached separately
    And resolving ServiceA does not return ServiceB

  Scenario: Factory-scoped components are NOT cached
    Given RequestHandler is marked @component(scope=Scope.FACTORY)
    When I resolve RequestHandler three times
    Then RequestHandler.__init__ is called three times
    And I receive three different instances

  Scenario: Singleton caching works for injected dependencies
    Given Logger is SINGLETON-scoped
    And ServiceA depends on Logger
    And ServiceB depends on Logger
    When I resolve both ServiceA and ServiceB
    Then Logger.__init__ is called exactly once
    And both services receive the same Logger instance
