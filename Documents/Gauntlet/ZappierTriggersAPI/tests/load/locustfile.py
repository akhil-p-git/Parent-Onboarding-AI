"""
Locust Load Tests for Zapier Triggers API.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --headless -u 100 -r 10 --run-time 60s
"""

import json
import random
import time
import uuid
from typing import Any

from locust import HttpUser, between, task
from locust.contrib.fasthttp import FastHttpUser


# Configuration
API_KEY = "sk_test_your_api_key_here"  # Replace with valid test API key


class EventIngestionUser(FastHttpUser):
    """
    Load test user for event ingestion scenarios.

    Simulates high-throughput event ingestion.
    """

    wait_time = between(0.1, 0.5)  # Fast operations

    def on_start(self):
        """Set up authentication headers."""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        self.event_types = [
            "user.created",
            "user.updated",
            "user.deleted",
            "order.created",
            "order.completed",
            "order.cancelled",
            "payment.received",
            "payment.failed",
            "notification.sent",
        ]
        self.sources = [
            "user-service",
            "order-service",
            "payment-service",
            "notification-service",
            "api-gateway",
        ]

    @task(10)
    def create_single_event(self):
        """Create a single event."""
        event_data = self._generate_event()

        with self.client.post(
            "/api/v1/events",
            json=event_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def create_batch_events(self):
        """Create a batch of events."""
        batch_size = random.randint(10, 50)
        batch_data = {
            "events": [self._generate_event() for _ in range(batch_size)]
        }

        with self.client.post(
            "/api/v1/events/batch",
            json=batch_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if data.get("summary", {}).get("failed", 0) == 0:
                    response.success()
                else:
                    response.failure(f"Partial failure: {data['summary']}")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def create_event_with_idempotency(self):
        """Create an event with idempotency key."""
        event_data = self._generate_event()
        event_data["idempotency_key"] = str(uuid.uuid4())

        with self.client.post(
            "/api/v1/events",
            json=event_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [201, 200]:  # 200 for duplicate
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def _generate_event(self) -> dict[str, Any]:
        """Generate random event data."""
        return {
            "event_type": random.choice(self.event_types),
            "source": random.choice(self.sources),
            "data": {
                "id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "action": random.choice(["create", "update", "delete"]),
                "payload": {
                    "key1": f"value_{random.randint(1, 1000)}",
                    "key2": random.random() * 100,
                },
            },
            "metadata": {
                "environment": "load-test",
                "correlation_id": str(uuid.uuid4()),
            },
        }


class InboxPollingUser(FastHttpUser):
    """
    Load test user for inbox polling scenarios.

    Simulates consumers polling the inbox for events.
    """

    wait_time = between(0.5, 2)  # Polling interval

    def on_start(self):
        """Set up authentication headers."""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        self.receipt_handles = []

    @task(5)
    def poll_inbox(self):
        """Poll inbox for events."""
        with self.client.get(
            "/api/v1/inbox?limit=10&visibility_timeout=30",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])

                # Store receipt handles for acknowledgment
                for event in events:
                    if "receipt_handle" in event:
                        self.receipt_handles.append(event["receipt_handle"])

                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def acknowledge_single(self):
        """Acknowledge a single event."""
        if not self.receipt_handles:
            return

        receipt_handle = self.receipt_handles.pop(0)

        with self.client.delete(
            f"/api/v1/inbox/{receipt_handle}",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [204, 404]:  # 404 if already acked
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def batch_acknowledge(self):
        """Batch acknowledge events."""
        if len(self.receipt_handles) < 3:
            return

        handles_to_ack = [self.receipt_handles.pop(0) for _ in range(min(5, len(self.receipt_handles)))]

        with self.client.post(
            "/api/v1/inbox/ack",
            json={"receipt_handles": handles_to_ack},
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_inbox_stats(self):
        """Get inbox statistics."""
        with self.client.get(
            "/api/v1/inbox/stats",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class SubscriptionManagementUser(HttpUser):
    """
    Load test user for subscription management.

    Simulates subscription CRUD operations (lower frequency).
    """

    wait_time = between(2, 5)  # Less frequent operations

    def on_start(self):
        """Set up authentication headers."""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        self.created_subscriptions = []

    @task(3)
    def list_subscriptions(self):
        """List subscriptions."""
        with self.client.get(
            "/api/v1/subscriptions?limit=20",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def create_subscription(self):
        """Create a new subscription."""
        subscription_data = {
            "name": f"Load Test Subscription {uuid.uuid4().hex[:8]}",
            "target_url": f"https://webhook.example.com/{uuid.uuid4().hex}",
            "filters": {
                "event_types": ["user.created", "order.completed"],
            },
            "webhook_config": {
                "timeout_seconds": 30,
                "retry_strategy": "exponential",
                "max_retries": 3,
            },
        }

        with self.client.post(
            "/api/v1/subscriptions",
            json=subscription_data,
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.created_subscriptions.append(data["id"])
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_subscription(self):
        """Get a subscription."""
        if not self.created_subscriptions:
            return

        sub_id = random.choice(self.created_subscriptions)

        with self.client.get(
            f"/api/v1/subscriptions/{sub_id}",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def delete_subscription(self):
        """Delete a subscription."""
        if not self.created_subscriptions:
            return

        sub_id = self.created_subscriptions.pop(0)

        with self.client.delete(
            f"/api/v1/subscriptions/{sub_id}",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code in [204, 404]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_subscription_stats(self):
        """Get subscription statistics."""
        with self.client.get(
            "/api/v1/subscriptions/stats",
            headers=self.headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class HealthCheckUser(FastHttpUser):
    """
    Load test user for health checks.

    Simulates monitoring systems hitting health endpoints.
    """

    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        """Check health endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def readiness_check(self):
        """Check readiness endpoint."""
        with self.client.get("/ready", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def liveness_check(self):
        """Check liveness endpoint."""
        with self.client.get("/live", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def metrics_check(self):
        """Check metrics endpoint."""
        with self.client.get(
            "/api/v1/health/metrics/prometheus",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class MixedWorkloadUser(FastHttpUser):
    """
    Load test user with mixed workload.

    Simulates realistic production traffic patterns.
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        """Set up authentication headers."""
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

    @task(50)
    def create_event(self):
        """Create event (most common operation)."""
        event_data = {
            "event_type": random.choice(["user.created", "order.completed"]),
            "source": "mixed-workload",
            "data": {"id": str(uuid.uuid4())},
        }

        self.client.post(
            "/api/v1/events",
            json=event_data,
            headers=self.headers,
        )

    @task(20)
    def poll_inbox(self):
        """Poll inbox."""
        self.client.get(
            "/api/v1/inbox?limit=5&visibility_timeout=30",
            headers=self.headers,
        )

    @task(10)
    def list_events(self):
        """List events."""
        self.client.get(
            "/api/v1/events?limit=20",
            headers=self.headers,
        )

    @task(5)
    def list_subscriptions(self):
        """List subscriptions."""
        self.client.get(
            "/api/v1/subscriptions?limit=10",
            headers=self.headers,
        )

    @task(5)
    def health_check(self):
        """Health check."""
        self.client.get("/health")

    @task(2)
    def batch_events(self):
        """Batch create events."""
        batch_data = {
            "events": [
                {
                    "event_type": "batch.event",
                    "source": "mixed-workload",
                    "data": {"index": i},
                }
                for i in range(10)
            ]
        }
        self.client.post(
            "/api/v1/events/batch",
            json=batch_data,
            headers=self.headers,
        )
