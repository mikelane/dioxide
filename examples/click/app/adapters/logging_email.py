"""Logging email adapter for development.

This adapter logs emails to the console instead of sending them, which is
useful for development when you want to see what emails would be sent.
"""

from dioxide import (
    Profile,
    adapter,
)

from ..domain.ports import (
    DatabasePort,
    EmailPort,
)


@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class LoggingEmailAdapter:
    """Email adapter that logs to console for development.

    This adapter is useful during development to see what emails would
    be sent without actually sending them.
    """

    def send_welcome_email(self, to: str, name: str) -> None:
        """Log a welcome email to console.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        print(f"\n{'=' * 50}")
        print("EMAIL WOULD BE SENT:")
        print(f"  To: {to}")
        print(f"  Subject: Welcome, {name}!")
        print(f"  Body: Hello {name}, welcome to our platform!")
        print(f"{'=' * 50}\n")


@adapter.for_(DatabasePort, profile=Profile.DEVELOPMENT)
class DevelopmentDatabaseAdapter:
    """In-memory database for development.

    Same as the test fake, but registered for development profile.
    """

    def __init__(self) -> None:
        """Initialize with empty user storage."""
        self.users: dict[str, dict] = {}
        self._next_id = 1

    def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID from in-memory storage."""
        return self.users.get(user_id)

    def create_user(self, name: str, email: str) -> dict:
        """Create a new user in in-memory storage."""
        user_id = str(self._next_id)
        self._next_id += 1

        user = {"id": user_id, "name": name, "email": email}
        self.users[user_id] = user
        return user

    def list_users(self) -> list[dict]:
        """List all users from in-memory storage."""
        return list(self.users.values())
