"""
API Key Model.

Manages API keys for authentication and authorization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import generate_prefixed_id
from app.models.base import Base, TimestampMixin


class ApiKeyEnvironment(str, Enum):
    """API key environment."""

    LIVE = "live"  # Production keys
    TEST = "test"  # Test/sandbox keys


class ApiKeyScope(str, Enum):
    """Available API key scopes/permissions."""

    # Event scopes
    EVENTS_WRITE = "events:write"  # Create events
    EVENTS_READ = "events:read"  # Read events

    # Subscription scopes
    SUBSCRIPTIONS_WRITE = "subscriptions:write"  # Create/update subscriptions
    SUBSCRIPTIONS_READ = "subscriptions:read"  # Read subscriptions
    SUBSCRIPTIONS_DELETE = "subscriptions:delete"  # Delete subscriptions

    # Inbox scopes
    INBOX_READ = "inbox:read"  # Read from inbox (polling)

    # Admin scopes
    ADMIN = "admin"  # Full access


# Default scopes for new API keys
DEFAULT_SCOPES = [
    ApiKeyScope.EVENTS_WRITE,
    ApiKeyScope.EVENTS_READ,
    ApiKeyScope.SUBSCRIPTIONS_READ,
    ApiKeyScope.INBOX_READ,
]


class ApiKey(Base, TimestampMixin):
    """
    API Key model for authentication.

    API keys are:
    - Used for authenticating API requests
    - Stored as hashed values (original key shown only on creation)
    - Scoped to specific permissions
    - Environment-specific (live/test)
    """

    __tablename__ = "api_keys"

    # Primary key with prefix
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: generate_prefixed_id("key"),
    )

    # Key identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name for the key",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of key purpose",
    )

    # Key storage (hashed)
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA-256 hash of the API key",
    )

    # Key prefix for identification (first 8 chars)
    key_prefix: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
        comment="Prefix of the key for identification (e.g., 'sk_live_abc1')",
    )

    # Environment
    environment: Mapped[ApiKeyEnvironment] = mapped_column(
        String(16),
        nullable=False,
        default=ApiKeyEnvironment.TEST,
        index=True,
    )

    # Permissions
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=lambda: [s.value for s in DEFAULT_SCOPES],
        comment="List of permission scopes",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this key was used",
    )
    usage_count: Mapped[int] = mapped_column(
        default=0,
        comment="Total number of API calls made with this key",
    )

    # Rate limiting
    rate_limit: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Custom rate limit (requests per minute), null for default",
    )

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this key expires (null for no expiration)",
    )

    # Extra data
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata (created_by, ip_whitelist, etc.)",
    )

    # Revocation info
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name}, env={self.environment})>"

    @property
    def is_valid(self) -> bool:
        """Check if the API key is currently valid."""
        from app.core.utils import utc_now

        if not self.is_active:
            return False
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at < utc_now():
            return False
        return True

    def has_scope(self, scope: str | ApiKeyScope) -> bool:
        """Check if the key has a specific scope."""
        scope_value = scope.value if isinstance(scope, ApiKeyScope) else scope

        # Admin scope has all permissions
        if ApiKeyScope.ADMIN.value in self.scopes:
            return True

        return scope_value in self.scopes

    def has_any_scope(self, scopes: list[str | ApiKeyScope]) -> bool:
        """Check if the key has any of the specified scopes."""
        return any(self.has_scope(scope) for scope in scopes)

    def has_all_scopes(self, scopes: list[str | ApiKeyScope]) -> bool:
        """Check if the key has all of the specified scopes."""
        return all(self.has_scope(scope) for scope in scopes)
