# How to Use These Docs

Choose your path based on what you want to accomplish.

---

## "I want to try dioxide quickly"

**Time: 15 minutes**

Get dioxide running with a minimal example to understand the core concepts.

1. {doc}`user_guide/getting_started` - Install and build your first container
2. {doc}`guides/choosing-decorators` - Which decorator: @service or @adapter? (decision tree)
3. {doc}`examples/01-basic-dependency-injection` - See a complete working example
4. {doc}`examples/02-email-service-with-profiles` - Understand profile switching

---

## "I'm evaluating dioxide for my project"

**Time: 30 minutes**

Understand what dioxide offers and whether it fits your needs.

1. {doc}`why-dioxide` - Philosophy, feature comparison, and honest limitations
2. {doc}`user_guide/hexagonal_architecture` - How dioxide maps to ports-and-adapters
3. {doc}`user_guide/package_scanning` - How scanning works, side effects, and best practices
4. {doc}`TESTING_GUIDE` - Testing philosophy (fakes over mocks)
5. {doc}`migration-from-dependency-injector` - Coming from another DI framework?

---

## "I'm integrating with a web framework"

**Time: 20 minutes**

Get dioxide working with your framework of choice.

### FastAPI

1. {doc}`cookbook/fastapi` - Lifespan, dependency injection, and testing endpoints
2. {doc}`examples/04-lifecycle-management` - Async startup/shutdown patterns
3. {doc}`guides/lifecycle-async-patterns` - Understanding async lifecycle with sync resolution

### Django

1. {doc}`integrations/django` - Django-specific integration guide

### Other Frameworks

1. {doc}`user_guide/getting_started` - Core container patterns work everywhere
2. {doc}`guides/scoping` - Request scoping for web applications
3. {doc}`guides/lifecycle-async-patterns` - Async lifecycle in sync frameworks (Flask, Django)

---

## "I want to understand the testing philosophy"

**Time: 45 minutes**

Learn why dioxide prefers fakes over mocks and how to test effectively.

1. {doc}`TESTING_GUIDE` - Comprehensive testing philosophy and patterns
2. {doc}`user_guide/testing_with_fakes` - Practical testing techniques
3. {doc}`cookbook/testing` - Copy-paste test fixtures and patterns
4. {doc}`migration-from-mocks` - Transitioning from mock-heavy tests

---

## "I need the API reference"

Jump directly to the technical documentation.

- {doc}`api/index` - Auto-generated API documentation for all public classes and functions

---

## "I want practical recipes"

Browse the cookbook for copy-paste solutions to common problems.

- {doc}`cookbook/index` - All recipes organized by category
- {doc}`cookbook/configuration` - Pydantic Settings integration
- {doc}`cookbook/database` - SQLAlchemy and repository patterns
- {doc}`cookbook/testing` - Test fixtures and patterns

---

## Learning Path Recommendations

| Your Background | Recommended Path |
|-----------------|------------------|
| New to DI | Quick start, then examples 1-4 in order |
| Using dependency-injector | Why dioxide, then migration guide |
| Familiar with hexagonal architecture | Hexagonal architecture guide, then testing |
| Mock-heavy test suite | Testing philosophy, then migration from mocks |
| FastAPI developer | FastAPI cookbook, then lifecycle async patterns |
| Flask/Django developer | Lifecycle async patterns, then cookbook |
| Confused about decorators | {doc}`guides/choosing-decorators` - visual decision tree |
