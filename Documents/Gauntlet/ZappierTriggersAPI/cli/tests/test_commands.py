"""
Tests for CLI Commands.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from triggers_cli.main import app

runner = CliRunner()


class TestEventsCommands:
    """Tests for events commands."""

    def test_events_send_success(self):
        """Test sending an event."""
        with patch("triggers_cli.commands.events.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.send_event.return_value = {
                "id": "evt_123",
                "event_type": "user.created",
                "source": "test",
                "status": "pending",
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(
                app,
                ["events", "send", "user.created", "test", "-d", '{"user_id": "123"}'],
            )

            assert result.exit_code == 0
            assert "evt_123" in result.stdout

    def test_events_send_invalid_json(self):
        """Test sending event with invalid JSON."""
        result = runner.invoke(
            app,
            ["events", "send", "user.created", "test", "-d", "invalid json"],
        )

        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout

    def test_events_list_success(self):
        """Test listing events."""
        with patch("triggers_cli.commands.events.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.list_events.return_value = {
                "data": [
                    {
                        "id": "evt_1",
                        "event_type": "user.created",
                        "source": "test",
                        "status": "pending",
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                    {
                        "id": "evt_2",
                        "event_type": "order.completed",
                        "source": "orders",
                        "status": "delivered",
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                ],
                "pagination": {"has_more": False},
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["events", "list"])

            assert result.exit_code == 0
            assert "evt_1" in result.stdout
            assert "evt_2" in result.stdout

    def test_events_list_empty(self):
        """Test listing events when empty."""
        with patch("triggers_cli.commands.events.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.list_events.return_value = {
                "data": [],
                "pagination": {"has_more": False},
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["events", "list"])

            assert result.exit_code == 0
            assert "No events found" in result.stdout

    def test_events_get_success(self):
        """Test getting a specific event."""
        with patch("triggers_cli.commands.events.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get_event.return_value = {
                "id": "evt_123",
                "event_type": "user.created",
                "source": "test",
                "status": "pending",
                "data": {"user_id": "123"},
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["events", "get", "evt_123"])

            assert result.exit_code == 0
            assert "evt_123" in result.stdout

    def test_events_replay_dry_run(self):
        """Test replay with dry run."""
        with patch("triggers_cli.commands.events.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.replay_event.return_value = {
                "success": True,
                "event_id": "evt_123",
                "replay_event_id": None,
                "dry_run": True,
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(
                app,
                ["events", "replay", "evt_123", "--dry-run"],
            )

            assert result.exit_code == 0
            assert "Dry run" in result.stdout


class TestInboxCommands:
    """Tests for inbox commands."""

    def test_inbox_list_success(self):
        """Test listing inbox."""
        with patch("triggers_cli.commands.inbox.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.list_inbox.return_value = {
                "data": [
                    {
                        "event_id": "evt_1",
                        "event_type": "user.created",
                        "source": "test",
                        "receipt_handle": "rh_123",
                        "received_at": "2024-01-01T00:00:00Z",
                    },
                ],
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["inbox", "list"])

            assert result.exit_code == 0
            assert "evt_1" in result.stdout

    def test_inbox_ack_success(self):
        """Test acknowledging events."""
        with patch("triggers_cli.commands.inbox.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.acknowledge_events.return_value = {
                "successful": 2,
                "failed": 0,
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["inbox", "ack", "rh_1,rh_2"])

            assert result.exit_code == 0
            assert "Acknowledged 2" in result.stdout


class TestDLQCommands:
    """Tests for DLQ commands."""

    def test_dlq_list_success(self):
        """Test listing DLQ."""
        with patch("triggers_cli.commands.dlq.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.list_dlq.return_value = {
                "data": [
                    {
                        "event_id": "evt_1",
                        "event_type": "user.created",
                        "source": "test",
                        "retry_count": 3,
                        "failure_reason": "Connection timeout",
                    },
                ],
                "pagination": {"total": 1},
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["dlq", "list"])

            assert result.exit_code == 0
            assert "evt_1" in result.stdout

    def test_dlq_retry_success(self):
        """Test retrying a DLQ item."""
        with patch("triggers_cli.commands.dlq.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.retry_dlq_item.return_value = {
                "success": True,
                "event_id": "evt_123",
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["dlq", "retry", "evt_123"])

            assert result.exit_code == 0
            assert "re-queued" in result.stdout


class TestHealthCommand:
    """Tests for health command."""

    def test_health_success(self):
        """Test health check success."""
        with patch("triggers_cli.main.TriggersClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.health_check.return_value = {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "database": "healthy",
                    "redis": "healthy",
                },
            }
            mock_client.return_value = mock_instance

            result = runner.invoke(app, ["health"])

            assert result.exit_code == 0
            assert "healthy" in result.stdout


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self):
        """Test showing configuration."""
        result = runner.invoke(app, ["config", "--show"])

        assert result.exit_code == 0
        assert "API URL" in result.stdout
