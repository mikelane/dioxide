"""SendGrid adapter for production email delivery.

This adapter implements EmailPort using the SendGrid API for real email
sending in production environments.
"""

import os

from dioxide import adapter, Profile

from ..domain.ports import EmailPort


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Production email adapter using SendGrid API.

    This adapter sends real emails via SendGrid. In a real application,
    you would use the sendgrid-python library.

    Example configuration via environment variables:
        SENDGRID_API_KEY=SG.xxx...
        SENDGRID_FROM_EMAIL=noreply@example.com
    """

    def __init__(self) -> None:
        """Initialize adapter with SendGrid API key from environment."""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com")

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
            print(f"[SendGridAdapter] Email sent successfully via SendGrid API")
        else:
            print(
                f"[SendGridAdapter] Email NOT sent (SENDGRID_API_KEY not configured)"
            )
