"""Logging email adapter for development environments.

This adapter implements EmailPort by logging emails instead of sending them,
which is useful for local development where you don't want to send real emails.

Note on constructor injection:
    This adapter does NOT use constructor injection because it doesn't need
    any configuration. Compare to SendGridAdapter which injects ConfigPort
    to get API keys.

    Constructor injection is optional - only use it when your adapter
    actually needs dependencies.
"""

from dioxide import Profile, adapter

from ..domain.ports import EmailPort


@adapter.for_(EmailPort, profile=[Profile.DEVELOPMENT, Profile.CI])
class LoggingEmailAdapter:
    """Development email adapter that logs instead of sending.

    This adapter is useful for local development and CI environments where
    you want to see what emails would be sent without actually sending them.

    Unlike SendGridAdapter, this adapter has no constructor dependencies:
    - No ConfigPort needed (doesn't require API keys or config)
    - Simple, self-contained implementation
    - This is common for development/logging adapters

    Constructor injection is only necessary when an adapter needs external
    configuration or depends on other ports/services.
    """

    def __init__(self) -> None:
        """Initialize logging adapter.

        Note: No dependencies needed! This adapter is self-contained.

        Compare to SendGridAdapter:
            def __init__(self, config: ConfigPort) -> None:
                self.api_key = config.get("SENDGRID_API_KEY")

        The key insight: use constructor injection when you NEED dependencies,
        not because you can.
        """
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
