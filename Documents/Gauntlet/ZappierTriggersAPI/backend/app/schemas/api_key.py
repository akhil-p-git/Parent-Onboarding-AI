"""
API Key Schemas.

Request and response schemas for API key management.
"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.api_key import ApiKeyEnvironment, ApiKeyScope
from app.schemas.base import BaseSchema, PaginationMeta, TimestampMixin


class CreateApiKeyRequest(BaseSchema):
    """Request schema for creating an API key."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for the key",
        examples=["Production API Key"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional description",
    )
    environment: ApiKeyEnvironment = Field(
        default=ApiKeyEnvironment.TEST,
        description="Environment: 'live' or 'test'",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="Permission scopes (default: standard scopes)",
        examples=[["events:write", "events:read", "subscriptions:read"]],
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiration datetime",
    )
    rate_limit: int | None = Field(
        default=None,
        ge=1,
        le=100000,
        description="Custom rate limit (requests per minute)",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
    )

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: list[str] | None) -> list[str] | None:
        """Validate scopes are valid."""
        if v is None:
            return v

        valid_scopes = {s.value for s in ApiKeyScope}
        invalid = set(v) - valid_scopes
        if invalid:
            raise ValueError(f"Invalid scopes: {', '.join(invalid)}")

        return v


class UpdateApiKeyRequest(BaseSchema):
    """Request schema for updating an API key."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New name",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="New description",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="New scopes",
    )
    is_active: bool | None = Field(
        default=None,
        description="Active status",
    )
    rate_limit: int | None = Field(
        default=None,
        ge=1,
        le=100000,
        description="New rate limit",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="New metadata",
    )


class ApiKeyResponse(BaseSchema, TimestampMixin):
    """Response schema for an API key."""

    id: str = Field(
        ...,
        description="Unique API key identifier",
        examples=["key_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )
    name: str = Field(
        ...,
        description="API key name",
    )
    description: str | None = Field(
        default=None,
        description="API key description",
    )
    key_prefix: str = Field(
        ...,
        description="Key prefix for identification",
        examples=["sk_live_abc1"],
    )
    environment: ApiKeyEnvironment = Field(
        ...,
        description="Environment",
    )
    scopes: list[str] = Field(
        ...,
        description="Permission scopes",
    )
    is_active: bool = Field(
        ...,
        description="Whether the key is active",
    )
    last_used_at: datetime | None = Field(
        default=None,
        description="Last time the key was used",
    )
    usage_count: int = Field(
        default=0,
        description="Total API calls made with this key",
    )
    rate_limit: int | None = Field(
        default=None,
        description="Custom rate limit",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Expiration datetime",
    )
    revoked_at: datetime | None = Field(
        default=None,
        description="When the key was revoked",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
    )


class ApiKeyWithSecretResponse(ApiKeyResponse):
    """API key response including the raw key (only on creation)."""

    key: str = Field(
        ...,
        description="The raw API key (only shown once on creation)",
        examples=["sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"],
    )


class ApiKeyListResponse(BaseSchema):
    """Response schema for listing API keys."""

    data: list[ApiKeyResponse] = Field(
        ...,
        description="List of API keys",
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Pagination metadata",
    )


class RevokeApiKeyRequest(BaseSchema):
    """Request schema for revoking an API key."""

    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Reason for revocation",
        examples=["Key compromised"],
    )


class RevokeApiKeyResponse(BaseSchema):
    """Response schema for API key revocation."""

    id: str = Field(
        ...,
        description="API key ID",
    )
    revoked_at: datetime = Field(
        ...,
        description="When the key was revoked",
    )
    reason: str | None = Field(
        default=None,
        description="Revocation reason",
    )


class ApiKeyUsageStats(BaseSchema):
    """API key usage statistics."""

    key_id: str = Field(
        ...,
        description="API key ID",
    )
    period_start: datetime = Field(
        ...,
        description="Statistics period start",
    )
    period_end: datetime = Field(
        ...,
        description="Statistics period end",
    )
    total_requests: int = Field(
        ...,
        description="Total requests in period",
    )
    successful_requests: int = Field(
        ...,
        description="Successful requests",
    )
    failed_requests: int = Field(
        ...,
        description="Failed requests",
    )
    rate_limited_requests: int = Field(
        ...,
        description="Rate limited requests",
    )
    by_endpoint: dict[str, int] = Field(
        default_factory=dict,
        description="Requests by endpoint",
    )


class AvailableScopesResponse(BaseSchema):
    """Response schema for listing available scopes."""

    scopes: list["ScopeInfo"] = Field(
        ...,
        description="List of available scopes",
    )


class ScopeInfo(BaseSchema):
    """Information about a permission scope."""

    name: str = Field(
        ...,
        description="Scope identifier",
        examples=["events:write"],
    )
    description: str = Field(
        ...,
        description="Scope description",
        examples=["Create and send events"],
    )
    category: str = Field(
        ...,
        description="Scope category",
        examples=["events", "subscriptions", "admin"],
    )
