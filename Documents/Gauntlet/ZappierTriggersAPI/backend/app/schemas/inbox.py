"""
Inbox Schemas.

Request and response schemas for inbox (polling) operations.
"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class InboxEventItem(BaseSchema):
    """Single event item from inbox."""

    id: str = Field(
        ...,
        description="Unique event identifier",
        examples=["evt_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )
    event_type: str = Field(
        ...,
        description="Event type identifier",
        examples=["user.created"],
    )
    source: str = Field(
        ...,
        description="Event source identifier",
        examples=["billing-service"],
    )
    data: dict[str, Any] = Field(
        ...,
        description="Event payload data",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Event metadata",
    )
    created_at: datetime = Field(
        ...,
        description="When the event was created",
    )
    receipt_handle: str = Field(
        ...,
        description="Handle for acknowledging this event",
        examples=["rcpt_abc123xyz"],
    )
    visibility_timeout: datetime = Field(
        ...,
        description="When the event becomes visible again if not acknowledged",
    )
    delivery_count: int = Field(
        default=1,
        description="Number of times this event has been delivered",
    )


class InboxListRequest(BaseSchema):
    """Request parameters for fetching events from inbox."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of events to fetch",
    )
    visibility_timeout: int = Field(
        default=30,
        ge=1,
        le=43200,  # 12 hours max
        description="Seconds before unacknowledged events become visible again",
    )
    event_types: list[str] | None = Field(
        default=None,
        description="Filter by event types",
        examples=[["user.created", "user.updated"]],
    )
    sources: list[str] | None = Field(
        default=None,
        description="Filter by sources",
        examples=[["billing-service"]],
    )
    wait_time: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Long polling wait time in seconds (0 for immediate return)",
    )


class InboxListResponse(BaseSchema):
    """Response schema for inbox list operation."""

    events: list[InboxEventItem] = Field(
        ...,
        description="List of events from inbox",
    )
    count: int = Field(
        ...,
        description="Number of events returned",
    )
    has_more: bool = Field(
        ...,
        description="Whether more events are available",
    )
    next_poll_at: datetime | None = Field(
        default=None,
        description="Recommended time for next poll (if using rate limiting)",
    )


class AcknowledgeRequest(BaseSchema):
    """Request schema for acknowledging events."""

    receipt_handles: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Receipt handles of events to acknowledge",
        examples=[["rcpt_abc123", "rcpt_def456"]],
    )

    @field_validator("receipt_handles")
    @classmethod
    def validate_receipt_handles(cls, v: list[str]) -> list[str]:
        """Validate receipt handles."""
        if not v:
            raise ValueError("At least one receipt handle is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 receipt handles per request")
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for handle in v:
            if handle not in seen:
                seen.add(handle)
                unique.append(handle)
        return unique


class AcknowledgeResultItem(BaseSchema):
    """Result for a single acknowledgment."""

    receipt_handle: str = Field(
        ...,
        description="Receipt handle that was acknowledged",
    )
    success: bool = Field(
        ...,
        description="Whether the acknowledgment was successful",
    )
    error: str | None = Field(
        default=None,
        description="Error message if acknowledgment failed",
        examples=["Receipt handle expired", "Receipt handle not found"],
    )


class AcknowledgeResponse(BaseSchema):
    """Response schema for acknowledgment operation."""

    total: int = Field(
        ...,
        description="Total receipt handles in request",
    )
    successful: int = Field(
        ...,
        description="Successfully acknowledged",
    )
    failed: int = Field(
        ...,
        description="Failed acknowledgments",
    )
    results: list[AcknowledgeResultItem] = Field(
        ...,
        description="Per-handle results",
    )


class ChangeVisibilityRequest(BaseSchema):
    """Request schema for changing visibility timeout."""

    receipt_handle: str = Field(
        ...,
        description="Receipt handle of the event",
    )
    visibility_timeout: int = Field(
        ...,
        ge=0,
        le=43200,  # 12 hours max
        description="New visibility timeout in seconds (0 to make immediately visible)",
    )


class ChangeVisibilityResponse(BaseSchema):
    """Response schema for visibility change operation."""

    success: bool = Field(
        ...,
        description="Whether the operation was successful",
    )
    new_visibility_timeout: datetime = Field(
        ...,
        description="New visibility timeout timestamp",
    )


class InboxStatsResponse(BaseSchema):
    """Response schema for inbox statistics."""

    visible: int = Field(
        ...,
        description="Number of visible (available) events",
    )
    in_flight: int = Field(
        ...,
        description="Number of events currently being processed",
    )
    delayed: int = Field(
        ...,
        description="Number of delayed events",
    )
    total: int = Field(
        ...,
        description="Total events in inbox",
    )
    oldest_event_at: datetime | None = Field(
        default=None,
        description="Timestamp of oldest event in inbox",
    )
    by_event_type: dict[str, int] = Field(
        default_factory=dict,
        description="Event counts by type",
    )
