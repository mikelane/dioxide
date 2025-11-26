"""SendGrid adapter for production email delivery.

This adapter demonstrates CONSTRUCTOR DEPENDENCY INJECTION - it depends on
ConfigPort to get its API key and sender email address.

Constructor injection makes adapters:
    - Testable: Tests can inject fake config
    - Explicit: Dependencies are visible in the signature
    - Consistent: All config comes through ConfigPort
"""

from dioxide import Profile, adapter

from ..domain.ports import ConfigPort, EmailPort


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Production email adapter using SendGrid API.

    This adapter demonstrates constructor dependency injection:

        def __init__(self, config: ConfigPort) -> None:
            self.api_key = config.get("SENDGRID_API_KEY")
            self.from_email = config.get("SENDGRID_FROM_EMAIL")

    When dioxide resolves this adapter:
    1. Sees __init__ needs ConfigPort
    2. Looks up ConfigPort in the container
    3. For PRODUCTION profile, finds EnvConfigAdapter
    4. Creates EnvConfigAdapter, passes to __init__
    5. SendGridAdapter gets config from environment variables

    This is the "Config Adapter Pattern" - a common way to make adapters
    configurable without hardcoding environment variable names.
    """

    def __init__(self, config: ConfigPort) -> None:
        """Initialize adapter with injected configuration.

        Args:
            config: Configuration port - automatically injected by dioxide!

        Note: dioxide automatically injects ConfigPort because:
        1. The parameter has a type hint (ConfigPort)
        2. ConfigPort is registered in the container (via @adapter.for_())
        3. The container is scanned with a profile that has a ConfigPort adapter
        """
        # Get config from injected ConfigPort (NOT os.environ directly!)
        self.api_key = config.get("SENDGRID_API_KEY")
        self.from_email = config.get("SENDGRID_FROM_EMAIL", "noreply@example.com")

        if not self.api_key:
            print(
                "[SendGridAdapter] WARNING: SENDGRID_API_KEY not set. "
                "Emails will not be sent."
            )

    async def send_welcome_email(self, to: str, name: str) -> None:
        """Send a welcome email via SendGrid.

        In production, this would use sendgrid-python:

            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=self.from_email,
                to_emails=to,
                subject=f"Welcome to our platform, {name}!",
                html_content=f"<p>Hello {name}, welcome aboard!</p>"
            )

            sg = SendGridAPIClient(self.api_key)
            response = await sg.send(message)

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        # Mock implementation - replace with real SendGrid API call
        print(
            f"[SendGridAdapter] Sending welcome email\n"
            f"  From: {self.from_email}\n"
            f"  To: {to}\n"
            f"  Subject: Welcome to our platform, {name}!\n"
            f"  Body: Hello {name}, welcome aboard!"
        )

        if self.api_key:
            print("[SendGridAdapter] Email sent successfully via SendGrid API")
        else:
            print("[SendGridAdapter] Email NOT sent (SENDGRID_API_KEY not configured)")
