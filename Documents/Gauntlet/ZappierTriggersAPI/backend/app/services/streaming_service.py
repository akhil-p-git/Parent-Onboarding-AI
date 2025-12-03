"""
Event Streaming Service.

Provides real-time event streaming via Server-Sent Events (SSE)
using Redis pub/sub for event distribution.
"""

import asyncio
import fnmatch
import json
import logging
from datetime import datetime
from typing import Any, AsyncIterator

from redis.asyncio import Redis

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class StreamingService:
    """Service for streaming events in real-time via SSE."""

    # Redis pub/sub channel for events
    EVENTS_CHANNEL = "events:stream"

    # Heartbeat interval in seconds
    HEARTBEAT_INTERVAL = 15

    def __init__(self, redis_client: Redis | None = None):
        """
        Initialize the streaming service.

        Args:
            redis_client: Optional Redis client (for testing)
        """
        self._redis = redis_client
        self._pubsub = None

    async def get_redis(self) -> Redis:
        """Get Redis client."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    async def publish_event(self, event: dict[str, Any]) -> None:
        """
        Publish an event to the streaming channel.

        This should be called when a new event is created to notify
        all connected SSE clients.

        Args:
            event: Event data to publish
        """
        redis = await self.get_redis()
        message = json.dumps(event)
        await redis.publish(self.EVENTS_CHANNEL, message)
        logger.debug(f"Published event to stream: {event.get('id', 'unknown')}")

    async def stream_events(
        self,
        event_types: list[str] | None = None,
        sources: list[str] | None = None,
        subscription_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream events in real-time via Redis pub/sub.

        Args:
            event_types: Optional list of event type patterns to filter
                        (supports wildcards like "user.*")
            sources: Optional list of source patterns to filter
            subscription_id: Optional subscription ID to filter events for

        Yields:
            Event data dictionaries
        """
        redis = await self.get_redis()

        # Create a new pubsub connection for this stream
        pubsub = redis.pubsub()
        await pubsub.subscribe(self.EVENTS_CHANNEL)

        logger.info(
            f"SSE stream started - filters: types={event_types}, "
            f"sources={sources}, subscription={subscription_id}"
        )

        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": {
                    "message": "Connected to event stream",
                    "timestamp": datetime.utcnow().isoformat(),
                    "filters": {
                        "event_types": event_types,
                        "sources": sources,
                        "subscription_id": subscription_id,
                    },
                },
            }

            while True:
                try:
                    # Use get_message with timeout for non-blocking operation
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=self.HEARTBEAT_INTERVAL,
                    )

                    if message is not None and message["type"] == "message":
                        # Parse the event
                        try:
                            event_data = json.loads(message["data"])
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in stream: {message['data']}")
                            continue

                        # Apply filters
                        if not self._matches_filters(
                            event_data, event_types, sources, subscription_id
                        ):
                            continue

                        # Yield the event
                        yield {
                            "event": "event",
                            "data": event_data,
                            "id": event_data.get("id"),
                        }

                    else:
                        # No message received, send heartbeat
                        yield {
                            "event": "heartbeat",
                            "data": {
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        }

                except asyncio.CancelledError:
                    logger.info("SSE stream cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error in stream loop: {e}")
                    yield {
                        "event": "error",
                        "data": {
                            "message": "Stream error, attempting to recover",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                    # Brief pause before retry
                    await asyncio.sleep(1)

        finally:
            # Clean up subscription
            await pubsub.unsubscribe(self.EVENTS_CHANNEL)
            await pubsub.close()
            logger.info("SSE stream closed")

    def _matches_filters(
        self,
        event: dict[str, Any],
        event_types: list[str] | None,
        sources: list[str] | None,
        subscription_id: str | None,
    ) -> bool:
        """
        Check if an event matches the specified filters.

        Args:
            event: Event data
            event_types: Event type patterns (supports wildcards)
            sources: Source patterns (supports wildcards)
            subscription_id: Subscription ID filter

        Returns:
            True if event matches all filters
        """
        # Check event type filter
        if event_types:
            event_type = event.get("event_type", "")
            if not self._matches_patterns(event_type, event_types):
                return False

        # Check source filter
        if sources:
            source = event.get("source", "")
            if not self._matches_patterns(source, sources):
                return False

        # Check subscription filter
        if subscription_id:
            # Event must include this subscription in its targets
            target_subs = event.get("_target_subscriptions", [])
            if subscription_id not in target_subs:
                # Also check metadata for subscription info
                metadata = event.get("metadata", {})
                if metadata.get("subscription_id") != subscription_id:
                    return False

        return True

    def _matches_patterns(self, value: str, patterns: list[str]) -> bool:
        """
        Check if a value matches any of the patterns.

        Supports:
        - Exact match: "user.created"
        - Wildcard match: "user.*", "*.created"
        - Partial wildcard: "user.created.*"

        Args:
            value: Value to check
            patterns: List of patterns to match against

        Returns:
            True if value matches any pattern
        """
        for pattern in patterns:
            # Convert pattern to fnmatch format
            # "user.*" -> "user.*"
            if fnmatch.fnmatch(value, pattern):
                return True
        return False


# Global service instance
_streaming_service: StreamingService | None = None


async def get_streaming_service() -> StreamingService:
    """Get streaming service singleton."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service


async def publish_event_to_stream(event: dict[str, Any]) -> None:
    """
    Convenience function to publish an event to the stream.

    Args:
        event: Event data to publish
    """
    service = await get_streaming_service()
    await service.publish_event(event)
