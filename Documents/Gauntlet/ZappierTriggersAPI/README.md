# Zapier Triggers API

A unified, real-time event ingestion system for the Zapier platform. This RESTful API enables any external system to send events into Zapier, powering agentic workflows that react to events in real time.

## Quick Start

```bash
# Clone and setup
cd ZappierTriggersAPI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run locally
uvicorn backend.app.main:app --reload

# Send your first event
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer sk_test_your_key" \
  -H "Content-Type: application/json" \
  -d '{"type": "order.created", "source": "my-app", "data": {"order_id": "12345"}}'
```

## Features

- **Event Ingestion**: Accept JSON events via REST API
- **Inbox Model**: Queue-based event retrieval with acknowledgment
- **Batch Operations**: Send up to 100 events per request
- **Webhook Delivery**: Real-time event delivery with retry policies
- **Developer Tools**: Interactive playground, CLI, and SDKs

## Project Structure

```
ZappierTriggersAPI/
├── backend/
│   └── app/
│       ├── api/v1/          # API route handlers
│       ├── core/            # Config, auth, middleware
│       ├── models/          # Database models
│       ├── schemas/         # Pydantic schemas
│       ├── services/        # Business logic
│       └── workers/         # Background workers
├── frontend/                # Dashboard UI (future)
├── shared/                  # Shared types/utilities
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── docs/
│   ├── PRD.md              # Product Requirements Document
│   └── ADDITIONAL_FEATURES.md
└── scripts/                 # Deployment/utility scripts
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/events` | Create single event |
| POST | `/api/v1/events/batch` | Create multiple events |
| GET | `/api/v1/events/{id}` | Get event by ID |
| GET | `/api/v1/inbox` | List pending events |
| DELETE | `/api/v1/inbox/{id}` | Acknowledge event |
| GET | `/api/v1/health` | Health check |

## Documentation

- [Product Requirements Document](docs/PRD.md) - Full specification
- [Additional Features](docs/ADDITIONAL_FEATURES.md) - Innovation roadmap
- [API Reference](docs/API.md) - OpenAPI specification (TODO)

## Tech Stack

- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Queue**: Amazon SQS / Redis
- **Cache**: Redis
- **Deployment**: AWS ECS / Docker

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend/app --cov-report=html

# Lint
ruff check .
black --check .
mypy backend/

# Load test
locust -f tests/load/locustfile.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `AWS_REGION` | AWS region for SQS | us-east-1 |
| `API_KEY_SECRET` | Secret for API key hashing | - |
| `LOG_LEVEL` | Logging level | INFO |

## License

Proprietary - Zapier Inc.
