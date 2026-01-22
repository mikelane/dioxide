"""Kafka adapter for production event publishing.

In a real application, this would use aiokafka or confluent-kafka.
This example simulates the behavior for demonstration purposes.
"""

from typing import Any

from dioxide import Profile, adapter

from ..domain.ports import EventPublisherPort


@adapter.for_(EventPublisherPort, profile=Profile.PRODUCTION)
class KafkaEventPublisher:
    """Production event publisher using Kafka.

    In a real implementation, this would:
    - Use aiokafka for async Kafka operations
    - Handle serialization (JSON, Avro, Protobuf)
    - Have proper error handling and retries
    - Support different topics for different event types
    """

    def __init__(self) -> None:
        """Initialize simulated Kafka connection."""
        print("  [Kafka] Event publisher initialized")

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to Kafka.

        Args:
            event_type: Type of event (used as topic name)
            payload: Event data
        """
        print(f"  [Kafka] Published {event_type} event: {payload}")
