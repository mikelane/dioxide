"""Email notification service — tightly coupled to smtplib."""

import smtplib
from email.mime.text import MIMEText


def send_welcome_email(name: str, address: str) -> None:
    """Send a welcome email to a new user."""
    msg = MIMEText(f"Hello {name}, welcome aboard!")
    msg["Subject"] = "Welcome!"
    msg["To"] = address
    msg["From"] = "noreply@example.com"

    with smtplib.SMTP("smtp.example.com", 587) as server:
        server.starttls()
        server.login("noreply@example.com", "secret")
        server.send_message(msg)
