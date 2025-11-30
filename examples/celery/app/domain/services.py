"""Domain services containing business logic.

Services coordinate between ports and implement the core application logic.
They are framework-agnostic and can be tested in isolation.
"""

from dioxide import service

from .ports import (
    NotificationPort,
    OrderPort,
)


@service
class OrderService:
    """Service for processing orders.

    This service coordinates order processing logic, updating order status
    and sending notifications to users.
    """

    def __init__(self, orders: OrderPort, notifications: NotificationPort) -> None:
        self.orders = orders
        self.notifications = notifications

    def process(self, order_id: str) -> dict:
        """Process an order by updating its status and notifying the user.

        Args:
            order_id: The order to process

        Returns:
            The updated order data
        """
        order = self.orders.get_order(order_id)
        self.orders.update_status(order_id, 'processing')
        self.notifications.send(
            order['user_id'],
            f"Order {order_id} is now being processed",
        )
        return order


@service
class NotificationService:
    """Service for sending notifications.

    Provides a simpler interface for sending common notification types.
    """

    def __init__(self, notifications: NotificationPort) -> None:
        self.notifications = notifications

    def notify_user(self, user_id: str, message: str) -> None:
        """Send a notification to a user.

        Args:
            user_id: The user to notify
            message: The notification message
        """
        self.notifications.send(user_id, message)
