"""Inbox models for the Triggers SDK."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InboxItem(BaseModel):
    """
    Represents an item in a subscription's inbox.

    Inbox items are events that have been delivered to a subscription
    and are waiting to be acknowledged.
    """

    model_config = ConfigDict(extra="ignore")

    event_id: str
    """ID of the event."""

    event_type: str
    """Type of the event."""

    source: str
    """Source that generated the event."""

    data: dict[str, Any]
    """Event payload data."""

    metadata: dict[str, Any] | None = None
    """Event metadata."""

    receipt_handle: str
    """
    Handle used to acknowledge this item.

    This handle is unique to this delivery and must be used
    when calling inbox.acknowledge().
    """

    subscription_id: str | None = None
    """ID of the subscription this was delivered to."""

    received_at: datetime
    """When this item was received in the inbox."""

    expires_at: datetime | None = None
    """When this item will expire if not acknowledged."""

    delivery_attempt: int = 1
    """Which delivery attempt this represents."""


class AcknowledgeRequest(BaseModel):
    """Request body for acknowledging inbox items."""

    model_config = ConfigDict(extra="forbid")

    receipt_handles: list[str]
    """List of receipt handles to acknowledge."""


class AcknowledgeResult(BaseModel):
    """Result of an acknowledge operation."""

    model_config = ConfigDict(extra="ignore")

    successful: int
    """Number of successfully acknowledged items."""

    failed: int
    """Number of failed acknowledgments."""

    errors: list[dict[str, Any]] | None = None
    """Details of any failures."""


class InboxStats(BaseModel):
    """Statistics for a subscription's inbox."""

    model_config = ConfigDict(extra="ignore")

    subscription_id: str
    """Subscription ID."""

    pending_count: int
    """Number of items waiting to be processed."""

    oldest_item_age_seconds: int | None = None
    """Age of the oldest unacknowledged item in seconds."""

    processing_rate: float | None = None
    """Events processed per second (if available)."""
