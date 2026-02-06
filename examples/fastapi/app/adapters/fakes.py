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
        self._should_fail: bool = False
        self._fail_with: Exception | None = None

    async def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID from in-memory storage."""
        if self._should_fail and self._fail_with:
            raise self._fail_with
        return self.users.get(user_id)

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user in in-memory storage."""
        if self._should_fail and self._fail_with:
            raise self._fail_with
        user_id = str(self._next_id)
        self._next_id += 1

        user = {"id": user_id, "name": name, "email": email}
        self.users[user_id] = user
        return user

    async def list_users(self) -> list[dict]:
        """List all users from in-memory storage."""
        if self._should_fail and self._fail_with:
            raise self._fail_with
        return list(self.users.values())

    def seed(self, *users: dict) -> None:
        """Pre-populate the database with test data.

        This avoids going through the API for test setup, making tests
        faster and more focused on what they're actually testing.

        Automatically advances the ID counter past any seeded IDs to
        prevent collisions when create_user is called afterwards.

        Args:
            *users: User dictionaries, each must have "id", "name", "email"
        """
        for user in users:
            self.users[user["id"]] = user
            try:
                seeded_id = int(user["id"])
                if seeded_id >= self._next_id:
                    self._next_id = seeded_id + 1
            except (ValueError, TypeError):
                pass

    def configure_to_fail(self, error: Exception) -> None:
        """Configure all operations to raise the given error.

        This enables testing how the application handles database failures
        without needing a real database that can actually fail.

        Args:
            error: Exception to raise on next operation
        """
        self._should_fail = True
        self._fail_with = error

    def reset(self) -> None:
        """Reset to default state: clear data and stop failing."""
        self.users.clear()
        self._next_id = 1
        self._should_fail = False
        self._fail_with = None


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
        self._should_fail: bool = False
        self._fail_with: Exception | None = None

    async def send_welcome_email(self, to: str, name: str) -> None:
        """Record a welcome email send.

        Instead of actually sending an email, this records the send
        so tests can verify it happened.
        """
        if self._should_fail and self._fail_with:
            raise self._fail_with
        self.sent_emails.append({"to": to, "name": name, "type": "welcome"})

    def clear(self) -> None:
        """Clear all recorded emails."""
        self.sent_emails.clear()

    def was_welcome_email_sent_to(self, email: str) -> bool:
        """Check if a welcome email was sent to a specific address.

        This is a convenience method for tests -- cleaner than manually
        searching the sent_emails list.
        """
        return any(
            e["to"] == email and e["type"] == "welcome" for e in self.sent_emails
        )

    def configure_to_fail(self, error: Exception) -> None:
        """Configure send operations to raise the given error.

        This enables testing how the application handles email service
        failures without needing a real email service.

        Args:
            error: Exception to raise on next send
        """
        self._should_fail = True
        self._fail_with = error

    def reset(self) -> None:
        """Reset to default state: clear emails and stop failing."""
        self.sent_emails.clear()
        self._should_fail = False
        self._fail_with = None
