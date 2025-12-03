# Zapier Triggers Python SDK

Official Python SDK for the Zapier Triggers API.

## Installation

```bash
pip install zapier-triggers
```

## Quick Start

```python
import asyncio
from zapier_triggers import TriggersClient

async def main():
    async with TriggersClient(api_key="your_api_key") as client:
        # Send an event
        event = await client.events.create(
            event_type="user.created",
            source="my-app",
            data={"user_id": "123", "email": "user@example.com"},
        )
        print(f"Created event: {event.id}")

        # List events
        events = await client.events.list(event_type="user.created", limit=10)
        for e in events:
            print(f"  {e.id}: {e.event_type} - {e.status}")

asyncio.run(main())
```

## Features

- **Async/await support** - Built on httpx for high-performance async HTTP
- **Type hints** - Full type annotations for IDE support
- **Automatic retries** - Configurable retry logic for failed requests
- **Pagination helpers** - Easy iteration over paginated results
- **Pydantic models** - Response data is validated and typed

## Configuration

### Client Options

```python
from zapier_triggers import TriggersClient

client = TriggersClient(
    api_key="your_api_key",          # Required: API key for auth
    base_url="https://api.zapier.com", # Optional: API base URL
    timeout=30.0,                     # Optional: Request timeout (seconds)
    max_retries=3,                    # Optional: Max retry attempts
)
```

### Environment Variables

You can also configure via environment variables:

```bash
export TRIGGERS_API_KEY=your_api_key
export TRIGGERS_API_URL=https://api.zapier.com
```

## API Reference

### Events

#### Create an Event

```python
event = await client.events.create(
    event_type="user.created",
    source="auth-service",
    data={"user_id": "123", "email": "user@example.com"},
    metadata={"trace_id": "abc123"},
    idempotency_key="user-123-created",  # Optional: prevent duplicates
)
```

#### Batch Create Events

```python
result = await client.events.batch_create([
    {"event_type": "user.created", "source": "auth", "data": {"id": "1"}},
    {"event_type": "user.created", "source": "auth", "data": {"id": "2"}},
])
print(f"Created: {result.successful}, Failed: {result.failed}")
```

#### Get an Event

```python
event = await client.events.get("evt_abc123")
print(f"Status: {event.status}")
```

#### List Events

```python
events = await client.events.list(
    event_type="user.created",
    source="auth-service",
    status="pending",
    limit=50,
)

for event in events:
    print(f"{event.id}: {event.event_type}")

# Check for more pages
if events.pagination.has_more:
    next_page = await client.events.list(
        cursor=events.pagination.next_cursor
    )
```

#### Iterate Over All Events

```python
# Automatically handles pagination
async for event in client.events.iterate(event_type="user.*"):
    print(f"Processing: {event.id}")
```

#### Replay an Event

```python
# Preview what would happen
preview = await client.events.replay("evt_123", dry_run=True)
print(f"Would replay to: {preview.target_subscriptions}")

# Execute replay
result = await client.events.replay("evt_123")
print(f"New event ID: {result.replay_event_id}")
```

### Inbox

#### List Inbox Items

```python
items = await client.inbox.list(
    subscription_id="sub_123",
    limit=10,
)

for item in items:
    print(f"Event: {item.event_type}")
    print(f"Data: {item.data}")
```

#### Acknowledge Items

```python
# Process items and acknowledge
items = await client.inbox.list(limit=10)
receipt_handles = []

for item in items:
    process_event(item.data)
    receipt_handles.append(item.receipt_handle)

result = await client.inbox.acknowledge(receipt_handles)
print(f"Acknowledged: {result.successful}")
```

#### Poll with Auto-Acknowledge

```python
# Long-running consumer
async for item in client.inbox.poll(
    subscription_id="sub_123",
    auto_acknowledge=True,
):
    await process_event(item.data)
    # Item is automatically acknowledged after processing
```

### Dead Letter Queue (DLQ)

#### List DLQ Items

```python
items = await client.dlq.list(event_type="order.*")

for item in items:
    print(f"Failed: {item.event_id}")
    print(f"Reason: {item.failure_reason}")
    print(f"Retries: {item.retry_count}")
```

#### Retry Failed Events

```python
# Retry a single event
result = await client.dlq.retry("evt_123")

# Retry multiple events
result = await client.dlq.batch_retry(["evt_123", "evt_456"])
print(f"Retried: {result.successful}")
```

#### Dismiss Events

```python
# Remove without retry
await client.dlq.dismiss("evt_123")

# Dismiss multiple
await client.dlq.batch_dismiss(["evt_123", "evt_456"])
```

## Error Handling

```python
from zapier_triggers import TriggersClient
from zapier_triggers.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

async with TriggersClient(api_key="...") as client:
    try:
        event = await client.events.get("evt_notfound")
    except NotFoundError as e:
        print(f"Event not found: {e.message}")
    except AuthenticationError as e:
        print(f"Auth failed: {e.message}")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after} seconds")
    except ValidationError as e:
        print(f"Validation failed: {e.validation_errors}")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=zapier_triggers

# Type checking
mypy zapier_triggers

# Linting
ruff check .
ruff format .
```

## License

MIT License - see LICENSE file for details.
