"""Initial schema - create events, api_keys, subscriptions, event_deliveries tables.

Revision ID: 001
Revises: None
Create Date: 2024-11-30 00:00:01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### Create api_keys table ###
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("environment", sa.String(length=16), nullable=False),
        sa.Column(
            "scopes",
            postgresql.ARRAY(sa.String(length=64)),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=False, default=0),
        sa.Column("rate_limit", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_environment", "api_keys", ["environment"])
    op.create_index("ix_api_keys_is_active", "api_keys", ["is_active"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # ### Create events table ###
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("api_key_id", sa.String(length=32), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_attempts", sa.Integer(), nullable=False, default=0),
        sa.Column("successful_deliveries", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_deliveries", sa.Integer(), nullable=False, default=0),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_events_api_key_id", "events", ["api_key_id"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_idempotency_key", "events", ["idempotency_key"])
    op.create_index("ix_events_source", "events", ["source"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_type_source", "events", ["event_type", "source"])
    op.create_index("ix_events_status_created", "events", ["status", "created_at"])
    op.create_index(
        "ix_events_created_at_desc",
        "events",
        ["created_at"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_events_data_gin",
        "events",
        ["data"],
        postgresql_using="gin",
        postgresql_ops={"data": "jsonb_path_ops"},
    )

    # ### Create subscriptions table ###
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("signing_secret", sa.String(length=64), nullable=False),
        sa.Column(
            "custom_headers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "event_types",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
        ),
        sa.Column(
            "event_sources",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=True,
        ),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_strategy", sa.String(length=32), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False),
        sa.Column("retry_max_delay_seconds", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("rate_limit", sa.Integer(), nullable=True),
        sa.Column("api_key_id", sa.String(length=32), nullable=True),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, default=0),
        sa.Column("failure_threshold", sa.Integer(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.Column("total_deliveries", sa.Integer(), nullable=False, default=0),
        sa.Column("successful_deliveries", sa.Integer(), nullable=False, default=0),
        sa.Column("failed_deliveries", sa.Integer(), nullable=False, default=0),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_api_key_id", "subscriptions", ["api_key_id"])
    op.create_index("ix_subscriptions_is_healthy", "subscriptions", ["is_healthy"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index(
        "ix_subscriptions_status_healthy",
        "subscriptions",
        ["status", "is_healthy"],
    )
    op.create_index(
        "ix_subscriptions_api_key_status",
        "subscriptions",
        ["api_key_id", "status"],
    )

    # ### Create event_deliveries table ###
    op.create_table(
        "event_deliveries",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("event_id", sa.String(length=32), nullable=False),
        sa.Column("subscription_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "request_headers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column(
            "response_headers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=True),
        sa.Column("signature", sa.String(length=128), nullable=True),
        sa.Column("signature_header", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "attempt_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["subscriptions.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_event_deliveries_event_id", "event_deliveries", ["event_id"])
    op.create_index(
        "ix_event_deliveries_subscription_id",
        "event_deliveries",
        ["subscription_id"],
    )
    op.create_index("ix_event_deliveries_status", "event_deliveries", ["status"])
    op.create_index(
        "ix_event_deliveries_scheduled_at",
        "event_deliveries",
        ["scheduled_at"],
    )
    op.create_index(
        "ix_event_deliveries_next_retry_at",
        "event_deliveries",
        ["next_retry_at"],
    )
    op.create_index(
        "ix_deliveries_status_scheduled",
        "event_deliveries",
        ["status", "scheduled_at"],
    )
    op.create_index(
        "ix_deliveries_event_subscription",
        "event_deliveries",
        ["event_id", "subscription_id"],
    )
    op.create_index(
        "ix_deliveries_retry",
        "event_deliveries",
        ["status", "next_retry_at"],
    )


def downgrade() -> None:
    # ### Drop tables in reverse order ###
    op.drop_table("event_deliveries")
    op.drop_table("subscriptions")
    op.drop_table("events")
    op.drop_table("api_keys")
