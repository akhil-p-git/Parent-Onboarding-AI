# Triggers CLI

Command-line tool for interacting with the Zapier Triggers API.

## Installation

```bash
# Install from source
cd cli
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

Set your API credentials using environment variables:

```bash
export TRIGGERS_API_URL=http://localhost:8000
export TRIGGERS_API_KEY=your_api_key_here
```

Or pass them as command-line options:

```bash
triggers --api-url http://localhost:8000 --api-key your_key events list
```

Or save to config file:

```bash
triggers config --set-url http://localhost:8000 --set-key your_key
```

## Commands

### Events

```bash
# Send a single event
triggers events send user.created my-service -d '{"user_id": "123", "email": "user@example.com"}'

# Send event from a file
triggers events send order.completed orders -f order_data.json

# Send batch of events
triggers events send-batch events.json

# List events
triggers events list
triggers events list --type user.created --status pending --limit 50

# Get event details
triggers events get evt_123abc

# Replay an event
triggers events replay evt_123abc
triggers events replay evt_123abc --dry-run
triggers events replay evt_123abc --subscriptions sub_1,sub_2

# Stream events in real-time
triggers events stream
triggers events stream --types user.created,order.completed
```

### Inbox

```bash
# List pending events in inbox
triggers inbox list
triggers inbox list --subscription sub_123 --limit 10

# Poll inbox continuously
triggers inbox poll --interval 5 --auto-ack

# Acknowledge processed events
triggers inbox ack "receipt_handle_1,receipt_handle_2"

# Get inbox statistics
triggers inbox stats
```

### Forward (Local Development)

Forward events from the Triggers API to your local development server:

```bash
# Forward to local webhook endpoint
triggers forward http://localhost:3000/webhooks

# Forward specific event types
triggers forward http://localhost:3000/hooks -t user.created,order.completed

# Forward with verbose output
triggers forward http://localhost:8080/api/events -v
```

### Dead Letter Queue

```bash
# List DLQ items
triggers dlq list
triggers dlq list --type user.created --limit 50

# Retry a failed event
triggers dlq retry evt_123abc

# Retry all matching events
triggers dlq retry-all --type user.created -y

# Dismiss an event
triggers dlq dismiss evt_123abc -y
```

### Other Commands

```bash
# Check API health
triggers health

# List subscriptions
triggers subscriptions

# View/update configuration
triggers config --show
triggers config --set-url http://api.example.com
```

## Output Formats

Most commands support different output formats:

```bash
# Table format (default)
triggers events list

# JSON format
triggers events list --format json

# Pipe to jq for processing
triggers events list -o json | jq '.data[].id'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRIGGERS_API_URL` | API base URL | `http://localhost:8000` |
| `TRIGGERS_API_KEY` | API authentication key | - |
| `TRIGGERS_OUTPUT_FORMAT` | Default output format | `table` |
| `TRIGGERS_TIMEOUT` | Request timeout (seconds) | `30` |
| `TRIGGERS_VERBOSE` | Enable verbose output | `false` |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=triggers_cli

# Format code
ruff format .

# Lint code
ruff check .
```

## Examples

### Send Event from Stdin

```bash
echo '{"user_id": "123"}' | triggers events send user.created my-service
```

### Process Events in a Script

```bash
#!/bin/bash
triggers inbox list -o json | jq -r '.data[].receipt_handle' | while read handle; do
    # Process event...
    triggers inbox ack "$handle"
done
```

### Watch Events in Real-Time

```bash
triggers events stream | while read event; do
    echo "Received: $event"
done
```
