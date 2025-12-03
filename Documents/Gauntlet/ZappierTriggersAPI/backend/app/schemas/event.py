"""
Event Schemas.

Request and response schemas for event operations.
"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.event import EventStatus
from app.schemas.base import BaseSchema, PaginationMeta, TimestampMixin


class EventData(BaseSchema):
    """Event payload data schema."""

    model_config = {"extra": "allow"}


class EventMetadata(BaseSchema):
    """Event metadata schema."""

    model_config = {"extra": "allow"}

    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing",
        examples=["corr_abc123"],
    )
    trace_id: str | None = Field(
        default=None,
        description="Distributed trace ID",
        examples=["trace_xyz789"],
    )
    source_ip: str | None = Field(
        default=None,
        description="Source IP address",
        examples=["192.168.1.1"],
    )


class CreateEventRequest(BaseSchema):
    """Request schema for creating a single event."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "user.created",
                    "source": "auth-service",
                    "data": {
                        "user_id": "usr_123456",
                        "email": "user@example.com",
                        "name": "John Doe",
                        "plan": "pro",
                    },
                    "metadata": {
                        "correlation_id": "corr_abc123",
                        "version": "1.0",
                    },
                    "idempotency_key": "idem_unique_key_123",
                },
                {
                    "event_type": "order.completed",
                    "source": "order-service",
                    "data": {
                        "order_id": "ord_789",
                        "total": 99.99,
                        "currency": "USD",
                        "items": [
                            {"sku": "ITEM-001", "quantity": 2},
                        ],
                    },
                },
            ]
        }
    }

    event_type: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event type identifier",
        examples=["user.created", "order.completed", "payment.received"],
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Event source identifier",
        examples=["billing-service", "auth-service", "orders-api"],
    )
    data: dict[str, Any] = Field(
        ...,
        description="Event payload data",
        examples=[{"user_id": "usr_123", "email": "user@example.com"}],
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional event metadata",
        examples=[{"correlation_id": "corr_abc123"}],
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Idempotency key for deduplication",
        examples=["idem_abc123xyz"],
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type format."""
        if not v or not v.strip():
            raise ValueError("event_type cannot be empty")
        # Allow alphanumeric, dots, underscores, hyphens
        import re
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError(
                "event_type must contain only alphanumeric characters, dots, underscores, and hyphens"
            )
        return v.strip()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source format."""
        if not v or not v.strip():
            raise ValueError("source cannot be empty")
        return v.strip()

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate event data."""
        if v is None:
            raise ValueError("data is required")
        # Check for reasonable size (1MB limit)
        import json
        if len(json.dumps(v)) > 1_000_000:
            raise ValueError("data payload exceeds 1MB limit")
        return v


class EventResponse(BaseSchema, TimestampMixin):
    """Response schema for a single event."""

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
    status: EventStatus = Field(
        ...,
        description="Event processing status",
        examples=["pending", "delivered", "failed"],
    )
    idempotency_key: str | None = Field(
        default=None,
        description="Idempotency key if provided",
    )
    processed_at: datetime | None = Field(
        default=None,
        description="When the event was processed",
    )
    delivery_attempts: int = Field(
        default=0,
        description="Number of delivery attempts",
    )
    successful_deliveries: int = Field(
        default=0,
        description="Number of successful deliveries",
    )
    failed_deliveries: int = Field(
        default=0,
        description="Number of failed deliveries",
    )


class EventListResponse(BaseSchema):
    """Response schema for listing events."""

    data: list[EventResponse] = Field(
        ...,
        description="List of events",
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Pagination metadata",
    )


class EventFilterParams(BaseSchema):
    """Query parameters for filtering events."""

    event_type: str | None = Field(
        default=None,
        description="Filter by event type",
        examples=["user.created"],
    )
    source: str | None = Field(
        default=None,
        description="Filter by source",
        examples=["billing-service"],
    )
    status: EventStatus | None = Field(
        default=None,
        description="Filter by status",
        examples=["pending"],
    )
    since: datetime | None = Field(
        default=None,
        description="Filter events created after this time",
    )
    until: datetime | None = Field(
        default=None,
        description="Filter events created before this time",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of events to return",
    )
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor",
    )


class EventStatsResponse(BaseSchema):
    """Response schema for event statistics."""

    total_events: int = Field(
        ...,
        description="Total number of events",
    )
    pending: int = Field(
        ...,
        description="Events pending delivery",
    )
    delivered: int = Field(
        ...,
        description="Successfully delivered events",
    )
    failed: int = Field(
        ...,
        description="Failed events",
    )
    by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Event counts by type",
    )
    by_source: dict[str, int] = Field(
        default_factory=dict,
        description="Event counts by source",
    )


# Replay Schemas


class ReplayEventRequest(BaseSchema):
    """Request schema for replaying an event."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "dry_run": False,
                    "target_subscription_ids": ["sub_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
                },
                {
                    "dry_run": True,
                    "payload_override": {"user_id": "usr_updated"},
                },
            ]
        }
    }

    dry_run: bool = Field(
        default=False,
        description="If true, simulate replay without actually queuing the event",
    )
    target_subscription_ids: list[str] | None = Field(
        default=None,
        description="Optional list of subscription IDs to target. If not provided, all matching subscriptions will receive the replay.",
        examples=[["sub_01ARZ3NDEKTSV4RRFFQ69G5FAV"]],
    )
    payload_override: dict[str, Any] | None = Field(
        default=None,
        description="Optional payload modifications to apply (merged with original)",
        examples=[{"user_id": "usr_modified"}],
    )
    metadata_override: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata modifications to apply (merged with original)",
        examples=[{"replay_reason": "testing"}],
    )


class ReplayEventResponse(BaseSchema):
    """Response schema for event replay operation."""

    success: bool = Field(
        ...,
        description="Whether the replay operation succeeded",
    )
    event_id: str = Field(
        ...,
        description="ID of the original event that was replayed",
    )
    replay_event_id: str | None = Field(
        default=None,
        description="ID of the newly created replay event (null for dry runs)",
    )
    dry_run: bool = Field(
        ...,
        description="Whether this was a dry run",
    )
    target_subscriptions: list[str] = Field(
        default_factory=list,
        description="List of subscription IDs that received/would receive the replay",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable result message",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details about the replay operation",
    )


class ReplayPreviewResponse(BaseSchema):
    """Response schema for replay preview."""

    event_id: str = Field(
        ...,
        description="ID of the event to be replayed",
    )
    original_event: dict[str, Any] = Field(
        ...,
        description="Summary of the original event",
    )
    replay_payload: dict[str, Any] = Field(
        ...,
        description="The payload that would be sent on replay",
    )
    target_subscriptions: list[dict[str, Any]] = Field(
        ...,
        description="Subscriptions that would receive the replay",
    )
    modifications: dict[str, Any] = Field(
        ...,
        description="Applied payload and metadata modifications",
    )
