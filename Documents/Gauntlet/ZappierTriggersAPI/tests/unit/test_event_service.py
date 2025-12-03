"""
Unit tests for EventService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import Event, EventStatus
from app.schemas import CreateEventRequest
from app.services.event_service import EventService, IdempotencyError


@pytest.mark.unit
class TestEventService:
    """Tests for EventService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create EventService with mock db."""
        return EventService(mock_db)

    @pytest.fixture
    def sample_request(self):
        """Create a sample event request."""
        return CreateEventRequest(
            event_type="user.created",
            source="test-service",
            data={"user_id": "123"},
            metadata={"test": True},
        )

    async def test_create_event_success(self, service, mock_db, sample_request):
        """Test successful event creation."""
        # Act
        event = await service.create_event(sample_request)

        # Assert
        assert event is not None
        assert event.event_type == "user.created"
        assert event.source == "test-service"
        assert event.data == {"user_id": "123"}
        assert event.status == EventStatus.PENDING
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    async def test_create_event_with_idempotency_key(self, service, mock_db, sample_request):
        """Test event creation with idempotency key."""
        # Arrange
        sample_request.idempotency_key = "test-key-123"

        # Mock Redis check (no existing event)
        with patch("app.services.event_service.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis.set.return_value = True
            mock_get_redis.return_value = mock_redis

            # Mock DB check
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            # Act
            event = await service.create_event(sample_request)

            # Assert
            assert event.idempotency_key == "test-key-123"
            mock_redis.set.assert_called_once()

    async def test_create_event_idempotency_conflict(self, service, mock_db, sample_request):
        """Test idempotency key conflict raises error."""
        # Arrange
        sample_request.idempotency_key = "existing-key"

        existing_event = Event(
            id="evt_existing",
            event_type="user.created",
            source="test-service",
            data={},
            status=EventStatus.PENDING,
            idempotency_key="existing-key",
        )

        with patch("app.services.event_service.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = "evt_existing"
            mock_get_redis.return_value = mock_redis

            mock_db.get.return_value = existing_event

            # Act & Assert
            with pytest.raises(IdempotencyError) as exc_info:
                await service.create_event(sample_request)

            assert exc_info.value.existing_event == existing_event

    async def test_create_event_generates_id(self, service, mock_db, sample_request):
        """Test that event ID is generated with correct prefix."""
        # Act
        event = await service.create_event(sample_request)

        # Assert
        assert event.id.startswith("evt_")

    async def test_create_events_batch(self, service, mock_db):
        """Test batch event creation."""
        # Arrange
        requests = [
            CreateEventRequest(
                event_type=f"event.type.{i}",
                source="batch-test",
                data={"index": i},
            )
            for i in range(5)
        ]

        # Act
        result = await service.create_events_batch(requests)

        # Assert
        assert result["successful"] == 5
        assert result["failed"] == 0
        assert len(result["events"]) == 5
        assert mock_db.add.call_count == 5

    async def test_create_events_batch_with_failures(self, service, mock_db):
        """Test batch creation with some failures."""
        # Arrange
        requests = [
            CreateEventRequest(
                event_type="valid.event",
                source="test",
                data={},
            ),
        ]

        # Simulate failure on add
        mock_db.add.side_effect = [Exception("DB Error")]

        # Act
        result = await service.create_events_batch(requests)

        # Assert
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    async def test_get_event_found(self, service, mock_db):
        """Test getting an existing event."""
        # Arrange
        expected_event = Event(
            id="evt_test123",
            event_type="user.created",
            source="test",
            data={},
            status=EventStatus.PENDING,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expected_event
        mock_db.execute.return_value = mock_result

        # Act
        event = await service.get_event("evt_test123")

        # Assert
        assert event == expected_event

    async def test_get_event_not_found(self, service, mock_db):
        """Test getting a non-existent event."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        event = await service.get_event("evt_nonexistent")

        # Assert
        assert event is None

    async def test_list_events_with_filters(self, service, mock_db):
        """Test listing events with filters."""
        # Arrange
        events = [
            Event(id=f"evt_{i}", event_type="user.created", source="test", data={}, status=EventStatus.PENDING)
            for i in range(3)
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = events
        mock_db.execute.return_value = mock_result

        # Act
        result, cursor = await service.list_events(
            event_type="user.created",
            status=EventStatus.PENDING,
            limit=10,
        )

        # Assert
        assert len(result) == 3
        mock_db.execute.assert_called_once()


@pytest.mark.unit
class TestIdempotencyError:
    """Tests for IdempotencyError exception."""

    def test_idempotency_error_creation(self):
        """Test IdempotencyError can be created with existing event."""
        existing = Event(
            id="evt_123",
            event_type="test",
            source="test",
            data={},
            status=EventStatus.PENDING,
        )

        error = IdempotencyError("Duplicate", existing_event=existing)

        assert str(error) == "Duplicate"
        assert error.existing_event == existing

    def test_idempotency_error_without_event(self):
        """Test IdempotencyError without existing event."""
        error = IdempotencyError("Duplicate key")

        assert str(error) == "Duplicate key"
        assert error.existing_event is None
