"""Step definitions for provider registration tests."""

from behave import given, then, when
from behave.runner import Context


class ConfigObject:
    """Test configuration object."""

    def __init__(self, db_host: str, db_port: int) -> None:
        self.db_host = db_host
        self.db_port = db_port


class UserService:
    """Test user service class."""

    def __init__(self) -> None:
        self.id = id(self)


class DatabaseConnection:
    """Test database connection class."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string


@given('the developer has created a configuration object with database settings')
def step_create_config_object(context: Context) -> None:
    """Create a configuration object for testing."""
    object.__setattr__(context, 'config', ConfigObject('localhost', 5432))


@when('the developer registers the configuration object as an instance provider')
def step_register_instance(context: Context) -> None:
    """Register the configuration object as an instance provider."""
    context.container.register_instance(ConfigObject, context.config)


@when('the developer resolves the configuration from the container twice')
def step_resolve_config_twice(context: Context) -> None:
    """Resolve the configuration twice to test instance provider behavior."""
    object.__setattr__(context, 'resolved1', context.container.resolve(ConfigObject))
    object.__setattr__(context, 'resolved2', context.container.resolve(ConfigObject))


@then('the developer receives the exact same configuration object both times')
def step_verify_same_instance(context: Context) -> None:
    """Verify that both resolutions return the same object reference."""
    assert context.resolved1 is context.resolved2, 'Instance provider should return the same object reference'
    assert context.resolved1 is context.config, 'Instance provider should return the original object'
    assert context.resolved2 is context.config, 'Instance provider should return the original object'


@given('the developer has defined a UserService class')
def step_define_user_service(context: Context) -> None:
    """Define a UserService class for testing."""
    object.__setattr__(context, 'user_service_class', UserService)


@when('the developer registers the UserService class as a class provider')
def step_register_class(context: Context) -> None:
    """Register the UserService class as a class provider."""
    context.container.register_class(UserService, context.user_service_class)


@when('the developer resolves UserService from the container multiple times')
def step_resolve_class_multiple_times(context: Context) -> None:
    """Resolve UserService multiple times to test class provider behavior."""
    object.__setattr__(context, 'instance1', context.container.resolve(UserService))
    object.__setattr__(context, 'instance2', context.container.resolve(UserService))
    object.__setattr__(context, 'instance3', context.container.resolve(UserService))


@then('the developer receives new UserService instances each time')
def step_verify_different_instances(context: Context) -> None:
    """Verify that each resolution creates a new instance."""
    assert isinstance(context.instance1, UserService), 'Should be a UserService instance'
    assert isinstance(context.instance2, UserService), 'Should be a UserService instance'
    assert isinstance(context.instance3, UserService), 'Should be a UserService instance'

    assert context.instance1 is not context.instance2, 'Class provider should create new instances'
    assert context.instance2 is not context.instance3, 'Class provider should create new instances'
    assert context.instance1 is not context.instance3, 'Class provider should create new instances'


@given('the developer has a factory function that creates database connections')
def step_define_factory(context: Context) -> None:
    """Define a factory function for creating database connections."""
    object.__setattr__(context, 'call_count', 0)

    def create_db_connection() -> DatabaseConnection:
        count = context.call_count + 1
        object.__setattr__(context, 'call_count', count)
        return DatabaseConnection(f'postgresql://localhost:5432/db_{count}')

    object.__setattr__(context, 'factory', create_db_connection)


@when('the developer registers the factory function as a factory provider')
def step_register_factory(context: Context) -> None:
    """Register the factory function as a factory provider."""
    context.container.register_factory(DatabaseConnection, context.factory)


@when('the developer resolves a database connection from the container multiple times')
def step_resolve_factory_multiple_times(context: Context) -> None:
    """Resolve the database connection multiple times to test factory provider behavior."""
    object.__setattr__(context, 'connection1', context.container.resolve(DatabaseConnection))
    object.__setattr__(context, 'connection2', context.container.resolve(DatabaseConnection))
    object.__setattr__(context, 'connection3', context.container.resolve(DatabaseConnection))


@then('the factory function is called each time a resolution occurs')
def step_verify_factory_called(context: Context) -> None:
    """Verify that the factory function is called for each resolution."""
    assert context.call_count == 3, f'Factory should have been called 3 times, was called {context.call_count} times'

    assert isinstance(context.connection1, DatabaseConnection), 'Should be a DatabaseConnection instance'
    assert isinstance(context.connection2, DatabaseConnection), 'Should be a DatabaseConnection instance'
    assert isinstance(context.connection3, DatabaseConnection), 'Should be a DatabaseConnection instance'

    assert context.connection1 is not context.connection2, 'Factory provider should create new instances'
    assert context.connection2 is not context.connection3, 'Factory provider should create new instances'
    assert context.connection1 is not context.connection3, 'Factory provider should create new instances'

    assert context.connection1.connection_string == 'postgresql://localhost:5432/db_1'
    assert context.connection2.connection_string == 'postgresql://localhost:5432/db_2'
    assert context.connection3.connection_string == 'postgresql://localhost:5432/db_3'
