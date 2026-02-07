"""Fake-based tests — coupled to the PORT, not the implementation."""

from dioxide_app import EmailPort, WelcomeService


class FakeEmail:
    """A simple in-memory fake that records what was sent."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


def test_sends_welcome_email():
    fake = FakeEmail()
    svc = WelcomeService(fake)

    svc.welcome_user("Alice", "alice@example.com")

    assert len(fake.sent) == 1
    assert fake.sent[0]["to"] == "alice@example.com"
    assert "Alice" in fake.sent[0]["body"]
