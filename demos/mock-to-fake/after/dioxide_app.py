"""Email service — the dioxide way. Depends on abstraction, not implementation."""

from __future__ import annotations

from typing import Protocol


class EmailPort(Protocol):
    """Port: what the service needs, not how it's done."""

    def send(self, to: str, subject: str, body: str) -> None: ...


class WelcomeService:
    def __init__(self, email: EmailPort) -> None:
        self._email = email

    def welcome_user(self, name: str, address: str) -> None:
        self._email.send(address, "Welcome!", f"Hello {name}, welcome aboard!")
