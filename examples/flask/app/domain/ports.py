"""Domain ports (interfaces) for the user management system.

Ports define the contracts that adapters must implement. They are pure
protocol definitions with no implementation details or framework dependencies.

Note: Unlike the FastAPI example which uses async methods, Flask uses
synchronous methods since Flask is a synchronous framework.
"""

from typing import Protocol


class DatabasePort(Protocol):
    """Port for database operations.

    Adapters implementing this port might use PostgreSQL, SQLite, or an
    in-memory store for testing.
    """

    def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        ...

    def create_user(self, name: str, email: str) -> dict:
        """Create a new user.

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary with ID
        """
        ...

    def list_users(self) -> list[dict]:
        """List all users.

        Returns:
            List of user dictionaries
        """
        ...


class EmailPort(Protocol):
    """Port for sending emails.

    Adapters implementing this port might use SendGrid, AWS SES, or a fake
    for testing that just records what would have been sent.
    """

    def send_welcome_email(self, to: str, name: str) -> None:
        """Send a welcome email to a new user.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        ...
