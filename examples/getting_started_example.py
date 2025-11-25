"""
Complete dioxide example: User registration with email notifications.

This is the complete working example from the Getting Started guide.

Run with different profiles to see adapter swapping in action:
- DIOXIDE_PROFILE=production python examples/getting_started_example.py
- DIOXIDE_PROFILE=test python examples/getting_started_example.py
- DIOXIDE_PROFILE=development python examples/getting_started_example.py (default)
"""

import asyncio
import os
from typing import Protocol

from dioxide import Container, Profile, adapter, service


# ============================================================================
# PORTS (Interfaces)
# ============================================================================
class EmailPort(Protocol):
    """Port for email operations."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


# ============================================================================
# ADAPTERS (Implementations)
# ============================================================================
@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Production email via SendGrid."""

    def __init__(self) -> None:
        self.api_key = os.getenv('SENDGRID_API_KEY', 'demo-key')

    async def send(self, to: str, subject: str, body: str) -> None:
        print(f'📧 [SendGrid] Sending email to {to}: {subject}')
        print(f'   API Key: {self.api_key[:10]}...')
        # Real API call would go here
        # await client.post("https://api.sendgrid.com/v3/mail/send", ...)


@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Test email adapter (captures in memory)."""

    def __init__(self) -> None:
        self.sent_emails: list[dict[str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent_emails.append({'to': to, 'subject': subject, 'body': body})
        print(f'✅ [Fake] Email captured: {to}')
        print(f'   Total sent: {len(self.sent_emails)}')


@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    """Development email adapter (prints to console)."""

    async def send(self, to: str, subject: str, body: str) -> None:
        print(f'📧 [Console] Email to: {to}')
        print(f'   Subject: {subject}')
        print(f'   Body: {body[:50]}...')


# ============================================================================
# SERVICES (Business Logic)
# ============================================================================
@service
class UserService:
    """Core business logic for user operations."""

    def __init__(self, email: EmailPort):
        self.email = email

    async def register_user(self, email_addr: str, name: str) -> bool:
        """Register user and send welcome email."""
        print(f'\nRegistering user: {name} ({email_addr})')

        await self.email.send(to=email_addr, subject='Welcome!', body=f'Hello {name}, thanks for signing up!')

        print(f'User {name} registered successfully!\n')
        return True


# ============================================================================
# APPLICATION
# ============================================================================
async def main() -> None:
    """Main application entry point."""
    # Get profile from environment (defaults to development)
    profile_name = os.getenv('DIOXIDE_PROFILE', 'development')

    try:
        profile = getattr(Profile, profile_name.upper())
    except AttributeError:
        print(f"Error: Unknown profile '{profile_name}'")
        print(f'Available profiles: {[p.value for p in Profile]}')
        return

    print('=' * 60)
    print('dioxide Getting Started Example')
    print(f'Profile: {profile.value}')
    print('=' * 60)

    # Create container and scan for components
    container = Container()
    container.scan(profile=profile)

    # Resolve and use service
    user_service = container.resolve(UserService)

    # Register a few users
    await user_service.register_user('alice@example.com', 'Alice')
    await user_service.register_user('bob@example.com', 'Bob')

    # If test profile, show captured emails
    if profile == Profile.TEST:
        fake_email = container.resolve(FakeEmailAdapter)
        print('Captured emails in test:')
        for i, email in enumerate(fake_email.sent_emails, 1):
            print(f'  {i}. {email["to"]}: {email["subject"]}')

    print('=' * 60)
    print('Example complete!')
    print('=' * 60)


if __name__ == '__main__':
    asyncio.run(main())
