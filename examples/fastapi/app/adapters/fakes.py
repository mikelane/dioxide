"""Fake adapters for fast, deterministic testing.

These adapters implement domain ports using simple in-memory data structures.
They are FAKES (real implementations with shortcuts), not MOCKS (behavior
verification objects). This follows dioxide's testing philosophy.

Why fakes instead of mocks?
- Fakes are real implementations, just simpler (in-memory vs database)
- Fakes test actual behavior, not implementation details
- Fakes make tests readable - no mock setup/verification boilerplate
- Fakes are reusable across many tests
- Fakes are fast - no I/O, no network calls
"""

from dioxide import Profile, adapter

from ..domain.ports import DatabasePort, EmailPort


@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabaseAdapter:
    """Fast in-memory fake database for testing.

    This fake uses a simple dictionary to store users. It's fast, deterministic,
    and provides all the same operations as the real database adapter.

    Unlike mocks, this is a REAL implementation - it actually stores and
    retrieves data. The only difference from production is it uses memory
    instead of PostgreSQL.
    """

    def __init__(self) -> None:
        """Initialize with empty user storage."""
        self.users: dict[str, dict] = {}
        self._next_id = 1

    async def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID from in-memory storage.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        return self.users.get(user_id)

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user in in-memory storage.

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary with ID
        """
        user_id = str(self._next_id)
        self._next_id += 1

        user = {"id": user_id, "name": name, "email": email}
        self.users[user_id] = user
        return user

    async def list_users(self) -> list[dict]:
        """List all users from in-memory storage.

        Returns:
            List of user dictionaries
        """
        return list(self.users.values())


@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Fake email adapter that records sends instead of sending.

    This fake doesn't send real emails - it just records what would have been
    sent. Tests can then verify the correct emails were "sent" by checking
    the sent_emails list.

    This is a FAKE, not a MOCK:
    - It has a real implementation (appending to a list)
    - Tests verify state (what's in sent_emails), not calls
    - It's reusable across many tests
    - No mocking framework needed
    """

    def __init__(self) -> None:
        """Initialize with empty sent emails list."""
        self.sent_emails: list[dict[str, str]] = []

    async def send_welcome_email(self, to: str, name: str) -> None:
        """Record a welcome email send.

        Instead of actually sending an email, this records the send
        so tests can verify it happened.

        Args:
            to: Recipient email address
            name: Recipient's name for personalization
        """
        self.sent_emails.append({"to": to, "name": name, "type": "welcome"})

    def clear(self) -> None:
        """Clear all recorded emails.

        Useful in test setup to ensure clean state between tests.
        """
        self.sent_emails.clear()

    def was_welcome_email_sent_to(self, email: str) -> bool:
        """Check if a welcome email was sent to a specific address.

        This is a convenience method for tests. It demonstrates how fakes
        can provide helpful test APIs without needing assertion libraries.

        Args:
            email: Email address to check

        Returns:
            True if welcome email was sent to this address
        """
        return any(
            e["to"] == email and e["type"] == "welcome" for e in self.sent_emails
        )
