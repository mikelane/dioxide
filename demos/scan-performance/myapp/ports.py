"""Ports (interfaces) for the demo application."""

from typing import Protocol


class EmailPort(Protocol):
    def send(self, to: str, body: str) -> None: ...


class PaymentPort(Protocol):
    def charge(self, amount: float) -> str: ...


class AnalyticsPort(Protocol):
    def track(self, event: str) -> None: ...
