"""
Events API Endpoints.

Handles event ingestion for the Triggers API.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentApiKey,
    DBSession,
    require_scopes,
)
from app.models import ApiKey, ApiKeyScope, EventStatus
from app.schemas import (
    BatchCreateEventRequest,
    BatchCreateEventResponse,
    CreateEventRequest,
    EventFilterParams,
    EventListResponse,
    EventResponse,
    PaginationMeta,
    ReplayEventRequest,
    ReplayEventResponse,
    ReplayPreviewResponse,
)
from app.schemas.error import (
    ConflictErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
)
from app.services.event_service import EventService, IdempotencyError
from app.services.replay_service import (
    ReplayService,
    EventNotFoundError,
    EventNotReplayableError,
    SubscriptionNotFoundError,
)
from app.services.streaming_service import StreamingService, get_streaming_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_event_service(db: DBSession) -> EventService:
    """Get event service instance."""
    return EventService(db)


async def get_replay_service(db: DBSession) -> ReplayService:
    """Get replay service instance."""
    return ReplayService(db)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
ReplayServiceDep = Annotated[ReplayService, Depends(get_replay_service)]
StreamingServiceDep = Annotated[StreamingService, Depends(get_streaming_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventResponse,
    responses={
        201: {"description": "Event created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
        409: {"model": ConflictErrorResponse, "description": "Idempotency key conflict"},
    },
    summary="Create Event",
    description="Create a single event to be processed and delivered to subscribers.",
)
async def create_event(
    request: CreateEventRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: EventServiceDep,
) -> EventResponse:
    """
    Create a new event.

    The event will be:
    1. Validated against the schema
    2. Persisted to the database
    3. Queued for delivery to matching subscriptions

    If an idempotency_key is provided and has been used before,
    the existing event will be returned with a 409 status.
    """
    try:
        event = await service.create_event(request, api_key_id=api_key.id)

        return EventResponse(
            id=event.id,
            event_type=event.event_type,
            source=event.source,
            data=event.data,
            metadata=event.event_meta,
            status=event.status,
            idempotency_key=event.idempotency_key,
            created_at=event.created_at,
            updated_at=event.updated_at,
            delivery_attempts=event.delivery_attempts,
            successful_deliveries=event.successful_deliveries,
            failed_deliveries=event.failed_deliveries,
        )

    except IdempotencyError as e:
        # Return existing event for idempotency
        existing_event = await service.get_event(e.existing_event_id)
        if existing_event:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "type": "https://api.zapier.com/errors/conflict",
                    "title": "Idempotency Key Conflict",
                    "status": 409,
                    "detail": f"Idempotency key already used for event: {e.existing_event_id}",
                    "existing_event_id": e.existing_event_id,
                },
            )
        raise


@router.post(
    "/batch",
    status_code=status.HTTP_201_CREATED,
    response_model=BatchCreateEventResponse,
    responses={
        201: {"description": "Batch processed (check individual results)"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
    },
    summary="Create Events (Batch)",
    description="Create multiple events in a single request. Maximum 100 events per batch.",
)
async def create_events_batch(
    request: BatchCreateEventRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: EventServiceDep,
) -> BatchCreateEventResponse:
    """
    Create multiple events in a batch.

    Each event is processed independently. The response includes
    per-item results indicating success or failure.

    If fail_fast is true, processing stops on the first error
    and remaining events are marked as skipped.
    """
    result = await service.create_events_batch(request, api_key_id=api_key.id)

    # Return 201 even for partial success
    # Clients should check the results for individual failures
    return result


@router.get(
    "",
    response_model=EventListResponse,
    summary="List Events",
    description="List events with optional filtering and pagination.",
)
async def list_events(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: EventServiceDep,
    event_type: Annotated[str | None, Query(description="Filter by event type")] = None,
    source: Annotated[str | None, Query(description="Filter by source")] = None,
    event_status: Annotated[
        EventStatus | None,
        Query(alias="status", description="Filter by status"),
    ] = None,
    since: Annotated[
        datetime | None,
        Query(description="Filter events created after this time"),
    ] = None,
    until: Annotated[
        datetime | None,
        Query(description="Filter events created before this time"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Max events to return")] = 100,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
) -> EventListResponse:
    """
    List events with optional filters.

    Results are ordered by creation time (newest first).
    Use cursor-based pagination for large result sets.
    """
    events, next_cursor = await service.list_events(
        event_type=event_type,
        source=source,
        status=event_status,
        since=since,
        until=until,
        limit=limit,
        cursor=cursor,
    )

    event_responses = [
        EventResponse(
            id=event.id,
            event_type=event.event_type,
            source=event.source,
            data=event.data,
            metadata=event.event_meta,
            status=event.status,
            idempotency_key=event.idempotency_key,
            created_at=event.created_at,
            updated_at=event.updated_at,
            processed_at=event.processed_at,
            delivery_attempts=event.delivery_attempts,
            successful_deliveries=event.successful_deliveries,
            failed_deliveries=event.failed_deliveries,
        )
        for event in events
    ]

    return EventListResponse(
        data=event_responses,
        pagination=PaginationMeta(
            limit=limit,
            has_more=next_cursor is not None,
            next_cursor=next_cursor,
        ),
    )


@router.get(
    "/stream",
    summary="Stream Events (SSE)",
    description="Real-time event streaming via Server-Sent Events.",
    responses={
        200: {
            "description": "SSE stream started",
            "content": {"text/event-stream": {}},
        },
    },
)
async def stream_events(
    request: Request,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    streaming_service: StreamingServiceDep,
    event_types: Annotated[
        str | None,
        Query(
            description="Comma-separated event types to filter (supports wildcards like 'user.*')"
        ),
    ] = None,
    sources: Annotated[
        str | None,
        Query(description="Comma-separated sources to filter"),
    ] = None,
    subscription_id: Annotated[
        str | None,
        Query(description="Filter events for a specific subscription"),
    ] = None,
) -> EventSourceResponse:
    """
    Stream events in real-time via Server-Sent Events (SSE).

    This endpoint provides a persistent connection that streams events as they occur.
    Use query parameters to filter which events you receive.

    **Event Types:**
    - `connected`: Sent when connection is established
    - `event`: New event matching your filters
    - `heartbeat`: Sent every 15 seconds to keep connection alive
    - `error`: Sent if there's a stream error

    **Filtering:**
    - `event_types`: Filter by event type patterns (e.g., "user.*,order.created")
    - `sources`: Filter by source patterns (e.g., "auth-service,payment")
    - `subscription_id`: Filter events targeting a specific subscription

    **Example usage:**
    ```bash
    curl -N -H "Authorization: Bearer <api_key>" \\
        "https://api.example.com/api/v1/events/stream?event_types=user.*"
    ```
    """
    # Parse filter parameters
    type_list = None
    if event_types:
        type_list = [t.strip() for t in event_types.split(",") if t.strip()]

    source_list = None
    if sources:
        source_list = [s.strip() for s in sources.split(",") if s.strip()]

    async def event_generator():
        """Generate SSE events from the stream."""
        try:
            async for event_data in streaming_service.stream_events(
                event_types=type_list,
                sources=source_list,
                subscription_id=subscription_id,
            ):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                # Format the event for SSE
                event_type = event_data.get("event", "message")
                data = event_data.get("data", {})
                event_id = event_data.get("id")

                yield {
                    "event": event_type,
                    "data": json.dumps(data),
                    "id": event_id,
                }

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled by client")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": "Stream error", "error": str(e)}),
            }

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    responses={
        200: {"description": "Event found"},
        404: {"model": NotFoundErrorResponse, "description": "Event not found"},
    },
    summary="Get Event",
    description="Retrieve a specific event by ID.",
)
async def get_event(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: EventServiceDep,
) -> EventResponse:
    """
    Get event details by ID.

    Returns the full event including payload, metadata, and delivery status.
    """
    event = await service.get_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Event Not Found",
                "status": 404,
                "detail": f"Event with ID '{event_id}' not found",
                "instance": f"/api/v1/events/{event_id}",
            },
        )

    return EventResponse(
        id=event.id,
        event_type=event.event_type,
        source=event.source,
        data=event.data,
        metadata=event.event_meta,
        status=event.status,
        idempotency_key=event.idempotency_key,
        created_at=event.created_at,
        updated_at=event.updated_at,
        processed_at=event.processed_at,
        delivery_attempts=event.delivery_attempts,
        successful_deliveries=event.successful_deliveries,
        failed_deliveries=event.failed_deliveries,
    )


@router.get(
    "/{event_id}/deliveries",
    summary="Get Event Deliveries",
    description="Get delivery attempts for a specific event.",
)
async def get_event_deliveries(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: EventServiceDep,
):
    """
    Get delivery history for an event.

    Returns all delivery attempts including status, timestamps, and response details.
    """
    event = await service.get_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Event Not Found",
                "status": 404,
                "detail": f"Event with ID '{event_id}' not found",
            },
        )

    # Return delivery records
    deliveries = []
    if hasattr(event, "deliveries") and event.deliveries:
        for delivery in event.deliveries:
            deliveries.append({
                "id": delivery.id,
                "subscription_id": delivery.subscription_id,
                "status": delivery.status,
                "attempt_count": delivery.attempt_count,
                "response_status_code": delivery.response_status_code,
                "response_time_ms": delivery.response_time_ms,
                "error_type": delivery.error_type,
                "error_message": delivery.error_message,
                "created_at": delivery.created_at.isoformat() if delivery.created_at else None,
                "completed_at": delivery.completed_at.isoformat() if delivery.completed_at else None,
            })

    return {
        "event_id": event_id,
        "total_deliveries": len(deliveries),
        "deliveries": deliveries,
    }


@router.post(
    "/{event_id}/replay",
    response_model=ReplayEventResponse,
    responses={
        200: {"description": "Event replayed successfully"},
        400: {"model": ValidationErrorResponse, "description": "Invalid replay request"},
        404: {"model": NotFoundErrorResponse, "description": "Event not found"},
    },
    summary="Replay Event",
    description="Replay an existing event for debugging or recovery purposes.",
)
async def replay_event(
    event_id: str,
    request: ReplayEventRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: ReplayServiceDep,
) -> ReplayEventResponse:
    """
    Replay an event to matching subscriptions.

    This endpoint allows you to:
    - Re-send an event to all matching subscriptions
    - Target specific subscriptions with target_subscription_ids
    - Modify the payload or metadata before replaying
    - Use dry_run=true to preview what would happen

    The replayed event creates a new event record with a reference to the original.
    """
    try:
        result = await service.replay_event(
            event_id=event_id,
            dry_run=request.dry_run,
            target_subscription_ids=request.target_subscription_ids,
            payload_override=request.payload_override,
            metadata_override=request.metadata_override,
            api_key_id=api_key.id,
        )

        return ReplayEventResponse(
            success=result.success,
            event_id=result.event_id,
            replay_event_id=result.replay_event_id,
            dry_run=result.dry_run,
            target_subscriptions=result.target_subscriptions,
            message=result.message,
            details=result.details,
        )

    except EventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Event Not Found",
                "status": 404,
                "detail": e.message,
                "instance": f"/api/v1/events/{event_id}/replay",
            },
        )

    except EventNotReplayableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://api.zapier.com/errors/bad-request",
                "title": "Event Not Replayable",
                "status": 400,
                "detail": e.message,
                "code": e.code,
            },
        )

    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": e.message,
            },
        )


@router.get(
    "/{event_id}/replay/preview",
    response_model=ReplayPreviewResponse,
    responses={
        200: {"description": "Replay preview generated"},
        404: {"model": NotFoundErrorResponse, "description": "Event not found"},
    },
    summary="Preview Event Replay",
    description="Preview what would happen if an event is replayed.",
)
async def preview_event_replay(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: ReplayServiceDep,
    target_subscription_ids: Annotated[
        str | None,
        Query(description="Comma-separated list of subscription IDs to target"),
    ] = None,
) -> ReplayPreviewResponse:
    """
    Preview what a replay operation would do.

    Returns information about:
    - The original event
    - The payload that would be sent
    - Subscriptions that would receive the replay

    This is a read-only operation that does not modify any data.
    """
    try:
        # Parse target subscription IDs if provided
        sub_ids = None
        if target_subscription_ids:
            sub_ids = [s.strip() for s in target_subscription_ids.split(",") if s.strip()]

        preview = await service.get_replay_preview(
            event_id=event_id,
            target_subscription_ids=sub_ids,
        )

        return ReplayPreviewResponse(**preview)

    except EventNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Event Not Found",
                "status": 404,
                "detail": e.message,
            },
        )

    except SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": e.message,
            },
        )
