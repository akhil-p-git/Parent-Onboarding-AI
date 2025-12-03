"""
Zapier Triggers SDK Models.

Pydantic models for API request and response data.
"""

from zapier_triggers.models.event import (
    Event,
    EventStatus,
    CreateEventRequest,
    BatchCreateEventRequest,
    BatchEventResult,
    BatchEventResultItem,
)
from zapier_triggers.models.inbox import InboxItem, AcknowledgeResult
from zapier_triggers.models.dlq import DLQItem, DLQStats, RetryResult
from zapier_triggers.models.common import PaginatedResponse, PaginationMeta

__all__ = [
    # Event models
    "Event",
    "EventStatus",
    "CreateEventRequest",
    "BatchCreateEventRequest",
    "BatchEventResult",
    "BatchEventResultItem",
    # Inbox models
    "InboxItem",
    "AcknowledgeResult",
    # DLQ models
    "DLQItem",
    "DLQStats",
    "RetryResult",
    # Common models
    "PaginatedResponse",
    "PaginationMeta",
]
