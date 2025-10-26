Feature: Provider Registration
  As a Python developer using dioxide
  I want to register different types of providers in the container
  So that I can manage object creation and lifecycle appropriately

  Background:
    Given the dioxide library is available

  Scenario: Developer registers and resolves an instance provider
    Given a developer has created a new Container
    And the developer has created a configuration object with database settings
    When the developer registers the configuration object as an instance provider
    And the developer resolves the configuration from the container twice
    Then the developer receives the exact same configuration object both times

  Scenario: Developer registers and resolves a class provider
    Given a developer has created a new Container
    And the developer has defined a UserService class
    When the developer registers the UserService class as a class provider
    And the developer resolves UserService from the container multiple times
    Then the developer receives new UserService instances each time

  Scenario: Developer registers and resolves a factory provider
    Given a developer has created a new Container
    And the developer has a factory function that creates database connections
    When the developer registers the factory function as a factory provider
    And the developer resolves a database connection from the container multiple times
    Then the factory function is called each time a resolution occurs
