"""Domain services containing core business logic.

Services are framework-agnostic and depend only on ports (interfaces), not
concrete implementations. This makes them highly testable and portable.
"""

from dioxide import service

from .ports import (
    DatabasePort,
    EmailPort,
)


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

    def register_user(self, name: str, email: str) -> dict:
        """Register a new user and send welcome email.

        This is the core business logic: create user, then notify them.
        The service doesn't know or care which database or email service
        is being used - that's determined by the active profile.

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary
        """
        user = self.db.create_user(name, email)
        self.email.send_welcome_email(email, name)
        return user

    def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        return self.db.get_user(user_id)

    def list_all_users(self) -> list[dict]:
        """List all registered users.

        Returns:
            List of user dictionaries
        """
        return self.db.list_users()
