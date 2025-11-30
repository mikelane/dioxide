"""Logging email adapter for development.

This adapter logs emails to the console instead of sending them. Useful for
local development where you want to see what emails would be sent without
actually sending them.
"""

from dioxide import (
    Profile,
    adapter,
)

from ..domain.ports import EmailPort


@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class LoggingEmailAdapter:
    """Email adapter that logs to console instead of sending.

    Perfect for local development - you can see what emails would be sent
    without setting up email infrastructure.
    """

    def send_welcome_email(self, to: str, name: str) -> None:
        """Log a welcome email to console.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        print(f"\n{'=' * 60}")
        print("WELCOME EMAIL (not actually sent)")
        print(f"{'=' * 60}")
        print(f"To: {to}")
        print(f"Subject: Welcome to our platform, {name}!")
        print(f"{'=' * 60}")
        print(f"Hello {name},")
        print()
        print("Thank you for joining our platform!")
        print("We're excited to have you on board.")
        print()
        print("Best regards,")
        print("The Team")
        print(f"{'=' * 60}\n")


@adapter.for_(EmailPort, profile=Profile.CI)
class CIEmailAdapter:
    """Silent email adapter for CI environments.

    In CI, we don't want any output from email sends. This adapter
    silently accepts emails without logging or sending.
    """

    def send_welcome_email(self, to: str, name: str) -> None:
        """Accept email silently (for CI environments).

        Args:
            to: Recipient email address (ignored)
            name: Recipient's name (ignored)
        """
        pass  # Silent in CI
