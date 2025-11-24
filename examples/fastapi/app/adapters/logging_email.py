"""Logging email adapter for development environments.

This adapter implements EmailPort by logging emails instead of sending them,
which is useful for local development where you don't want to send real emails.
"""

from dioxide import Profile, adapter

from ..domain.ports import EmailPort


@adapter.for_(EmailPort, profile=[Profile.DEVELOPMENT, Profile.CI])
class LoggingEmailAdapter:
    """Development email adapter that logs instead of sending.

    This adapter is useful for local development and CI environments where
    you want to see what emails would be sent without actually sending them.
    """

    def __init__(self) -> None:
        """Initialize logging adapter."""
        print("[LoggingEmailAdapter] Initialized (emails will be logged, not sent)")

    async def send_welcome_email(self, to: str, name: str) -> None:
        """Log a welcome email instead of sending it.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        print(
            f"\n{'=' * 60}\n"
            f"[LoggingEmailAdapter] EMAIL (NOT SENT)\n"
            f"{'=' * 60}\n"
            f"To: {to}\n"
            f"Subject: Welcome to our platform, {name}!\n"
            f"Body: Hello {name}, welcome aboard!\n"
            f"{'=' * 60}\n"
        )
