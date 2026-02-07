"""Domain services containing core business logic.

Services are framework-agnostic and depend only on ports (interfaces), not
concrete implementations. This makes them highly testable and portable.
"""

import uuid

from dioxide import Scope, service

from .ports import DatabasePort, EmailPort


@service(scope=Scope.REQUEST)
class RequestContext:
    """Per-request context with a unique request ID.

    Demonstrates REQUEST scope: each HTTP request gets its own instance,
    shared across all injection points within that request. Disposed
    automatically when the request ends.
    """

    def __init__(self) -> None:
        self.request_id = str(uuid.uuid4())


@service
class UserService:
    """Core business logic for user management.

    This service orchestrates database and email operations without knowing
    which concrete adapters are being used. In production it might use
    PostgreSQL and SendGrid, in tests it uses in-memory fakes.
    """

    def __init__(self, db: DatabasePort, email: EmailPort) -> None:
        """Initialize service with port dependencies.

        Args:
            db: Database port for persistence
            email: Email port for notifications
        """
        self.db = db
        self.email = email

    async def register_user(self, name: str, email: str) -> dict:
        """Register a new user and send welcome email.

        This is the core business logic: create user, then notify them.
        The service doesn't know or care which database or email service
        is being used - that's determined by the active profile.

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary

        Example:
            >>> service = container.resolve(UserService)
            >>> user = await service.register_user("Alice", "alice@example.com")
            >>> print(user["name"])
            Alice
        """
        # Business logic: create user first
        user = await self.db.create_user(name, email)

        # Then send welcome email
        await self.email.send_welcome_email(email, name)

        return user

    async def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        return await self.db.get_user(user_id)

    async def list_all_users(self) -> list[dict]:
        """List all registered users.

        Returns:
            List of user dictionaries
        """
        return await self.db.list_users()
