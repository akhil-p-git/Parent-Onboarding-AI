"""
API v1 Router - Aggregates all API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import dlq, events, health, inbox, subscriptions

api_router = APIRouter()

# Health endpoints (no auth required)
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["System"],
)

# Event endpoints
api_router.include_router(
    events.router,
    prefix="/events",
    tags=["Events"],
)

# Inbox endpoints
api_router.include_router(
    inbox.router,
    prefix="/inbox",
    tags=["Inbox"],
)

# Subscription endpoints
api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"],
)

# Dead Letter Queue endpoints
api_router.include_router(
    dlq.router,
    prefix="/dlq",
    tags=["Dead Letter Queue"],
)
