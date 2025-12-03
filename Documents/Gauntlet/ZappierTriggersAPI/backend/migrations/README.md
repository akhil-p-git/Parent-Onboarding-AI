# Database Migrations

This directory contains Alembic migrations for the Zapier Triggers API database schema.

## Structure

```
migrations/
├── env.py              # Alembic environment configuration
├── script.py.mako      # Template for new migrations
├── README.md           # This file
└── versions/           # Migration files
    └── 001_initial_schema.py
```

## Commands

### Create a New Migration

Auto-generate migration from model changes:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

Create an empty migration:
```bash
cd backend
alembic revision -m "description of changes"
```

### Run Migrations

Apply all pending migrations:
```bash
alembic upgrade head
```

Apply up to a specific revision:
```bash
alembic upgrade <revision>
```

### Rollback Migrations

Rollback the last migration:
```bash
alembic downgrade -1
```

Rollback to a specific revision:
```bash
alembic downgrade <revision>
```

Rollback all migrations:
```bash
alembic downgrade base
```

### View Migration Status

Show current revision:
```bash
alembic current
```

Show migration history:
```bash
alembic history
```

Show pending migrations:
```bash
alembic heads
```

## Using Make Commands

From the project root:
```bash
make db-migrate       # Run all pending migrations
make db-rollback      # Rollback last migration
make db-revision m="message"  # Create new migration
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic may not detect all changes correctly
2. **Test migrations both ways** - Ensure both `upgrade()` and `downgrade()` work
3. **Keep migrations small** - One logical change per migration
4. **Never edit migrations after they're deployed** - Create new migrations instead
5. **Use descriptive names** - Migration filenames should describe the change

## Initial Schema

The initial migration (`001_initial_schema.py`) creates:

- `api_keys` - API key authentication and authorization
- `events` - Inbound webhook events
- `subscriptions` - Webhook delivery configurations
- `event_deliveries` - Delivery tracking and audit trail

All tables include:
- ULID-based primary keys with prefixes
- Timestamps (created_at, updated_at)
- JSONB columns for flexible metadata
- Appropriate indexes for query performance
