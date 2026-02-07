"""Email notification service — refactored to use HTTP API."""

import urllib.request
import json


def send_welcome_email(name: str, address: str) -> None:
    """Send a welcome email via HTTP API (e.g., SendGrid, Mailgun)."""
    payload = json.dumps({
        "to": address,
        "from": "noreply@example.com",
        "subject": "Welcome!",
        "body": f"Hello {name}, welcome aboard!",
    }).encode()

    req = urllib.request.Request(
        "https://api.emailservice.com/v1/send",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer token"},
    )
    urllib.request.urlopen(req)  # noqa: S310
