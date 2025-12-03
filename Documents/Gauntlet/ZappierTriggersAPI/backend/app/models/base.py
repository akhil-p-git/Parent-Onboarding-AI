"""
Base Model and Common Mixins.

Provides base class for all SQLAlchemy models with common fields and utilities.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.utils import generate_ulid


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Use JSONB for JSON columns in PostgreSQL
    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ULIDMixin:
    """
    Mixin that provides ULID-based primary key.

    ULIDs are time-ordered, sortable, and URL-safe.
    Format: 01ARZ3NDEKTSV4RRFFQ69G5FAV (26 characters)
    """

    id: Mapped[str] = mapped_column(
        String(26),
        primary_key=True,
        default=generate_ulid,
    )


class PrefixedIDMixin:
    """
    Mixin for models that need prefixed IDs.

    Override `id_prefix` in subclass to set the prefix.
    Example: evt_01ARZ3NDEKTSV4RRFFQ69G5FAV
    """

    id_prefix: str = ""

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    @classmethod
    def generate_id(cls) -> str:
        """Generate a prefixed ID."""
        return f"{cls.id_prefix}_{generate_ulid()}" if cls.id_prefix else generate_ulid()
