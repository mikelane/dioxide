Feature: Manual Provider Registration
  As a Python developer
  I want to manually register providers when needed
  So that I can handle edge cases not covered by auto-discovery

  Background:
    Given the dioxide DI container exists

  Scenario: Registering a singleton provider manually
    Given a Python class DatabaseConnection
    And a factory function that creates DatabaseConnection instances
    When I call container.register_singleton(DatabaseConnection, factory_fn)
    Then the container can resolve DatabaseConnection
    And the same instance is returned on every resolve

  Scenario: Registering a factory provider manually
    Given a Python class RequestContext
    And a factory function that creates RequestContext instances
    When I call container.register_factory(RequestContext, factory_fn)
    Then the container can resolve RequestContext
    And a new instance is created on every resolve

  Scenario: Manual registration takes precedence over scan()
    Given ServiceA is marked with @component
    And I manually register a custom provider for ServiceA
    When I call container.scan()
    Then the container uses my custom provider
    And the @component registration is ignored

  Scenario: Manually registering a provider for an interface
    Given an abstract class IEmailService
    And a concrete class SmtpEmailService
    And a factory function that returns SmtpEmailService instances
    When I call container.register_singleton(IEmailService, factory_fn)
    Then resolving IEmailService returns a SmtpEmailService instance
    And type checkers accept IEmailService as a valid dependency
