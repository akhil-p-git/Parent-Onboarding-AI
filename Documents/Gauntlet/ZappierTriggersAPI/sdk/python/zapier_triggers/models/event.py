"""Event models for the Triggers SDK."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventStatus(str, Enum):
    """Status of an event in the system."""

    PENDING = "pending"
    """Event is queued for processing."""

    PROCESSING = "processing"
    """Event is currently being processed."""

    DELIVERED = "delivered"
    """Event has been successfully delivered to all subscribers."""

    PARTIALLY_DELIVERED = "partially_delivered"
    """Event was delivered to some but not all subscribers."""

    FAILED = "failed"
    """Event delivery failed for all subscribers."""


class Event(BaseModel):
    """
    Represents an event in the Triggers system.

    Events are the core data unit that flows through the system,
    containing the payload data that subscribers receive.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    """Unique identifier for the event (e.g., 'evt_abc123')."""

    event_type: str
    """Type of the event (e.g., 'user.created', 'order.completed')."""

    source: str
    """Source system that generated the event."""

    data: dict[str, Any]
    """Event payload data."""

    metadata: dict[str, Any] | None = None
    """Optional metadata associated with the event."""

    status: EventStatus
    """Current processing status of the event."""

    idempotency_key: str | None = None
    """Client-provided key for idempotent event creation."""

    created_at: datetime
    """Timestamp when the event was created."""

    updated_at: datetime | None = None
    """Timestamp when the event was last updated."""

    processed_at: datetime | None = None
    """Timestamp when the event finished processing."""

    delivery_attempts: int = 0
    """Number of delivery attempts made."""

    successful_deliveries: int = 0
    """Number of successful deliveries."""

    failed_deliveries: int = 0
    """Number of failed deliveries."""


class CreateEventRequest(BaseModel):
    """Request body for creating a single event."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=1, max_length=256)
    """Type of the event (e.g., 'user.created')."""

    source: str = Field(..., min_length=1, max_length=256)
    """Source system generating the event."""

    data: dict[str, Any] = Field(default_factory=dict)
    """Event payload data."""

    metadata: dict[str, Any] | None = None
    """Optional metadata."""

    idempotency_key: str | None = Field(None, max_length=256)
    """Optional idempotency key for deduplication."""


class BatchEventItem(BaseModel):
    """Single event item in a batch request."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=1, max_length=256)
    """Type of the event."""

    source: str = Field(..., min_length=1, max_length=256)
    """Source system."""

    data: dict[str, Any] = Field(default_factory=dict)
    """Event payload."""

    metadata: dict[str, Any] | None = None
    """Optional metadata."""

    idempotency_key: str | None = None
    """Optional idempotency key."""

    reference_id: str | None = None
    """Client-provided reference ID for tracking in batch results."""


class BatchCreateEventRequest(BaseModel):
    """Request body for creating multiple events in a batch."""

    model_config = ConfigDict(extra="forbid")

    events: list[BatchEventItem] = Field(..., min_length=1, max_length=100)
    """List of events to create (max 100)."""

    fail_fast: bool = False
    """If true, stop processing on first error."""


class BatchEventError(BaseModel):
    """Error details for a failed batch item."""

    code: str
    """Error code."""

    message: str
    """Error message."""


class BatchEventResultItem(BaseModel):
    """Result for a single item in a batch operation."""

    model_config = ConfigDict(extra="ignore")

    index: int
    """Index of the item in the original request."""

    reference_id: str | None = None
    """Client-provided reference ID."""

    success: bool
    """Whether the item was processed successfully."""

    event: Event | None = None
    """The created event (if successful)."""

    error: BatchEventError | None = None
    """Error details (if failed)."""


class BatchEventResult(BaseModel):
    """Result of a batch event creation operation."""

    model_config = ConfigDict(extra="ignore")

    successful: int
    """Number of successfully created events."""

    failed: int
    """Number of failed events."""

    results: list[BatchEventResultItem]
    """Per-item results."""


class ReplayEventRequest(BaseModel):
    """Request body for replaying an event."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = False
    """If true, preview the replay without executing."""

    target_subscription_ids: list[str] | None = None
    """Specific subscriptions to replay to (optional)."""

    payload_override: dict[str, Any] | None = None
    """Override event payload data."""

    metadata_override: dict[str, Any] | None = None
    """Override event metadata."""


class ReplayEventResponse(BaseModel):
    """Response from a replay operation."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    """Whether the replay was successful."""

    event_id: str
    """Original event ID."""

    replay_event_id: str | None = None
    """ID of the new replayed event (if not dry_run)."""

    dry_run: bool
    """Whether this was a dry run."""

    target_subscriptions: list[str]
    """Subscriptions that received/would receive the replay."""

    message: str | None = None
    """Additional message."""
