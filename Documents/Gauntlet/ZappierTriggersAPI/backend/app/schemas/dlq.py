"""
Dead Letter Queue Schemas.

Request and response schemas for DLQ operations.
"""

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema, PaginationMeta


class DLQItemResponse(BaseSchema):
    """Response schema for a DLQ item."""

    dlq_id: str = Field(
        ...,
        description="Unique identifier for this DLQ entry",
        examples=["dlq_evt_01ARZ3NDEK_0"],
    )
    event_id: str = Field(
        ...,
        description="Original event ID",
        examples=["evt_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )
    event_type: str = Field(
        ...,
        description="Event type",
        examples=["user.created"],
    )
    source: str = Field(
        ...,
        description="Event source",
        examples=["billing-service"],
    )
    created_at: datetime | None = Field(
        default=None,
        description="When the event was originally created",
    )
    enqueued_at: datetime | None = Field(
        default=None,
        description="When the event was enqueued",
    )
    dlq_entered_at: datetime | None = Field(
        default=None,
        description="When the event entered the DLQ",
    )
    failure_reason: str | None = Field(
        default=None,
        description="Reason for failure",
    )
    retry_count: int = Field(
        default=0,
        description="Number of retry attempts",
    )


class DLQListResponse(BaseSchema):
    """Response schema for listing DLQ items."""

    data: list[DLQItemResponse] = Field(
        ...,
        description="List of DLQ items",
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Pagination metadata",
    )


class DLQStatsResponse(BaseSchema):
    """Response schema for DLQ statistics."""

    total: int = Field(
        ...,
        description="Total items in DLQ",
    )
    by_event_type: dict[str, int] = Field(
        default_factory=dict,
        description="Count by event type",
    )
    by_source: dict[str, int] = Field(
        default_factory=dict,
        description="Count by source",
    )
    oldest_item: str | None = Field(
        default=None,
        description="Timestamp of oldest item",
    )
    newest_item: str | None = Field(
        default=None,
        description="Timestamp of newest item",
    )


class RetryDLQItemRequest(BaseSchema):
    """Request schema for retrying a DLQ item."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {},
                {"modify_payload": {"retry_reason": "manual retry"}},
            ]
        }
    }

    modify_payload: dict[str, Any] | None = Field(
        default=None,
        description="Optional payload modifications to apply before retry",
    )


class RetryDLQItemResponse(BaseSchema):
    """Response schema for retry operation."""

    success: bool = Field(
        ...,
        description="Whether the retry was successful",
    )
    event_id: str = Field(
        ...,
        description="The event ID that was retried",
    )
    message: str = Field(
        ...,
        description="Result message",
    )
    retry_count: int = Field(
        default=0,
        description="Total retry count after this operation",
    )


class RetryBatchRequest(BaseSchema):
    """Request schema for batch retry operation."""

    event_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of event IDs to retry",
        examples=[["evt_123", "evt_456"]],
    )


class BatchResultItem(BaseSchema):
    """Result for a single item in a batch operation."""

    event_id: str = Field(
        ...,
        description="The event ID",
    )
    success: bool = Field(
        ...,
        description="Whether the operation succeeded",
    )
    error: str | None = Field(
        default=None,
        description="Error message if failed",
    )


class BatchOperationResponse(BaseSchema):
    """Response schema for batch operations."""

    total: int = Field(
        ...,
        description="Total items processed",
    )
    successful: int = Field(
        ...,
        description="Number of successful operations",
    )
    failed: int = Field(
        ...,
        description="Number of failed operations",
    )
    results: list[BatchResultItem] = Field(
        ...,
        description="Individual results",
    )


class DismissDLQItemResponse(BaseSchema):
    """Response schema for dismiss operation."""

    success: bool = Field(
        ...,
        description="Whether the dismiss was successful",
    )
    event_id: str = Field(
        ...,
        description="The event ID that was dismissed",
    )
    message: str = Field(
        ...,
        description="Result message",
    )


class DismissBatchRequest(BaseSchema):
    """Request schema for batch dismiss operation."""

    event_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of event IDs to dismiss",
        examples=[["evt_123", "evt_456"]],
    )


class PurgeDLQResponse(BaseSchema):
    """Response schema for purge operation."""

    success: bool = Field(
        ...,
        description="Whether the purge was successful",
    )
    purged_count: int = Field(
        ...,
        description="Number of items purged",
    )
    message: str = Field(
        ...,
        description="Result message",
    )
