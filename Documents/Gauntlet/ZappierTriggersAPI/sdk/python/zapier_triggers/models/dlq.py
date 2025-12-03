"""Dead Letter Queue (DLQ) models for the Triggers SDK."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DLQItem(BaseModel):
    """
    Represents an item in the Dead Letter Queue.

    Items end up in the DLQ when they fail delivery
    after exhausting all retry attempts.
    """

    model_config = ConfigDict(extra="ignore")

    event_id: str
    """ID of the failed event."""

    event_type: str
    """Type of the event."""

    source: str
    """Source that generated the event."""

    data: dict[str, Any]
    """Event payload data."""

    metadata: dict[str, Any] | None = None
    """Event metadata."""

    subscription_id: str | None = None
    """Subscription that failed to receive this event."""

    failure_reason: str | None = None
    """Human-readable description of why delivery failed."""

    error_code: str | None = None
    """Machine-readable error code."""

    retry_count: int
    """Number of delivery attempts made."""

    first_failed_at: datetime | None = None
    """When the first delivery failure occurred."""

    last_failed_at: datetime | None = None
    """When the most recent delivery failure occurred."""

    created_at: datetime
    """When this item was added to the DLQ."""


class DLQStats(BaseModel):
    """Statistics for the Dead Letter Queue."""

    model_config = ConfigDict(extra="ignore")

    total_items: int
    """Total number of items in the DLQ."""

    by_event_type: dict[str, int] | None = None
    """Count of items grouped by event type."""

    by_error_code: dict[str, int] | None = None
    """Count of items grouped by error code."""

    oldest_item_age_seconds: int | None = None
    """Age of the oldest item in seconds."""


class RetryRequest(BaseModel):
    """Request body for retrying a DLQ item."""

    model_config = ConfigDict(extra="forbid")

    modify_payload: dict[str, Any] | None = None
    """Optional payload modifications before retry."""


class RetryResult(BaseModel):
    """Result of a retry operation."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    """Whether the item was successfully re-queued."""

    event_id: str
    """ID of the retried event."""

    message: str | None = None
    """Additional message."""


class BatchRetryRequest(BaseModel):
    """Request body for batch retry operation."""

    model_config = ConfigDict(extra="forbid")

    event_ids: list[str]
    """List of event IDs to retry."""


class BatchRetryResult(BaseModel):
    """Result of a batch retry operation."""

    model_config = ConfigDict(extra="ignore")

    successful: int
    """Number of successfully re-queued items."""

    failed: int
    """Number of failed retries."""

    results: list[RetryResult]
    """Per-item results."""


class DismissResult(BaseModel):
    """Result of dismissing a DLQ item."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    """Whether the item was successfully dismissed."""

    event_id: str
    """ID of the dismissed event."""

    message: str | None = None
    """Additional message."""
