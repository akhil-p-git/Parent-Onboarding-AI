"""Common models used across the SDK."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    model_config = ConfigDict(extra="ignore")

    limit: int
    """Maximum number of items returned."""

    has_more: bool
    """Whether there are more items available."""

    next_cursor: str | None = None
    """Cursor to fetch the next page of results."""

    total: int | None = None
    """Total count of items (if available)."""


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(extra="ignore")

    data: list[T]
    """List of items in this page."""

    pagination: PaginationMeta
    """Pagination metadata."""

    def __iter__(self):
        """Iterate over items in the response."""
        return iter(self.data)

    def __len__(self) -> int:
        """Return the number of items in this page."""
        return len(self.data)


class APIResponse(BaseModel):
    """Base class for API responses."""

    model_config = ConfigDict(extra="ignore")


class HealthStatus(BaseModel):
    """API health status response."""

    model_config = ConfigDict(extra="ignore")

    status: str
    """Overall health status."""

    version: str | None = None
    """API version."""

    components: dict[str, str] | None = None
    """Health status of individual components."""
