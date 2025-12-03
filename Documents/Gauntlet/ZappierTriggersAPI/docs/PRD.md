# Zapier Triggers API - Product Requirements Document

**Organization:** Zapier
**Project ID:** K1oUUDeoZrvJkVZafqHL_1761943818847
**Version:** 1.0
**Last Updated:** November 29, 2024
**Author:** Akhil P
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [Target Users & Personas](#4-target-users--personas)
5. [User Stories & Use Cases](#5-user-stories--use-cases)
6. [Functional Requirements](#6-functional-requirements)
7. [API Specification](#7-api-specification)
8. [Data Models & Schemas](#8-data-models--schemas)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [System Architecture](#10-system-architecture)
11. [Security Requirements](#11-security-requirements)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Strategy](#13-deployment-strategy)
14. [Observability & Monitoring](#14-observability--monitoring)
15. [Risk Assessment & Mitigation](#15-risk-assessment--mitigation)
16. [Dependencies & Assumptions](#16-dependencies--assumptions)
17. [Out of Scope](#17-out-of-scope)
18. [Future Roadmap](#18-future-roadmap)
19. [Appendix](#19-appendix)

---

## 1. Executive Summary

### 1.1 Vision

The Zapier Triggers API is a next-generation, unified event ingestion system designed to enable real-time, event-driven automation on the Zapier platform. This RESTful API provides a standardized, reliable, and developer-friendly interface for any external system to send events into Zapier, powering agentic workflows that react to events in real time.

### 1.2 Background

Traditional Zapier triggers are tightly coupled to individual integrations, requiring polling mechanisms or platform-specific implementations. This architecture has served well but faces limitations:

- **Latency**: Polling-based triggers introduce delays between event occurrence and workflow execution
- **Scalability**: Each integration maintains its own trigger logic, leading to duplicated patterns
- **Flexibility**: Developers cannot easily send custom events without building full integrations
- **Real-time Gaps**: No unified mechanism exists for instant event delivery

### 1.3 Proposed Solution

The Triggers API introduces a centralized event ingestion layer that:

- Accepts events from any authenticated source via a simple REST interface
- Stores events durably with guaranteed delivery semantics
- Provides an inbox model for event consumption with acknowledgment workflows
- Enables real-time webhook delivery to subscribed endpoints
- Supports event filtering, transformation, and routing

### 1.4 Business Value

- **Developer Velocity**: Reduce integration time from weeks to hours
- **Platform Stickiness**: Become the universal event bus for automation
- **New Revenue Streams**: Premium tiers for high-volume event processing
- **Competitive Advantage**: First-class support for agentic AI workflows

---

## 2. Problem Statement

### 2.1 Current Challenges

| Challenge | Impact | Affected Users |
|-----------|--------|----------------|
| Polling-based triggers | 5-15 minute delays | All users |
| Integration-specific logic | High maintenance burden | Platform engineers |
| No custom event support | Limited flexibility | Developers |
| Inconsistent reliability | Missed events | Business users |
| No event replay capability | Data loss on failures | Operations teams |

### 2.2 Market Context

The automation market is rapidly evolving toward:
- **Event-driven architectures** (EDA) as the standard for microservices
- **Agentic AI systems** that require real-time event streams
- **Low-latency expectations** from modern SaaS applications

### 2.3 Opportunity

By providing a unified Triggers API, Zapier can:
- Capture the growing demand for real-time automation
- Position as the central nervous system for business events
- Enable new categories of AI-powered workflows

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

| Goal | Description | Timeline |
|------|-------------|----------|
| G1 | Launch MVP with core event ingestion and inbox retrieval | Phase 1 |
| G2 | Achieve production-grade reliability (99.9% uptime) | Phase 2 |
| G3 | Enable real-time webhook delivery | Phase 2 |
| G4 | Onboard 10+ internal integrations | Phase 3 |

### 3.2 Success Metrics

#### Technical Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Event Ingestion Latency | < 100ms p99 | APM instrumentation |
| API Availability | 99.9% uptime | Health check monitoring |
| Event Delivery Success Rate | 99.99% | Delivery confirmation tracking |
| Throughput Capacity | 10,000 events/sec | Load testing |
| Error Rate | < 0.1% | Error logging analysis |

#### Business Metrics

| Metric | Target | Timeline |
|--------|--------|----------|
| Developer Adoption | 100+ active API keys | 3 months post-launch |
| Integration Migrations | 10% of existing triggers | 6 months post-launch |
| Developer NPS | > 50 | Quarterly surveys |
| Time to First Event | < 5 minutes | Onboarding funnel analysis |

### 3.3 Key Results (OKRs)

**Objective 1: Build a reliable event ingestion system**
- KR1: Achieve 99.9% uptime in production
- KR2: Process 1M events/day with < 100ms latency
- KR3: Zero data loss incidents

**Objective 2: Deliver exceptional developer experience**
- KR1: < 5 minutes to send first event
- KR2: 90% of developers succeed without support
- KR3: API documentation rated 4.5+/5

---

## 4. Target Users & Personas

### 4.1 Primary Personas

#### Persona 1: Platform Developer (Alex)

| Attribute | Details |
|-----------|---------|
| Role | Senior Software Engineer at a SaaS company |
| Goals | Integrate product events with Zapier for customer workflows |
| Pain Points | Current integration process is complex and time-consuming |
| Technical Level | Expert; comfortable with REST APIs, webhooks, auth flows |
| Success Criteria | Send events reliably with minimal code changes |

**User Journey:**
1. Discovers Triggers API in documentation
2. Creates API key in Zapier dashboard
3. Sends test event from local environment
4. Integrates into production application
5. Monitors event delivery in dashboard

#### Persona 2: Automation Specialist (Jordan)

| Attribute | Details |
|-----------|---------|
| Role | RevOps Manager building internal automation |
| Goals | Create workflows that react to custom business events |
| Pain Points | Limited trigger options force manual intervention |
| Technical Level | Intermediate; can write scripts and use APIs |
| Success Criteria | Build end-to-end automated workflows without engineering help |

**User Journey:**
1. Identifies business process needing automation
2. Uses low-code tool to send events to Triggers API
3. Creates Zap triggered by incoming events
4. Tests workflow with sample data
5. Deploys and monitors in production

#### Persona 3: Integration Partner (Sam)

| Attribute | Details |
|-----------|---------|
| Role | Partner Engineer at integration partner company |
| Goals | Build Zapier integration for their platform |
| Pain Points | Current trigger development is overly complex |
| Technical Level | Expert; deep API and integration experience |
| Success Criteria | Reduce trigger implementation time by 75% |

### 4.2 Secondary Personas

- **Business Analyst**: Needs real-time event data for reporting
- **DevOps Engineer**: Manages API deployment and monitoring
- **Security Team**: Reviews API security and compliance

---

## 5. User Stories & Use Cases

### 5.1 Epic: Event Ingestion

#### US-001: Send Simple Event
**As a** developer
**I want to** send a JSON event to Zapier via HTTP POST
**So that** I can trigger workflows from my application

**Acceptance Criteria:**
- [ ] POST to `/events` with JSON payload succeeds
- [ ] Response includes unique event ID and timestamp
- [ ] Event is persisted durably
- [ ] Response time < 100ms for 99th percentile
- [ ] Invalid JSON returns 400 with clear error message

**Technical Notes:**
- Validate JSON schema on ingestion
- Generate UUIDv7 for event ID (time-ordered)
- Store in append-only event log

---

#### US-002: Send Batch Events
**As a** developer
**I want to** send multiple events in a single request
**So that** I can reduce API calls and improve efficiency

**Acceptance Criteria:**
- [ ] POST to `/events/batch` with array of events
- [ ] Maximum 100 events per batch
- [ ] Returns array of results (success/failure per event)
- [ ] Partial failures are handled gracefully
- [ ] Total payload size limit: 1MB

---

#### US-003: Event Validation
**As a** developer
**I want** my events to be validated against a schema
**So that** I catch errors before they affect workflows

**Acceptance Criteria:**
- [ ] Optional schema ID in event metadata
- [ ] Validation against registered schema
- [ ] Clear error messages for validation failures
- [ ] Schema registry endpoint for CRUD operations

---

### 5.2 Epic: Event Retrieval

#### US-004: List Pending Events
**As an** automation system
**I want to** retrieve undelivered events from my inbox
**So that** I can process them in my workflow

**Acceptance Criteria:**
- [ ] GET `/inbox` returns paginated event list
- [ ] Events ordered by timestamp (oldest first)
- [ ] Supports limit and cursor parameters
- [ ] Includes event metadata and payload
- [ ] Filters by event type supported

---

#### US-005: Acknowledge Event Delivery
**As an** automation system
**I want to** acknowledge that I've processed an event
**So that** it's removed from my pending queue

**Acceptance Criteria:**
- [ ] DELETE `/inbox/{event_id}` marks event as delivered
- [ ] Batch acknowledgment supported
- [ ] Acknowledged events excluded from inbox queries
- [ ] Audit log of acknowledgments maintained

---

#### US-006: Peek at Events
**As a** developer
**I want to** peek at events without acknowledging them
**So that** I can debug and test my integration

**Acceptance Criteria:**
- [ ] GET `/inbox/{event_id}` returns single event
- [ ] Does not change event status
- [ ] Includes full event details and metadata

---

### 5.3 Epic: Real-time Delivery

#### US-007: Webhook Subscriptions
**As an** automation system
**I want to** receive events via webhook
**So that** I can react to events in real-time

**Acceptance Criteria:**
- [ ] POST `/subscriptions` creates webhook endpoint
- [ ] Supports URL, headers, and filtering rules
- [ ] Webhook signature for verification
- [ ] Configurable retry policy

---

#### US-008: Webhook Delivery with Retries
**As an** automation system
**I want** failed webhook deliveries to be retried
**So that** I don't miss events due to temporary failures

**Acceptance Criteria:**
- [ ] Exponential backoff retry (1s, 2s, 4s, 8s, 16s)
- [ ] Maximum 5 retry attempts
- [ ] Dead letter queue for failed events
- [ ] Webhook delivery status in dashboard

---

### 5.4 Epic: Developer Experience

#### US-009: API Key Management
**As a** developer
**I want to** create and manage API keys
**So that** I can authenticate my applications

**Acceptance Criteria:**
- [ ] Generate API keys from dashboard
- [ ] Support for multiple keys per account
- [ ] Key rotation without downtime
- [ ] Scoped permissions per key
- [ ] Usage tracking per key

---

#### US-010: Event Explorer
**As a** developer
**I want to** view recent events in a dashboard
**So that** I can debug my integration

**Acceptance Criteria:**
- [ ] Real-time event stream view
- [ ] Search and filter capabilities
- [ ] Event detail inspection
- [ ] Replay failed events

---

### 5.5 Use Case Scenarios

#### Scenario 1: E-commerce Order Processing

```
Actor: E-commerce Platform
Trigger: Customer places order
Flow:
1. E-commerce backend POSTs order.created event
2. Triggers API stores event and delivers to Zapier
3. Zap triggers with order data
4. Actions: Update CRM, send email, notify Slack
Result: Order processed in < 1 second
```

#### Scenario 2: CI/CD Pipeline Notifications

```
Actor: GitHub Actions
Trigger: Deployment completes
Flow:
1. GitHub Action POSTs deployment.completed event
2. Event includes commit SHA, environment, status
3. Zap triggers and routes based on status
4. Actions: Notify team, update status page
Result: Team notified within seconds of deployment
```

#### Scenario 3: IoT Sensor Alerting

```
Actor: IoT Gateway
Trigger: Sensor reading exceeds threshold
Flow:
1. Gateway POSTs sensor.alert event with batch API
2. Events processed in order
3. Zaps trigger for each alert
4. Actions: Page on-call, log to database
Result: Alerts processed in real-time
```

---

## 6. Functional Requirements

### 6.1 Priority Definitions

| Priority | Definition | Commitment |
|----------|------------|------------|
| P0 | Critical for launch | Must ship |
| P1 | High value, needed soon | Target for v1.1 |
| P2 | Nice to have | Future consideration |

### 6.2 P0 Requirements (Must-Have for MVP)

#### FR-001: Event Ingestion Endpoint

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `POST /api/v1/events` |
| Auth | API Key (Bearer token) |
| Rate Limit | 1000 req/min per key |
| Payload | JSON, max 256KB |
| Response | 201 Created with event ID |

**Request Schema:**
```json
{
  "type": "string (required, max 256 chars)",
  "source": "string (required, max 256 chars)",
  "data": "object (required, max 256KB)",
  "metadata": {
    "idempotency_key": "string (optional)",
    "correlation_id": "string (optional)",
    "schema_id": "string (optional)"
  }
}
```

**Response Schema:**
```json
{
  "id": "evt_01HX7Q8Y2Z3K4M5N6P7R8S9T0V",
  "type": "order.created",
  "source": "ecommerce-api",
  "created_at": "2024-11-29T12:00:00.000Z",
  "status": "pending",
  "links": {
    "self": "/api/v1/events/evt_01HX7Q8Y2Z3K4M5N6P7R8S9T0V"
  }
}
```

---

#### FR-002: Batch Event Ingestion

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `POST /api/v1/events/batch` |
| Max Events | 100 per request |
| Max Payload | 1MB total |
| Response | Array of results |

**Request Schema:**
```json
{
  "events": [
    {
      "type": "order.created",
      "source": "ecommerce-api",
      "data": { "order_id": "12345" }
    }
  ]
}
```

**Response Schema:**
```json
{
  "results": [
    {
      "index": 0,
      "success": true,
      "id": "evt_01HX7Q8Y2Z3K4M5N6P7R8S9T0V"
    },
    {
      "index": 1,
      "success": false,
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid event type format"
      }
    }
  ],
  "summary": {
    "total": 2,
    "succeeded": 1,
    "failed": 1
  }
}
```

---

#### FR-003: Event Inbox Retrieval

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `GET /api/v1/inbox` |
| Pagination | Cursor-based, max 100 per page |
| Ordering | Oldest first (FIFO) |
| Filters | type, source, created_after, created_before |

**Response Schema:**
```json
{
  "events": [
    {
      "id": "evt_01HX7Q8Y2Z3K4M5N6P7R8S9T0V",
      "type": "order.created",
      "source": "ecommerce-api",
      "data": { "order_id": "12345" },
      "created_at": "2024-11-29T12:00:00.000Z",
      "attempts": 0
    }
  ],
  "pagination": {
    "cursor": "eyJpZCI6ImV2dF8wMUhYN...",
    "has_more": true,
    "limit": 100
  }
}
```

---

#### FR-004: Event Acknowledgment

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `DELETE /api/v1/inbox/{event_id}` |
| Effect | Marks event as delivered |
| Idempotent | Yes |

**Alternative: Batch Acknowledgment**
```
POST /api/v1/inbox/ack
{
  "event_ids": ["evt_01...", "evt_02..."]
}
```

---

#### FR-005: Get Single Event

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `GET /api/v1/events/{event_id}` |
| Response | Full event details |
| History | Includes delivery attempts |

---

#### FR-006: Authentication & Authorization

| Mechanism | Specification |
|-----------|---------------|
| Auth Type | Bearer Token (API Key) |
| Header | `Authorization: Bearer sk_live_...` |
| Key Format | `sk_live_` + 32 random chars (production) |
| | `sk_test_` + 32 random chars (sandbox) |
| Scopes | events:write, events:read, inbox:read, inbox:write |

---

#### FR-007: Health Check Endpoint

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `GET /api/v1/health` |
| Auth | None required |
| Response | Service status and version |

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-11-29T12:00:00.000Z",
  "components": {
    "database": "healthy",
    "queue": "healthy"
  }
}
```

---

### 6.3 P1 Requirements (Should-Have)

#### FR-008: Webhook Subscriptions

Create and manage webhook endpoints for real-time event delivery.

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `POST /api/v1/subscriptions` |
| Delivery | Async with retry |
| Signature | HMAC-SHA256 |

---

#### FR-009: Event Replay

Replay events for debugging or recovery.

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `POST /api/v1/events/{event_id}/replay` |
| Effect | Re-queues event for delivery |
| Limit | 3 replays per event |

---

#### FR-010: Event Type Registry

Register and validate event schemas.

| Attribute | Specification |
|-----------|---------------|
| Endpoint | `POST /api/v1/event-types` |
| Schema | JSON Schema draft-07 |
| Validation | Optional, configurable |

---

### 6.4 P2 Requirements (Nice-to-Have)

#### FR-011: Event Filtering Rules
Configure server-side filters to route events to specific subscriptions.

#### FR-012: Event Transformation
Apply JSONPath or JMESPath transformations before delivery.

#### FR-013: Event Archival
Long-term storage for compliance and analytics.

#### FR-014: GraphQL API
Alternative query interface for complex event queries.

---

## 7. API Specification

### 7.1 Base URL

| Environment | URL |
|-------------|-----|
| Production | `https://api.zapier.com/triggers/v1` |
| Sandbox | `https://sandbox.api.zapier.com/triggers/v1` |
| Local Dev | `http://localhost:8000/api/v1` |

### 7.2 Authentication

All API requests must include an API key in the Authorization header:

```http
Authorization: Bearer sk_live_abc123def456...
```

### 7.3 Rate Limiting

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Free | 100 | 20 |
| Professional | 1,000 | 100 |
| Enterprise | 10,000 | 1,000 |

Rate limit headers returned:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1701259200
```

### 7.4 Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.zapier.com/problems/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The 'type' field is required",
  "instance": "/api/v1/events",
  "errors": [
    {
      "field": "type",
      "code": "required",
      "message": "This field is required"
    }
  ],
  "request_id": "req_01HX7Q8Y..."
}
```

### 7.5 Standard Error Codes

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | validation_error | Invalid request body |
| 401 | authentication_error | Missing or invalid API key |
| 403 | authorization_error | Insufficient permissions |
| 404 | not_found | Resource does not exist |
| 409 | conflict | Duplicate idempotency key |
| 422 | unprocessable_entity | Semantically invalid |
| 429 | rate_limit_exceeded | Too many requests |
| 500 | internal_error | Server error |
| 503 | service_unavailable | Temporary outage |

### 7.6 Complete Endpoint Reference

```yaml
openapi: 3.0.3
info:
  title: Zapier Triggers API
  version: 1.0.0

paths:
  /events:
    post:
      summary: Create event
      operationId: createEvent
      tags: [Events]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateEventRequest'
      responses:
        '201':
          description: Event created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Event'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/AuthenticationError'
        '429':
          $ref: '#/components/responses/RateLimitError'

  /events/batch:
    post:
      summary: Create multiple events
      operationId: createEventBatch
      tags: [Events]

  /events/{eventId}:
    get:
      summary: Get event by ID
      operationId: getEvent
      tags: [Events]

  /inbox:
    get:
      summary: List pending events
      operationId: listInbox
      tags: [Inbox]

  /inbox/{eventId}:
    delete:
      summary: Acknowledge event
      operationId: acknowledgeEvent
      tags: [Inbox]

  /inbox/ack:
    post:
      summary: Batch acknowledge events
      operationId: batchAcknowledge
      tags: [Inbox]

  /subscriptions:
    get:
      summary: List subscriptions
      operationId: listSubscriptions
      tags: [Subscriptions]
    post:
      summary: Create subscription
      operationId: createSubscription
      tags: [Subscriptions]

  /subscriptions/{subscriptionId}:
    get:
      summary: Get subscription
      operationId: getSubscription
      tags: [Subscriptions]
    patch:
      summary: Update subscription
      operationId: updateSubscription
      tags: [Subscriptions]
    delete:
      summary: Delete subscription
      operationId: deleteSubscription
      tags: [Subscriptions]

  /health:
    get:
      summary: Health check
      operationId: healthCheck
      tags: [System]
      security: []
```

---

## 8. Data Models & Schemas

### 8.1 Core Entities

#### Event

```typescript
interface Event {
  // Unique identifier (UUIDv7 for time-ordering)
  id: string;  // "evt_01HX7Q8Y2Z3K4M5N6P7R8S9T0V"

  // Event classification
  type: string;           // "order.created"
  source: string;         // "ecommerce-api"

  // Payload
  data: Record<string, unknown>;

  // Metadata
  metadata: {
    idempotency_key?: string;
    correlation_id?: string;
    schema_id?: string;
    user_agent?: string;
    ip_address?: string;
  };

  // Timestamps
  created_at: string;     // ISO 8601
  received_at: string;    // ISO 8601

  // Delivery tracking
  status: 'pending' | 'delivered' | 'failed' | 'expired';
  delivery_attempts: number;
  last_attempt_at?: string;
  delivered_at?: string;

  // Relations
  account_id: string;
  api_key_id: string;
}
```

#### Subscription

```typescript
interface Subscription {
  id: string;             // "sub_01HX7Q8Y..."

  // Webhook configuration
  url: string;            // "https://example.com/webhook"
  headers?: Record<string, string>;

  // Filtering
  filter?: {
    types?: string[];     // ["order.*", "payment.completed"]
    sources?: string[];
  };

  // Retry configuration
  retry_policy: {
    max_attempts: number; // 5
    initial_delay_ms: number; // 1000
    max_delay_ms: number; // 60000
    multiplier: number;   // 2
  };

  // Security
  signing_secret: string;

  // Status
  status: 'active' | 'paused' | 'disabled';

  // Metadata
  created_at: string;
  updated_at: string;
  account_id: string;
}
```

#### API Key

```typescript
interface ApiKey {
  id: string;             // "key_01HX7Q8Y..."

  // Key value (only returned on creation)
  key?: string;           // "sk_live_abc123..."
  key_prefix: string;     // "sk_live_abc1"

  // Configuration
  name: string;
  scopes: string[];       // ["events:write", "inbox:read"]

  // Environment
  environment: 'live' | 'test';

  // Usage tracking
  last_used_at?: string;
  request_count: number;

  // Status
  status: 'active' | 'revoked';
  expires_at?: string;

  // Metadata
  created_at: string;
  account_id: string;
}
```

### 8.2 Database Schema

```sql
-- Events table (append-only)
CREATE TABLE events (
    id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    api_key_id VARCHAR(32) NOT NULL,
    type VARCHAR(256) NOT NULL,
    source VARCHAR(256) NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    delivery_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    received_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    last_attempt_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    -- Indexes
    INDEX idx_events_account_status (account_id, status),
    INDEX idx_events_type (type),
    INDEX idx_events_created (created_at),
    INDEX idx_events_source (source)
);

-- Event delivery log
CREATE TABLE event_deliveries (
    id VARCHAR(32) PRIMARY KEY,
    event_id VARCHAR(32) NOT NULL REFERENCES events(id),
    subscription_id VARCHAR(32) REFERENCES subscriptions(id),
    status VARCHAR(20) NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    latency_ms INTEGER,
    attempted_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_deliveries_event (event_id)
);

-- Subscriptions
CREATE TABLE subscriptions (
    id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    headers JSONB DEFAULT '{}',
    filter JSONB DEFAULT '{}',
    retry_policy JSONB NOT NULL,
    signing_secret VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_subs_account (account_id, status)
);

-- API Keys
CREATE TABLE api_keys (
    id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    name VARCHAR(256),
    scopes TEXT[] DEFAULT ARRAY['events:write'],
    environment VARCHAR(10) DEFAULT 'live',
    status VARCHAR(20) DEFAULT 'active',
    last_used_at TIMESTAMPTZ,
    request_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    INDEX idx_keys_account (account_id, status),
    INDEX idx_keys_hash (key_hash)
);

-- Idempotency tracking
CREATE TABLE idempotency_keys (
    key VARCHAR(256) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    event_id VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
```

### 8.3 JSON Schemas

#### Event Creation Request

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CreateEventRequest",
  "type": "object",
  "required": ["type", "source", "data"],
  "properties": {
    "type": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "pattern": "^[a-zA-Z][a-zA-Z0-9._-]*$",
      "description": "Event type using dot notation (e.g., order.created)"
    },
    "source": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "Identifier for the event source system"
    },
    "data": {
      "type": "object",
      "description": "Event payload data"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "idempotency_key": {
          "type": "string",
          "maxLength": 256,
          "description": "Client-provided key for deduplication"
        },
        "correlation_id": {
          "type": "string",
          "maxLength": 256,
          "description": "ID to correlate related events"
        },
        "schema_id": {
          "type": "string",
          "description": "ID of schema to validate against"
        }
      }
    }
  }
}
```

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Requirement | Measurement |
|--------|-------------|-------------|
| Event Ingestion Latency | p50 < 50ms, p99 < 100ms | APM tracing |
| Inbox Query Latency | p50 < 100ms, p99 < 500ms | APM tracing |
| Webhook Delivery Latency | p50 < 200ms (network excluded) | Delivery logs |
| Throughput | 10,000 events/sec sustained | Load testing |
| Concurrent Connections | 10,000 simultaneous | Load testing |

### 9.2 Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% (8.76 hours downtime/year) |
| RTO (Recovery Time Objective) | < 5 minutes |
| RPO (Recovery Point Objective) | < 1 minute |
| Planned Maintenance Windows | < 4 hours/month |

### 9.3 Scalability

| Dimension | Requirement |
|-----------|-------------|
| Horizontal Scaling | Auto-scale 2-20 instances |
| Database | Read replicas for query scaling |
| Queue | Partitioned for parallel processing |
| Storage | Automatic sharding by account |

### 9.4 Reliability

| Requirement | Implementation |
|-------------|----------------|
| No data loss | Write-ahead logging, synchronous replication |
| Exactly-once delivery | Idempotency keys, delivery tracking |
| Graceful degradation | Circuit breakers, bulkheads |
| Disaster recovery | Multi-AZ deployment, cross-region backup |

### 9.5 Maintainability

| Aspect | Requirement |
|--------|-------------|
| Code Coverage | > 80% unit test coverage |
| Documentation | 100% of public APIs documented |
| Deployment | Zero-downtime deployments |
| Rollback | < 5 minutes to roll back |

---

## 10. System Architecture

### 10.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Web Apps │  │ Mobile   │  │ IoT      │  │ SaaS     │  │ Scripts  │      │
│  │          │  │ Apps     │  │ Devices  │  │ Platforms│  │          │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │             │
        └─────────────┴─────────────┴─────────────┴─────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDGE LAYER                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    AWS CloudFront / API Gateway                       │  │
│  │  • SSL Termination  • Rate Limiting  • DDoS Protection  • Caching    │  │
│  └────────────────────────────────┬─────────────────────────────────────┘  │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                     │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   API Service   │  │   API Service   │  │   API Service   │   (ECS/K8s) │
│  │   (FastAPI)     │  │   (FastAPI)     │  │   (FastAPI)     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                        │
│           └────────────────────┴────────────────────┘                        │
│                                │                                             │
│  ┌─────────────────────────────┴─────────────────────────────┐              │
│  │                    Internal Services                       │              │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │              │
│  │  │ Auth        │  │ Validation  │  │ Routing     │        │              │
│  │  │ Service     │  │ Service     │  │ Service     │        │              │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │              │
│  └───────────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MESSAGE LAYER                                        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Amazon SQS                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │ Events Queue │  │ Delivery     │  │ Dead Letter  │                │  │
│  │  │              │  │ Queue        │  │ Queue        │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Worker Services (ECS)                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │ Event Processor │  │ Webhook         │  │ Cleanup         │       │  │
│  │  │ Worker          │  │ Delivery Worker │  │ Worker          │       │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                          │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │  Amazon RDS        │  │  Amazon            │  │  Amazon S3         │    │
│  │  (PostgreSQL)      │  │  ElastiCache       │  │  (Event Archive)   │    │
│  │                    │  │  (Redis)           │  │                    │    │
│  │  • Events          │  │  • API Key Cache   │  │  • Historical      │    │
│  │  • Subscriptions   │  │  • Rate Limiting   │  │    Events          │    │
│  │  • Deliveries      │  │  • Session Data    │  │  • Compliance      │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Component Details

#### API Service (FastAPI)

**Responsibilities:**
- HTTP request handling
- Request validation
- Authentication/authorization
- Rate limiting enforcement
- Event ingestion
- Inbox queries

**Technology Stack:**
- Python 3.11+
- FastAPI (ASGI framework)
- Pydantic (validation)
- SQLAlchemy (ORM)
- uvicorn (ASGI server)

#### Event Processor Worker

**Responsibilities:**
- Process incoming events from queue
- Apply routing rules
- Trigger webhook deliveries
- Update event status

#### Webhook Delivery Worker

**Responsibilities:**
- Execute HTTP requests to subscriber endpoints
- Handle retry logic with exponential backoff
- Record delivery attempts
- Move failed events to DLQ

### 10.3 Data Flow

```
Event Ingestion Flow:
━━━━━━━━━━━━━━━━━━━━

1. Client POST → API Gateway (rate limit, auth)
2. API Gateway → API Service (validate, persist)
3. API Service → PostgreSQL (write event)
4. API Service → SQS Events Queue (enqueue)
5. API Service → Client (201 response)

Event Delivery Flow:
━━━━━━━━━━━━━━━━━━━

1. Event Processor ← SQS Events Queue (poll)
2. Event Processor → PostgreSQL (load subscriptions)
3. Event Processor → SQS Delivery Queue (enqueue deliveries)
4. Webhook Worker ← SQS Delivery Queue (poll)
5. Webhook Worker → Subscriber Endpoint (HTTP POST)
6. Webhook Worker → PostgreSQL (record result)
7. If failed: Webhook Worker → SQS Delivery Queue (retry with delay)
8. If max retries: Webhook Worker → DLQ (dead letter)
```

### 10.4 Infrastructure as Code

```hcl
# terraform/main.tf (excerpt)

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "triggers-api-vpc"
  cidr   = "10.0.0.0/16"
  azs    = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

module "ecs_cluster" {
  source = "terraform-aws-modules/ecs/aws"
  name   = "triggers-api-cluster"
}

module "rds" {
  source            = "terraform-aws-modules/rds/aws"
  identifier        = "triggers-api-db"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r6g.large"
  allocated_storage = 100
  multi_az          = true
}

module "elasticache" {
  source          = "terraform-aws-modules/elasticache/aws"
  cluster_id      = "triggers-api-cache"
  engine          = "redis"
  node_type       = "cache.r6g.large"
  num_cache_nodes = 2
}

module "sqs" {
  source = "terraform-aws-modules/sqs/aws"
  name   = "triggers-events-queue"

  redrive_policy = jsonencode({
    deadLetterTargetArn = module.dlq.arn
    maxReceiveCount     = 5
  })
}
```

---

## 11. Security Requirements

### 11.1 Authentication

| Mechanism | Description |
|-----------|-------------|
| API Keys | Primary auth for API access |
| Key Hashing | SHA-256 hashing in storage |
| Key Rotation | Zero-downtime rotation support |
| Scope Enforcement | Fine-grained permission scopes |

### 11.2 Authorization

```yaml
Scopes:
  events:write:
    description: Create events
    endpoints: [POST /events, POST /events/batch]

  events:read:
    description: Read event details
    endpoints: [GET /events/{id}]

  inbox:read:
    description: List pending events
    endpoints: [GET /inbox]

  inbox:write:
    description: Acknowledge events
    endpoints: [DELETE /inbox/{id}, POST /inbox/ack]

  subscriptions:read:
    description: List subscriptions
    endpoints: [GET /subscriptions]

  subscriptions:write:
    description: Manage subscriptions
    endpoints: [POST /subscriptions, PATCH /subscriptions/{id}, DELETE /subscriptions/{id}]
```

### 11.3 Data Protection

| Layer | Protection |
|-------|------------|
| In Transit | TLS 1.3 required |
| At Rest | AES-256 encryption (RDS, S3) |
| PII Handling | Field-level encryption for sensitive data |
| Key Management | AWS KMS for encryption keys |

### 11.4 Webhook Security

| Mechanism | Implementation |
|-----------|----------------|
| Request Signing | HMAC-SHA256 signature in header |
| Timestamp Validation | Reject requests > 5 minutes old |
| IP Whitelisting | Optional subscriber IP restrictions |

**Signature Verification (Subscriber Implementation):**

```python
import hmac
import hashlib
import time

def verify_webhook(payload: bytes, signature: str, timestamp: str, secret: str) -> bool:
    # Check timestamp freshness
    if abs(time.time() - int(timestamp)) > 300:  # 5 minutes
        return False

    # Compute expected signature
    signed_payload = f"{timestamp}.{payload.decode()}"
    expected = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

### 11.5 Security Compliance

| Standard | Status |
|----------|--------|
| SOC 2 Type II | Required |
| GDPR | Required (EU customers) |
| CCPA | Required (CA customers) |
| HIPAA | Future consideration |

---

## 12. Testing Strategy

### 12.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  5%
                    │  Tests  │
                   ─┴─────────┴─
                  ┌─────────────┐
                  │ Integration │  25%
                  │   Tests     │
                 ─┴─────────────┴─
                ┌─────────────────┐
                │    Unit Tests   │  70%
                │                 │
               ─┴─────────────────┴─
```

### 12.2 Unit Tests

**Coverage Target:** 80%+

**Frameworks:**
- pytest (Python)
- pytest-asyncio (async tests)
- pytest-cov (coverage)

**Example Test:**

```python
# tests/unit/test_event_service.py

import pytest
from app.services.event_service import EventService
from app.schemas.event import CreateEventRequest

class TestEventService:
    @pytest.fixture
    def service(self, mock_db, mock_queue):
        return EventService(db=mock_db, queue=mock_queue)

    async def test_create_event_success(self, service):
        request = CreateEventRequest(
            type="order.created",
            source="test-api",
            data={"order_id": "12345"}
        )

        event = await service.create_event(request, account_id="acc_123")

        assert event.id.startswith("evt_")
        assert event.type == "order.created"
        assert event.status == "pending"

    async def test_create_event_idempotency(self, service):
        request = CreateEventRequest(
            type="order.created",
            source="test-api",
            data={"order_id": "12345"},
            metadata={"idempotency_key": "unique-key-123"}
        )

        event1 = await service.create_event(request, account_id="acc_123")
        event2 = await service.create_event(request, account_id="acc_123")

        assert event1.id == event2.id  # Same event returned
```

### 12.3 Integration Tests

**Scope:** Database, queue, cache interactions

```python
# tests/integration/test_event_flow.py

import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestEventFlow:
    async def test_create_and_retrieve_event(self, client: AsyncClient, auth_headers):
        # Create event
        response = await client.post(
            "/api/v1/events",
            json={
                "type": "test.event",
                "source": "integration-test",
                "data": {"key": "value"}
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        event_id = response.json()["id"]

        # Retrieve from inbox
        response = await client.get(
            "/api/v1/inbox",
            headers=auth_headers
        )
        assert response.status_code == 200
        events = response.json()["events"]
        assert any(e["id"] == event_id for e in events)

        # Acknowledge
        response = await client.delete(
            f"/api/v1/inbox/{event_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
```

### 12.4 Load Tests

**Tool:** Locust

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between

class EventAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.headers = {"Authorization": f"Bearer {self.environment.api_key}"}

    @task(10)
    def create_event(self):
        self.client.post(
            "/api/v1/events",
            json={
                "type": "load.test",
                "source": "locust",
                "data": {"timestamp": time.time()}
            },
            headers=self.headers
        )

    @task(5)
    def list_inbox(self):
        self.client.get("/api/v1/inbox", headers=self.headers)

    @task(1)
    def batch_create(self):
        self.client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {"type": "batch.test", "source": "locust", "data": {"i": i}}
                    for i in range(50)
                ]
            },
            headers=self.headers
        )
```

**Load Test Scenarios:**

| Scenario | Target | Duration |
|----------|--------|----------|
| Baseline | 100 req/s | 10 min |
| Peak Load | 1000 req/s | 5 min |
| Stress Test | 5000 req/s | 2 min |
| Soak Test | 500 req/s | 4 hours |

### 12.5 Contract Tests

Ensure API compatibility with consumers using Pact or similar.

---

## 13. Deployment Strategy

### 13.1 Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development | http://localhost:8000 |
| Dev | Feature testing | https://dev-triggers.zapier.internal |
| Staging | Pre-production | https://staging-triggers.zapier.internal |
| Production | Live traffic | https://api.zapier.com/triggers |

### 13.2 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff black mypy
      - run: ruff check .
      - run: black --check .
      - run: mypy app/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r app/
      - run: safety check

  build:
    needs: [test, lint, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ env.ECR_REGISTRY }}/triggers-api:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          cluster: triggers-api-staging
          service: api
          task-definition: task-def-staging.json

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          cluster: triggers-api-production
          service: api
          task-definition: task-def-production.json
```

### 13.3 Deployment Strategies

| Strategy | Use Case |
|----------|----------|
| Rolling | Normal deployments |
| Blue/Green | Major releases |
| Canary | High-risk changes |

### 13.4 Rollback Procedure

1. Identify issue via monitoring alerts
2. Trigger rollback via deployment pipeline
3. Previous version restored within 5 minutes
4. Post-incident review within 24 hours

---

## 14. Observability & Monitoring

### 14.1 Logging

**Structure:**
```json
{
  "timestamp": "2024-11-29T12:00:00.000Z",
  "level": "INFO",
  "service": "triggers-api",
  "trace_id": "abc123",
  "span_id": "def456",
  "message": "Event created",
  "event_id": "evt_01HX7Q8Y...",
  "account_id": "acc_123",
  "latency_ms": 45
}
```

**Tools:** AWS CloudWatch Logs, structured JSON format

### 14.2 Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `events_created_total` | Counter | Total events created |
| `events_delivered_total` | Counter | Total events delivered |
| `event_ingestion_latency` | Histogram | Event creation latency |
| `inbox_size` | Gauge | Pending events per account |
| `webhook_delivery_latency` | Histogram | Webhook round-trip time |
| `api_request_duration` | Histogram | Request latency by endpoint |
| `error_rate` | Gauge | Errors per second |

**Tools:** Prometheus + Grafana or AWS CloudWatch

### 14.3 Tracing

Distributed tracing across all services using OpenTelemetry.

**Trace Headers:**
```http
X-Trace-Id: abc123def456
X-Span-Id: 789xyz
```

### 14.4 Alerting

| Alert | Condition | Severity |
|-------|-----------|----------|
| High Error Rate | > 1% 5xx errors for 5 min | Critical |
| High Latency | p99 > 500ms for 10 min | Warning |
| Queue Depth | > 10,000 pending for 5 min | Warning |
| Database Connections | > 80% pool utilization | Warning |
| API Down | Health check fails 3x | Critical |

### 14.5 Dashboards

**Operations Dashboard:**
- Request rate and latency
- Error rate by endpoint
- Queue depths
- Database performance

**Business Dashboard:**
- Events created per hour
- Top event types
- Account activity
- Delivery success rate

---

## 15. Risk Assessment & Mitigation

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database overload | Medium | High | Read replicas, caching, sharding |
| Queue backup | Medium | Medium | Auto-scaling workers, monitoring |
| Webhook endpoint failures | High | Medium | Retry with backoff, circuit breaker |
| DDoS attack | Low | High | CloudFront WAF, rate limiting |
| Data loss | Low | Critical | Multi-AZ, backups, replication |

### 15.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low adoption | Medium | High | Developer advocacy, documentation |
| Competition | Medium | Medium | Feature velocity, integrations |
| Compliance issues | Low | High | Security audits, legal review |

### 15.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Deployment failures | Medium | Medium | Canary releases, auto-rollback |
| Team knowledge gaps | Medium | Medium | Documentation, cross-training |
| Dependency vulnerabilities | Medium | Medium | Automated scanning, patching |

---

## 16. Dependencies & Assumptions

### 16.1 External Dependencies

| Dependency | Purpose | Fallback |
|------------|---------|----------|
| AWS RDS | Primary database | Multi-AZ failover |
| AWS SQS | Message queue | Multi-AZ |
| AWS ElastiCache | Caching | Graceful degradation |
| AWS KMS | Key management | None (critical) |

### 16.2 Internal Dependencies

| Dependency | Owner | Interface |
|------------|-------|-----------|
| Authentication Service | Platform Team | JWT validation |
| Billing Service | Billing Team | Usage reporting |
| Analytics Pipeline | Data Team | Event streaming |

### 16.3 Assumptions

1. AWS infrastructure is available and reliable
2. Developers are familiar with REST APIs
3. Zapier internal services are accessible
4. Event payloads are JSON-serializable
5. Webhook endpoints are HTTPS

---

## 17. Out of Scope

The following are explicitly **not** included in this MVP:

| Item | Reason | Future Phase |
|------|--------|--------------|
| GraphQL API | Complexity; REST sufficient for MVP | v2.0 |
| Event transformation | Requires rule engine | v1.2 |
| Advanced filtering | Complex query language | v1.2 |
| Long-term archival | Storage cost considerations | v1.3 |
| Multi-region | Operational complexity | v2.0 |
| Self-hosted option | Different deployment model | v3.0 |
| SDK libraries | Can be built post-launch | v1.1 |

---

## 18. Future Roadmap

### 18.1 Phase 1: MVP (Current)
- Core event ingestion
- Inbox retrieval
- Event acknowledgment
- API key authentication
- Basic monitoring

### 18.2 Phase 2: Enhanced Delivery
- Webhook subscriptions
- Retry policies
- Event replay
- Delivery dashboard

### 18.3 Phase 3: Developer Experience
- SDK libraries (Python, Node.js, Go)
- CLI tool
- Interactive documentation
- Event playground

### 18.4 Phase 4: Advanced Features
- Event filtering rules
- Schema registry
- Event transformation
- Analytics dashboard

### 18.5 Phase 5: Enterprise
- Multi-region deployment
- SLA guarantees
- Dedicated support
- Custom retention policies

---

## 19. Appendix

### 19.1 Glossary

| Term | Definition |
|------|------------|
| Event | A JSON payload representing something that happened |
| Trigger | A Zapier mechanism that starts a workflow |
| Inbox | Queue of undelivered events for an account |
| Subscription | Webhook endpoint configuration |
| Idempotency | Guarantee that duplicate requests produce same result |
| Dead Letter Queue | Storage for events that failed delivery |

### 19.2 Reference Documents

- [Zapier Platform Documentation](https://platform.zapier.com/docs)
- [CloudEvents Specification](https://cloudevents.io/)
- [OpenAPI 3.0 Specification](https://swagger.io/specification/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

### 19.3 Related Systems

- Zapier Integration Platform
- Zapier Workflow Engine
- Zapier Authentication Service
- Zapier Billing Service

### 19.4 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-29 | Akhil P | Initial draft |

---

*This document is a living artifact and will be updated as the project evolves.*
