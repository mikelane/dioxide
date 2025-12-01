"""Port definitions (interfaces) for the application.

Ports define the contracts that adapters must implement. They allow
the domain logic to remain independent of infrastructure concerns.
"""

from typing import Protocol


class OrderPort(Protocol):
    """Port for order data access."""

    def get_order(self, order_id: str) -> dict:
        """Retrieve an order by ID.

        Args:
            order_id: The unique order identifier

        Returns:
            Order data dictionary with keys: id, user_id, status, items
        """
        ...

    def update_status(self, order_id: str, status: str) -> None:
        """Update the status of an order.

        Args:
            order_id: The unique order identifier
            status: New status (e.g., 'processing', 'shipped', 'delivered')
        """
        ...


class NotificationPort(Protocol):
    """Port for sending notifications to users."""

    def send(self, user_id: str, message: str) -> None:
        """Send a notification to a user.

        Args:
            user_id: The user to notify
            message: The notification message
        """
        ...
