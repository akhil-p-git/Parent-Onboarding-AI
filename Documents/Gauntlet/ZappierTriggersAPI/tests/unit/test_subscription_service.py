"""
Unit tests for SubscriptionService.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import Subscription, SubscriptionStatus
from app.schemas import CreateSubscriptionRequest, UpdateSubscriptionRequest, WebhookConfig
from app.services.subscription_service import SubscriptionService


@pytest.mark.unit
class TestSubscriptionService:
    """Tests for SubscriptionService."""

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
        """Create SubscriptionService with mock db."""
        return SubscriptionService(mock_db)

    @pytest.fixture
    def sample_create_request(self):
        """Create a sample subscription request."""
        return CreateSubscriptionRequest(
            name="Test Subscription",
            target_url="https://webhook.example.com/events",
            webhook_config=WebhookConfig(
                timeout_seconds=30,
                retry_strategy="exponential",
                max_retries=5,
            ),
        )

    async def test_create_subscription_success(self, service, mock_db, sample_create_request):
        """Test successful subscription creation."""
        # Act
        subscription = await service.create_subscription(sample_create_request)

        # Assert
        assert subscription is not None
        assert subscription.name == "Test Subscription"
        assert subscription.target_url == "https://webhook.example.com/events"
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.signing_secret is not None
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    async def test_create_subscription_generates_id(self, service, mock_db, sample_create_request):
        """Test that subscription ID is generated with correct prefix."""
        # Act
        subscription = await service.create_subscription(sample_create_request)

        # Assert
        assert subscription.id.startswith("sub_")

    async def test_create_subscription_generates_signing_secret(self, service, mock_db, sample_create_request):
        """Test that signing secret is generated."""
        # Act
        subscription = await service.create_subscription(sample_create_request)

        # Assert
        assert subscription.signing_secret is not None
        assert len(subscription.signing_secret) > 20  # Should be a long secret

    async def test_create_subscription_with_api_key(self, service, mock_db, sample_create_request):
        """Test subscription creation with API key association."""
        # Act
        subscription = await service.create_subscription(
            sample_create_request,
            api_key_id="key_test123",
        )

        # Assert
        assert subscription.api_key_id == "key_test123"

    async def test_get_subscription_found(self, service, mock_db):
        """Test getting an existing subscription."""
        # Arrange
        expected = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expected
        mock_db.execute.return_value = mock_result

        # Act
        subscription = await service.get_subscription("sub_test123")

        # Assert
        assert subscription == expected

    async def test_get_subscription_not_found(self, service, mock_db):
        """Test getting a non-existent subscription."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        subscription = await service.get_subscription("sub_nonexistent")

        # Assert
        assert subscription is None

    async def test_get_subscription_excludes_deleted(self, service, mock_db):
        """Test that deleted subscriptions are not returned."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        subscription = await service.get_subscription("sub_deleted")

        # Assert
        assert subscription is None

    async def test_update_subscription_success(self, service, mock_db):
        """Test successful subscription update."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Original Name",
            target_url="https://old.example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        update_request = UpdateSubscriptionRequest(
            name="Updated Name",
            target_url="https://new.example.com",
        )

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            updated = await service.update_subscription("sub_test123", update_request)

        # Assert
        assert updated.name == "Updated Name"
        assert updated.target_url == "https://new.example.com"

    async def test_update_subscription_partial(self, service, mock_db):
        """Test partial subscription update."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Original Name",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        update_request = UpdateSubscriptionRequest(name="Only Name Changed")

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            updated = await service.update_subscription("sub_test123", update_request)

        # Assert
        assert updated.name == "Only Name Changed"
        assert updated.target_url == "https://example.com"  # Unchanged

    async def test_update_subscription_not_found(self, service, mock_db):
        """Test update of non-existent subscription."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        update_request = UpdateSubscriptionRequest(name="New Name")

        # Act
        result = await service.update_subscription("sub_nonexistent", update_request)

        # Assert
        assert result is None

    async def test_delete_subscription_success(self, service, mock_db):
        """Test successful subscription deletion (soft delete)."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            result = await service.delete_subscription("sub_test123")

        # Assert
        assert result is True
        assert existing.status == SubscriptionStatus.DELETED
        assert existing.deleted_at is not None

    async def test_delete_subscription_not_found(self, service, mock_db):
        """Test deletion of non-existent subscription."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.delete_subscription("sub_nonexistent")

        # Assert
        assert result is False

    async def test_rotate_signing_secret(self, service, mock_db):
        """Test signing secret rotation."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="old_secret",
            status=SubscriptionStatus.ACTIVE,
            metadata={},
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            result = await service.rotate_signing_secret("sub_test123", grace_period_hours=24)

        # Assert
        assert result is not None
        new_secret, expiry = result
        assert new_secret != "old_secret"
        assert existing.signing_secret == new_secret
        assert "previous_signing_secret" in existing.metadata
        assert existing.metadata["previous_signing_secret"] == "old_secret"

    async def test_pause_subscription(self, service, mock_db):
        """Test pausing a subscription."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            result = await service.pause_subscription("sub_test123")

        # Assert
        assert result is True
        assert existing.status == SubscriptionStatus.PAUSED

    async def test_resume_subscription_from_paused(self, service, mock_db):
        """Test resuming a paused subscription."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.PAUSED,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        with patch.object(service, "_invalidate_cache", new_callable=AsyncMock):
            # Act
            result = await service.resume_subscription("sub_test123")

        # Assert
        assert result is True
        assert existing.status == SubscriptionStatus.ACTIVE

    async def test_resume_subscription_not_paused(self, service, mock_db):
        """Test resuming a non-paused subscription fails."""
        # Arrange
        existing = Subscription(
            id="sub_test123",
            name="Test",
            target_url="https://example.com",
            signing_secret="secret",
            status=SubscriptionStatus.ACTIVE,  # Not paused
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        # Act
        result = await service.resume_subscription("sub_test123")

        # Assert
        assert result is False

    async def test_list_subscriptions(self, service, mock_db):
        """Test listing subscriptions."""
        # Arrange
        subscriptions = [
            Subscription(
                id=f"sub_{i}",
                name=f"Sub {i}",
                target_url="https://example.com",
                signing_secret="secret",
                status=SubscriptionStatus.ACTIVE,
            )
            for i in range(3)
        ]

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = subscriptions
        mock_db.execute.return_value = mock_result

        # Act
        result, cursor = await service.list_subscriptions(limit=10)

        # Assert
        assert len(result) == 3

    async def test_list_subscriptions_with_status_filter(self, service, mock_db):
        """Test listing subscriptions with status filter."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Act
        result, cursor = await service.list_subscriptions(
            status=SubscriptionStatus.PAUSED,
            limit=10,
        )

        # Assert
        mock_db.execute.assert_called_once()

    async def test_get_stats(self, service, mock_db):
        """Test getting subscription statistics."""
        # Arrange
        mock_result = AsyncMock()
        mock_result.__iter__ = lambda self: iter([
            (SubscriptionStatus.ACTIVE, True, 5),
            (SubscriptionStatus.ACTIVE, False, 2),
            (SubscriptionStatus.PAUSED, True, 1),
        ])
        mock_db.execute.return_value = mock_result

        # Act
        stats = await service.get_stats()

        # Assert
        assert stats["total_subscriptions"] == 8
        assert stats["active"] == 7
        assert stats["paused"] == 1
        assert stats["healthy"] == 6
        assert stats["unhealthy"] == 2
