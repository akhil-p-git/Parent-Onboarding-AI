"""
Base Schemas and Common Utilities.

Provides base classes and common patterns for all Pydantic schemas.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Type variable for generic responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,  # Allow population by field name or alias
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_assignment=True,  # Validate on assignment
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(
        ...,
        description="When the resource was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        ...,
        description="When the resource was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of items to return",
    )
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor from previous response",
        examples=["eyJpZCI6IjAxQVJaM05ERUtUU1Y0UlJGRlE2OUc1RkFWIn0="],
    )


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    data: list[T] = Field(
        ...,
        description="List of items",
    )
    pagination: "PaginationMeta" = Field(
        ...,
        description="Pagination metadata",
    )


class PaginationMeta(BaseSchema):
    """Pagination metadata for list responses."""

    total: int | None = Field(
        default=None,
        description="Total number of items (may be null for performance)",
        examples=[150],
    )
    limit: int = Field(
        ...,
        description="Number of items requested",
        examples=[100],
    )
    has_more: bool = Field(
        ...,
        description="Whether more items are available",
        examples=[True],
    )
    next_cursor: str | None = Field(
        default=None,
        description="Cursor to fetch next page",
        examples=["eyJpZCI6IjAxQVJaM05ERUtUU1Y0UlJGRlE2OUc1RkFWIn0="],
    )


class SuccessResponse(BaseSchema):
    """Generic success response."""

    success: bool = Field(
        default=True,
        description="Whether the operation was successful",
    )
    message: str | None = Field(
        default=None,
        description="Optional success message",
    )


class MetadataField(BaseSchema):
    """Schema for metadata fields."""

    model_config = ConfigDict(extra="allow")

    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing",
        examples=["req_abc123"],
    )
    trace_id: str | None = Field(
        default=None,
        description="Distributed trace ID",
        examples=["trace_xyz789"],
    )


def create_example_datetime() -> str:
    """Create example datetime string for documentation."""
    return "2024-01-15T10:30:00Z"
