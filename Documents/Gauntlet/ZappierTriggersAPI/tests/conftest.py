"""
Pytest configuration and fixtures.

Provides comprehensive test fixtures for unit, integration, and e2e tests.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Set test environment before importing app modules
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use DB 15 for tests

pytest_plugins = ["pytest_asyncio"]


# ============================================================================
# Event Loop Fixture
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine (SQLite in-memory)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest_asyncio.fixture
async def db_session_committed(
    test_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session that commits.

    Use this for integration tests that need committed data.
    """
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.commit()


# ============================================================================
# Redis Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[Any, None]:
    """Create a test Redis client."""
    import redis.asyncio as redis

    client = redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/15"),
        decode_responses=True,
    )

    try:
        await client.ping()
        # Clear test database
        await client.flushdb()
        yield client
    except Exception:
        # Redis not available, yield mock
        pytest.skip("Redis not available")
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def mock_redis(mocker) -> Any:
    """Create a mock Redis client for unit tests."""
    mock = mocker.AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.ping.return_value = True
    mock.llen.return_value = 0
    mock.lpush.return_value = 1
    mock.rpop.return_value = None
    mock.info.return_value = {"redis_version": "7.0.0"}
    return mock


# ============================================================================
# Application Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def app(test_engine: AsyncEngine) -> AsyncGenerator[FastAPI, None]:
    """Create a test FastAPI application."""
    from app.main import app as fastapi_app

    # Override database dependency
    from app.api.deps import get_db
    from app.core.database import get_session_factory

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield fastapi_app

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Generator[Any, None, None]:
    """Create a synchronous test client."""
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Authentication Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_api_key(db_session: AsyncSession) -> Any:
    """Create a test API key in the database."""
    from app.core.security import generate_api_key, hash_api_key
    from app.core.utils import generate_prefixed_id
    from app.models import ApiKey, ApiKeyScope

    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    api_key = ApiKey(
        id=generate_prefixed_id("key"),
        name="Test API Key",
        key_hash=hashed_key,
        key_prefix=raw_key[:12],
        scopes=[
            ApiKeyScope.EVENTS_WRITE,
            ApiKeyScope.EVENTS_READ,
            ApiKeyScope.INBOX_READ,
            ApiKeyScope.SUBSCRIPTIONS_READ,
            ApiKeyScope.SUBSCRIPTIONS_WRITE,
            ApiKeyScope.SUBSCRIPTIONS_DELETE,
        ],
        environment="test",
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.flush()

    # Return both raw key and model
    return {"raw_key": raw_key, "model": api_key}


@pytest.fixture
def auth_headers(test_api_key: dict) -> dict[str, str]:
    """Return authorization headers with test API key."""
    return {"Authorization": f"Bearer {test_api_key['raw_key']}"}


@pytest_asyncio.fixture
async def readonly_api_key(db_session: AsyncSession) -> Any:
    """Create a read-only test API key."""
    from app.core.security import generate_api_key, hash_api_key
    from app.core.utils import generate_prefixed_id
    from app.models import ApiKey, ApiKeyScope

    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)

    api_key = ApiKey(
        id=generate_prefixed_id("key"),
        name="Read-only API Key",
        key_hash=hashed_key,
        key_prefix=raw_key[:12],
        scopes=[
            ApiKeyScope.EVENTS_READ,
            ApiKeyScope.INBOX_READ,
            ApiKeyScope.SUBSCRIPTIONS_READ,
        ],
        environment="test",
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.flush()

    return {"raw_key": raw_key, "model": api_key}


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def sample_event(db_session: AsyncSession) -> Any:
    """Create a sample event in the database."""
    from app.core.utils import generate_prefixed_id
    from app.models import Event, EventStatus

    event = Event(
        id=generate_prefixed_id("evt"),
        event_type="user.created",
        source="test-service",
        data={"user_id": "123", "email": "test@example.com"},
        metadata={"test": True},
        status=EventStatus.PENDING,
    )
    db_session.add(event)
    await db_session.flush()
    return event


@pytest_asyncio.fixture
async def sample_subscription(db_session: AsyncSession, test_api_key: dict) -> Any:
    """Create a sample subscription in the database."""
    from app.core.security import generate_signing_secret
    from app.core.utils import generate_prefixed_id
    from app.models import Subscription, SubscriptionStatus

    subscription = Subscription(
        id=generate_prefixed_id("sub"),
        name="Test Subscription",
        target_url="https://webhook.example.com/events",
        signing_secret=generate_signing_secret(),
        event_types=["user.created", "user.updated"],
        status=SubscriptionStatus.ACTIVE,
        api_key_id=test_api_key["model"].id,
    )
    db_session.add(subscription)
    await db_session.flush()
    return subscription


@pytest_asyncio.fixture
async def sample_delivery(
    db_session: AsyncSession,
    sample_event: Any,
    sample_subscription: Any,
) -> Any:
    """Create a sample delivery in the database."""
    from app.core.utils import generate_prefixed_id, utc_now
    from app.models import DeliveryStatus, EventDelivery

    delivery = EventDelivery(
        id=generate_prefixed_id("del"),
        event_id=sample_event.id,
        subscription_id=sample_subscription.id,
        status=DeliveryStatus.PENDING,
        max_attempts=3,
        scheduled_at=utc_now(),
        request_url=sample_subscription.target_url,
    )
    db_session.add(delivery)
    await db_session.flush()
    return delivery


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_event_data() -> dict[str, Any]:
    """Return sample event data for API requests."""
    return {
        "event_type": "order.completed",
        "source": "checkout-service",
        "data": {
            "order_id": "ord_12345",
            "customer_id": "cust_67890",
            "total": 99.99,
            "items": [{"sku": "ITEM-001", "quantity": 2}],
        },
        "metadata": {"environment": "test"},
    }


@pytest.fixture
def sample_subscription_data() -> dict[str, Any]:
    """Return sample subscription data for API requests."""
    return {
        "name": "Order Notifications",
        "target_url": "https://api.example.com/webhooks/orders",
        "filters": {
            "event_types": ["order.completed", "order.cancelled"],
            "event_sources": ["checkout-service"],
        },
        "webhook_config": {
            "timeout_seconds": 30,
            "retry_strategy": "exponential",
            "max_retries": 5,
        },
    }


# ============================================================================
# Markers
# ============================================================================


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (with real DB)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full stack)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "redis: Tests requiring Redis")
