"""
Zapier Triggers Python SDK.

Official Python client for the Zapier Triggers API.

Example usage:
    ```python
    from zapier_triggers import TriggersClient

    async with TriggersClient(api_key="your_api_key") as client:
        # Send an event
        event = await client.events.create(
            event_type="user.created",
            source="my-app",
            data={"user_id": "123", "email": "user@example.com"},
        )
        print(f"Created event: {event.id}")

        # List events
        events = await client.events.list(limit=10)
        for e in events.data:
            print(f"Event: {e.event_type} - {e.status}")
    ```
"""

from zapier_triggers.client import TriggersClient
from zapier_triggers.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TriggersAPIError,
    ValidationError,
)
from zapier_triggers.models import (
    Event,
    EventStatus,
    InboxItem,
    DLQItem,
    PaginatedResponse,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "TriggersClient",
    # Exceptions
    "TriggersAPIError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    # Models
    "Event",
    "EventStatus",
    "InboxItem",
    "DLQItem",
    "PaginatedResponse",
]
