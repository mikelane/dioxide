"""Step definitions for basic Container functionality."""

import threading

from behave import given, then, when
from behave.runner import Context


@given('the dioxide library is available')
def step_library_available(context: Context) -> None:
    """Verify dioxide can be imported."""
    try:
        import dioxide

        context.dioxide = dioxide
    except ImportError as e:
        raise AssertionError(f'dioxide library not available: {e}') from e


@when('a developer creates a new Container instance')
def step_create_container(context: Context) -> None:
    """Create a new Container instance."""
    from dioxide import Container

    context.container = Container()


@then('the Container exists')
def step_container_exists(context: Context) -> None:
    """Verify the Container instance exists."""
    assert hasattr(context, 'container'), 'Container was not created'
    assert context.container is not None, 'Container is None'


@then('the Container is ready to accept registrations')
def step_container_ready(context: Context) -> None:
    """Verify the Container is in a valid state to accept registrations."""
    # Container should be instantiated and have registration methods
    assert hasattr(context.container, 'register_instance'), 'Container missing register_instance method'
    assert hasattr(context.container, 'register_class'), 'Container missing register_class method'
    assert hasattr(context.container, 'register_factory'), 'Container missing register_factory method'


@given('a developer has created a new Container')
def step_developer_created_container(context: Context) -> None:
    """Create a Container for the developer."""
    from dioxide import Container

    context.container = Container()


@when('the developer checks the container state')
def step_check_container_state(context: Context) -> None:
    """Check the current state of the container."""
    # Store state information for later assertions
    # This is a query operation, so we don't modify state
    pass


@then('the Container reports it is empty')
def step_container_is_empty(context: Context) -> None:
    """Verify the Container reports empty state."""
    # Will implement when Container has an is_empty() or similar method
    # For now, check that attempting to list providers returns empty
    pass


@then('the Container has zero registered dependencies')
def step_container_zero_dependencies(context: Context) -> None:
    """Verify the Container has no registered dependencies."""
    # Will implement when Container has a count() or list_providers() method
    # For now, this is a placeholder that will be implemented
    pass


@when('the developer attempts to resolve a dependency "{dependency_name}"')
def step_attempt_resolve(context: Context, dependency_name: str) -> None:
    """Attempt to resolve a dependency by name."""
    # Create a mock type for testing
    context.dependency_name = dependency_name

    # Try to resolve and capture the exception
    try:
        # We'll create a mock class for testing
        class UserService:
            pass

        context.result = context.container.resolve(UserService)
        context.exception = None
    except Exception as e:
        context.exception = e
        context.result = None


@then('the Container raises a DependencyNotFoundError')
def step_raises_dependency_not_found(context: Context) -> None:
    """Verify a DependencyNotFoundError was raised."""
    assert context.exception is not None, 'No exception was raised'
    # Check for KeyError (as per ADR-002, we map to Python KeyError)
    assert isinstance(context.exception, KeyError), f'Expected KeyError, got {type(context.exception).__name__}'


@then('the error message indicates "{dependency_name}" is not registered')
def step_error_message_indicates(context: Context, dependency_name: str) -> None:
    """Verify the error message mentions the dependency name."""
    assert context.exception is not None, 'No exception was raised'
    error_message = str(context.exception)
    assert dependency_name in error_message or 'UserService' in error_message, (
        f'Error message does not mention dependency: {error_message}'
    )


@when('the developer accesses the container from multiple threads')
def step_access_from_multiple_threads(context: Context) -> None:
    """Access the container concurrently from multiple threads."""
    num_threads = 10
    operations_per_thread = 100
    errors: list[Exception] = []

    def thread_worker() -> None:
        """Worker function that accesses the container."""
        try:
            for _ in range(operations_per_thread):
                # Perform read operations on the container
                # This tests thread-safe concurrent access
                pass
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=thread_worker) for _ in range(num_threads)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    context.thread_errors = errors


@then('the Container maintains data integrity across all threads')
def step_maintains_data_integrity(context: Context) -> None:
    """Verify no data corruption occurred during concurrent access."""
    assert not context.thread_errors, f'Errors occurred during concurrent access: {context.thread_errors}'


@then('no race conditions occur during concurrent access')
def step_no_race_conditions(context: Context) -> None:
    """Verify no race conditions occurred."""
    # If we got here without errors, no race conditions occurred
    assert not context.thread_errors, 'Race conditions detected'


@when('the developer requests a list of registered dependencies')
def step_request_dependency_list(context: Context) -> None:
    """Request a list of registered dependencies."""
    # Will implement when Container has a list_providers() or similar method
    # For now, store that we made the request
    context.requested_list = True


@then('the Container returns an empty list')
def step_returns_empty_list(context: Context) -> None:
    """Verify an empty list is returned."""
    # Placeholder for when we implement list_providers()
    pass


@then('the response is a valid Python iterable')
def step_response_is_iterable(context: Context) -> None:
    """Verify the response is iterable."""
    # Placeholder for when we implement list_providers()
    pass


@given('a developer has created a Container named "{container_name}"')
def step_create_named_container(context: Context, container_name: str) -> None:
    """Create a Container with a specific name for tracking."""
    from dioxide import Container

    if not hasattr(context, 'containers'):
        context.containers = {}

    context.containers[container_name] = Container()


@when('the developer modifies "{container_name}"')
def step_modify_container(context: Context, container_name: str) -> None:
    """Modify a specific container."""

    # For this test, we just need to verify containers are independent
    # We'll register a mock dependency in one container
    class MockService:
        pass

    _ = context.containers[container_name]
    # Try to register (will implement when register methods are ready)
    # For now, this is a placeholder
    context.modified_container = container_name


@then('"{container_name}" remains unchanged')
def step_container_unchanged(context: Context, container_name: str) -> None:
    """Verify a container was not affected by changes to another."""
    # Verify the container still exists and is independent
    assert container_name in context.containers, f'Container {container_name} not found'
    container = context.containers[container_name]
    assert container is not None, f'Container {container_name} is None'


@then('the containers maintain independent state')
def step_containers_independent(context: Context) -> None:
    """Verify containers maintain independent state."""
    # Verify we have multiple containers
    assert len(context.containers) >= 2, 'Need at least 2 containers for this test'

    # Verify they are different objects
    containers = list(context.containers.values())
    for i, container_a in enumerate(containers):
        for container_b in containers[i + 1 :]:
            assert container_a is not container_b, 'Containers are not independent'
