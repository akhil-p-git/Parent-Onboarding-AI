"""
Test Factories.

Factory Boy factories for generating test data.
"""

import factory
from factory import Faker, LazyAttribute, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from app.core.security import generate_api_key, generate_signing_secret, hash_api_key
from app.core.utils import generate_prefixed_id
from app.models import (
    ApiKey,
    ApiKeyScope,
    DeliveryStatus,
    Event,
    EventDelivery,
    EventStatus,
    Subscription,
    SubscriptionStatus,
)


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""

    class Meta:
        abstract = True


class ApiKeyFactory(BaseFactory):
    """Factory for creating ApiKey instances."""

    class Meta:
        model = ApiKey

    id = LazyAttribute(lambda _: generate_prefixed_id("key"))
    name = Faker("company")
    description = Faker("sentence")
    key_prefix = LazyAttribute(lambda o: o._raw_key[:12] if hasattr(o, "_raw_key") else "sk_test_1234")
    key_hash = LazyAttribute(
        lambda o: hash_api_key(o._raw_key) if hasattr(o, "_raw_key") else hash_api_key("test")
    )
    scopes = [
        ApiKeyScope.EVENTS_WRITE,
        ApiKeyScope.EVENTS_READ,
        ApiKeyScope.INBOX_READ,
        ApiKeyScope.SUBSCRIPTIONS_READ,
        ApiKeyScope.SUBSCRIPTIONS_WRITE,
    ]
    environment = "test"
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Generate raw key before creation."""
        raw_key = generate_api_key()
        obj = super()._create(model_class, *args, **kwargs)
        obj._raw_key = raw_key
        obj.key_prefix = raw_key[:12]
        obj.key_hash = hash_api_key(raw_key)
        return obj

    @classmethod
    def create_with_raw_key(cls, **kwargs):
        """Create an API key and return both model and raw key."""
        raw_key = generate_api_key()
        kwargs["key_prefix"] = raw_key[:12]
        kwargs["key_hash"] = hash_api_key(raw_key)
        obj = cls.create(**kwargs)
        return {"model": obj, "raw_key": raw_key}


class EventFactory(BaseFactory):
    """Factory for creating Event instances."""

    class Meta:
        model = Event

    id = LazyAttribute(lambda _: generate_prefixed_id("evt"))
    event_type = Faker(
        "random_element",
        elements=[
            "user.created",
            "user.updated",
            "user.deleted",
            "order.created",
            "order.completed",
            "order.cancelled",
            "payment.received",
            "payment.failed",
        ],
    )
    source = Faker(
        "random_element",
        elements=[
            "user-service",
            "order-service",
            "payment-service",
            "notification-service",
        ],
    )
    data = LazyAttribute(
        lambda o: {
            "id": Faker("uuid4").evaluate(None, None, {"locale": None}),
            "timestamp": Faker("iso8601").evaluate(None, None, {"locale": None}),
            "details": {"key": "value"},
        }
    )
    metadata = LazyAttribute(lambda _: {"environment": "test", "version": "1.0"})
    status = EventStatus.PENDING
    idempotency_key = None


class PendingEventFactory(EventFactory):
    """Factory for pending events."""

    status = EventStatus.PENDING


class ProcessingEventFactory(EventFactory):
    """Factory for processing events."""

    status = EventStatus.PROCESSING


class DeliveredEventFactory(EventFactory):
    """Factory for delivered events."""

    status = EventStatus.DELIVERED


class FailedEventFactory(EventFactory):
    """Factory for failed events."""

    status = EventStatus.FAILED


class SubscriptionFactory(BaseFactory):
    """Factory for creating Subscription instances."""

    class Meta:
        model = Subscription

    id = LazyAttribute(lambda _: generate_prefixed_id("sub"))
    name = Faker("company")
    description = Faker("sentence")
    target_url = Faker("url", schemes=["https"])
    signing_secret = LazyAttribute(lambda _: generate_signing_secret())
    event_types = ["user.created", "user.updated"]
    event_sources = None
    filters = None
    custom_headers = None
    status = SubscriptionStatus.ACTIVE
    is_healthy = True
    retry_strategy = "exponential"
    max_retries = 5
    retry_delay_seconds = 60
    retry_max_delay_seconds = 3600
    timeout_seconds = 30
    consecutive_failures = 0
    total_deliveries = 0
    successful_deliveries = 0
    failed_deliveries = 0
    api_key_id = None
    metadata = None


class ActiveSubscriptionFactory(SubscriptionFactory):
    """Factory for active subscriptions."""

    status = SubscriptionStatus.ACTIVE
    is_healthy = True


class PausedSubscriptionFactory(SubscriptionFactory):
    """Factory for paused subscriptions."""

    status = SubscriptionStatus.PAUSED


class UnhealthySubscriptionFactory(SubscriptionFactory):
    """Factory for unhealthy subscriptions."""

    is_healthy = False
    consecutive_failures = 5
    last_failure_reason = "Connection refused"


class EventDeliveryFactory(BaseFactory):
    """Factory for creating EventDelivery instances."""

    class Meta:
        model = EventDelivery

    id = LazyAttribute(lambda _: generate_prefixed_id("del"))
    event_id = None  # Must be set explicitly
    subscription_id = None  # Must be set explicitly
    status = DeliveryStatus.PENDING
    attempt_count = 0
    max_attempts = 5
    request_url = Faker("url", schemes=["https"])
    request_headers = None
    request_body = None
    response_status_code = None
    response_headers = None
    response_body = None
    response_time_ms = None
    error_type = None
    error_message = None
    signature = None
    retry_delay_seconds = None
    attempt_history = None


class PendingDeliveryFactory(EventDeliveryFactory):
    """Factory for pending deliveries."""

    status = DeliveryStatus.PENDING


class InFlightDeliveryFactory(EventDeliveryFactory):
    """Factory for in-flight deliveries."""

    status = DeliveryStatus.IN_FLIGHT
    attempt_count = 1


class DeliveredDeliveryFactory(EventDeliveryFactory):
    """Factory for successful deliveries."""

    status = DeliveryStatus.DELIVERED
    attempt_count = 1
    response_status_code = 200
    response_time_ms = 150


class FailedDeliveryFactory(EventDeliveryFactory):
    """Factory for failed deliveries."""

    status = DeliveryStatus.EXHAUSTED
    attempt_count = 5
    error_type = "http_error"
    error_message = "HTTP 500"


# ============================================================================
# Batch Factories
# ============================================================================


class EventBatchFactory:
    """Factory for creating batches of events."""

    @staticmethod
    def create_batch(count: int = 10, **kwargs) -> list[Event]:
        """Create a batch of events."""
        return EventFactory.create_batch(count, **kwargs)

    @staticmethod
    def build_batch(count: int = 10, **kwargs) -> list[Event]:
        """Build a batch of events without saving."""
        return EventFactory.build_batch(count, **kwargs)


class SubscriptionBatchFactory:
    """Factory for creating batches of subscriptions."""

    @staticmethod
    def create_batch(count: int = 5, **kwargs) -> list[Subscription]:
        """Create a batch of subscriptions."""
        return SubscriptionFactory.create_batch(count, **kwargs)


# ============================================================================
# Request Data Factories
# ============================================================================


class CreateEventRequestFactory(factory.Factory):
    """Factory for creating event request payloads."""

    class Meta:
        model = dict

    event_type = Faker(
        "random_element",
        elements=["user.created", "order.completed", "payment.received"],
    )
    source = Faker(
        "random_element",
        elements=["api", "webhook", "system"],
    )
    data = LazyAttribute(
        lambda _: {
            "id": Faker("uuid4").evaluate(None, None, {"locale": None}),
            "action": "create",
        }
    )
    metadata = LazyAttribute(lambda _: {"environment": "test"})


class CreateSubscriptionRequestFactory(factory.Factory):
    """Factory for creating subscription request payloads."""

    class Meta:
        model = dict

    name = Faker("company")
    target_url = Faker("url", schemes=["https"])
    filters = LazyAttribute(
        lambda _: {
            "event_types": ["user.created", "user.updated"],
        }
    )
    webhook_config = LazyAttribute(
        lambda _: {
            "timeout_seconds": 30,
            "retry_strategy": "exponential",
            "max_retries": 5,
        }
    )


class BatchEventRequestFactory(factory.Factory):
    """Factory for creating batch event request payloads."""

    class Meta:
        model = dict

    events = LazyAttribute(
        lambda _: [
            CreateEventRequestFactory.build() for _ in range(10)
        ]
    )
