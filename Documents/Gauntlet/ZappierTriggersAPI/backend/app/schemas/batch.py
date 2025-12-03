"""
Batch Event Schemas.

Request and response schemas for batch event operations.
"""

from typing import Any

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema
from app.schemas.event import CreateEventRequest, EventResponse


class BatchEventItem(BaseSchema):
    """Single event item in a batch request."""

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event type identifier",
        examples=["user.created"],
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event source identifier",
        examples=["billing-service"],
    )
    data: dict[str, Any] = Field(
        ...,
        description="Event payload data",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional event metadata",
    )
    idempotency_key: str | None = Field(
        default=None,
        max_length=255,
        description="Idempotency key for deduplication",
    )
    reference_id: str | None = Field(
        default=None,
        max_length=255,
        description="Client-provided reference ID for tracking in response",
        examples=["my-event-1"],
    )


class BatchCreateEventRequest(BaseSchema):
    """Request schema for creating multiple events in a batch."""

    events: list[BatchEventItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of events to create (max 100)",
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop processing on first error",
    )

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[BatchEventItem]) -> list[BatchEventItem]:
        """Validate batch events."""
        if not v:
            raise ValueError("At least one event is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 events per batch")

        # Check for duplicate reference IDs
        ref_ids = [e.reference_id for e in v if e.reference_id]
        if len(ref_ids) != len(set(ref_ids)):
            raise ValueError("Duplicate reference_id values in batch")

        return v

    @model_validator(mode="after")
    def validate_total_size(self) -> "BatchCreateEventRequest":
        """Validate total batch size."""
        import json

        total_size = sum(
            len(json.dumps(e.data)) for e in self.events
        )
        # 10MB total batch limit
        if total_size > 10_000_000:
            raise ValueError("Total batch payload exceeds 10MB limit")
        return self


class BatchEventError(BaseSchema):
    """Error details for a failed batch event."""

    code: str = Field(
        ...,
        description="Error code",
        examples=["validation_error", "duplicate_idempotency_key", "payload_too_large"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["The event_type field is required"],
    )
    field: str | None = Field(
        default=None,
        description="Field that caused the error",
        examples=["event_type"],
    )


class BatchEventResultItem(BaseSchema):
    """Result for a single event in a batch response."""

    index: int = Field(
        ...,
        description="Index in the original request array",
        examples=[0],
    )
    reference_id: str | None = Field(
        default=None,
        description="Client-provided reference ID if provided",
        examples=["my-event-1"],
    )
    success: bool = Field(
        ...,
        description="Whether this event was created successfully",
    )
    event: EventResponse | None = Field(
        default=None,
        description="Created event (if successful)",
    )
    error: BatchEventError | None = Field(
        default=None,
        description="Error details (if failed)",
    )


class BatchCreateEventResponse(BaseSchema):
    """Response schema for batch event creation."""

    total: int = Field(
        ...,
        description="Total number of events in the request",
        examples=[10],
    )
    successful: int = Field(
        ...,
        description="Number of successfully created events",
        examples=[9],
    )
    failed: int = Field(
        ...,
        description="Number of failed events",
        examples=[1],
    )
    results: list[BatchEventResultItem] = Field(
        ...,
        description="Per-event results",
    )

    @property
    def all_successful(self) -> bool:
        """Check if all events were created successfully."""
        return self.failed == 0

    @property
    def partial_success(self) -> bool:
        """Check if some events failed."""
        return self.successful > 0 and self.failed > 0


class BatchEventSummary(BaseSchema):
    """Summary of batch operation for quick status check."""

    batch_id: str = Field(
        ...,
        description="Unique batch operation ID",
        examples=["batch_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )
    status: str = Field(
        ...,
        description="Batch status: 'complete', 'partial', 'failed'",
        examples=["complete"],
    )
    total: int = Field(
        ...,
        description="Total events in batch",
    )
    successful: int = Field(
        ...,
        description="Successfully processed events",
    )
    failed: int = Field(
        ...,
        description="Failed events",
    )
    event_ids: list[str] = Field(
        default_factory=list,
        description="IDs of successfully created events",
    )
