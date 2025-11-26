"""Domain ports (interfaces) for the user management system.

Ports define the contracts that adapters must implement. They are pure
protocol definitions with no implementation details or framework dependencies.
"""

from typing import Protocol


class ConfigPort(Protocol):
    """Port for application configuration.

    This port demonstrates constructor dependency injection - adapters for
    DatabasePort and EmailPort can depend on ConfigPort to get their settings.

    Using a port for configuration (instead of reading os.environ directly)
    allows:
    - Different config sources per profile (env vars, files, in-memory)
    - Easy testing with controllable configuration
    - Centralized configuration management
    """

    def get(self, key: str, default: str = "") -> str:
        """Get a configuration value.

        Args:
            key: Configuration key (e.g., "DATABASE_URL", "SENDGRID_API_KEY")
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        ...


class DatabasePort(Protocol):
    """Port for database operations.

    Adapters implementing this port might use PostgreSQL, MongoDB, or an
    in-memory store for testing.
    """

    async def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        ...

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user.

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary with ID
        """
        ...

    async def list_users(self) -> list[dict]:
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

    async def send_welcome_email(self, to: str, name: str) -> None:
        """Send a welcome email to a new user.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        ...
