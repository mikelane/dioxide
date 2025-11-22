"""
Type checking test: Invalid resolve() usage.

This file contains intentionally WRONG code that should FAIL mypy.
It verifies that mypy catches type errors when using Container.resolve().
"""

from dioxide import Container


class UserService:
    def get_user(self, user_id: int) -> str:
        return f'User {user_id}'


def test_invalid_method_call() -> None:
    """mypy should catch calling non-existent methods."""
    container = Container()
    container.register_singleton(UserService, lambda: UserService())

    service = container.resolve(UserService)

    # This should fail mypy - wrong_method doesn't exist
    service.wrong_method()


def test_invalid_attribute_access() -> None:
    """mypy should catch accessing non-existent attributes."""
    container = Container()
    container.register_singleton(UserService, lambda: UserService())

    service = container.resolve(UserService)

    # This should fail mypy - nonexistent_attr doesn't exist
    _ = service.nonexistent_attr


def test_wrong_argument_types() -> None:
    """mypy should catch wrong argument types."""
    container = Container()
    container.register_singleton(UserService, lambda: UserService())

    service = container.resolve(UserService)

    # This should fail mypy - get_user expects int, not str
    service.get_user('not an int')  # type: ignore[arg-type]
