"""
Delivery Worker.

Background worker that processes webhook deliveries from the queue.
"""

import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.redis import get_redis
from app.services.delivery_service import DeliveryService

logger = logging.getLogger(__name__)


class DeliveryWorker:
    """
    Background worker for processing webhook deliveries.

    Polls pending deliveries from the database and executes them
    with proper retry handling and error management.
    """

    # How often to poll for new deliveries (seconds)
    POLL_INTERVAL = 1.0

    # How many deliveries to process per batch
    BATCH_SIZE = 50

    # How many concurrent deliveries to execute
    CONCURRENCY = 10

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        poll_interval: float | None = None,
        batch_size: int | None = None,
        concurrency: int | None = None,
    ):
        """
        Initialize the delivery worker.

        Args:
            session_factory: SQLAlchemy async session factory
            poll_interval: Override default poll interval
            batch_size: Override default batch size
            concurrency: Override default concurrency
        """
        self.session_factory = session_factory
        self.poll_interval = poll_interval or self.POLL_INTERVAL
        self.batch_size = batch_size or self.BATCH_SIZE
        self.concurrency = concurrency or self.CONCURRENCY

        self._running = False
        self._shutdown_event = asyncio.Event()
        self._semaphore: asyncio.Semaphore | None = None
        self._active_tasks: set[asyncio.Task] = set()

    async def start(self) -> None:
        """Start the delivery worker."""
        if self._running:
            logger.warning("Worker already running")
            return

        logger.info(
            f"Starting delivery worker (poll={self.poll_interval}s, "
            f"batch={self.batch_size}, concurrency={self.concurrency})"
        )

        self._running = True
        self._shutdown_event.clear()
        self._semaphore = asyncio.Semaphore(self.concurrency)

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown_signal)

        try:
            await self._run_loop()
        finally:
            self._running = False
            logger.info("Delivery worker stopped")

    async def stop(self) -> None:
        """Stop the delivery worker gracefully."""
        if not self._running:
            return

        logger.info("Stopping delivery worker...")
        self._shutdown_event.set()

        # Wait for active tasks to complete (with timeout)
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks...")
            done, pending = await asyncio.wait(
                self._active_tasks,
                timeout=30.0,
                return_when=asyncio.ALL_COMPLETED,
            )

            if pending:
                logger.warning(f"Cancelling {len(pending)} pending tasks")
                for task in pending:
                    task.cancel()

    def _handle_shutdown_signal(self) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal")
        self._shutdown_event.set()

    async def _run_loop(self) -> None:
        """Main processing loop."""
        while not self._shutdown_event.is_set():
            try:
                processed = await self._process_batch()

                if processed == 0:
                    # No work, wait before polling again
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.poll_interval,
                        )
                    except asyncio.TimeoutError:
                        pass
                # If we processed items, immediately check for more

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                # Back off on errors
                await asyncio.sleep(5.0)

    async def _process_batch(self) -> int:
        """
        Process a batch of pending deliveries.

        Returns:
            int: Number of deliveries processed
        """
        async with self.session_factory() as db:
            service = DeliveryService(db)

            # Get pending deliveries
            deliveries = await service.get_pending_deliveries(limit=self.batch_size)

            if not deliveries:
                return 0

            logger.debug(f"Processing {len(deliveries)} deliveries")

            # Process deliveries concurrently
            tasks = []
            for delivery in deliveries:
                task = asyncio.create_task(
                    self._process_delivery(delivery.id)
                )
                self._active_tasks.add(task)
                task.add_done_callback(self._active_tasks.discard)
                tasks.append(task)

            # Wait for all tasks in this batch
            await asyncio.gather(*tasks, return_exceptions=True)

            return len(deliveries)

    async def _process_delivery(self, delivery_id: str) -> None:
        """
        Process a single delivery with concurrency control.

        Args:
            delivery_id: The delivery ID to process
        """
        if self._semaphore is None:
            return

        async with self._semaphore:
            if self._shutdown_event.is_set():
                return

            async with self.session_factory() as db:
                try:
                    service = DeliveryService(db)

                    # Fetch the delivery (it might have been processed by another worker)
                    from app.models import DeliveryStatus, EventDelivery

                    delivery = await db.get(EventDelivery, delivery_id)

                    if not delivery:
                        logger.warning(f"Delivery {delivery_id} not found")
                        return

                    if delivery.status not in (
                        DeliveryStatus.PENDING,
                        DeliveryStatus.RETRYING,
                    ):
                        logger.debug(
                            f"Delivery {delivery_id} already processed: {delivery.status}"
                        )
                        return

                    # Execute the delivery
                    success = await service.execute_delivery(delivery)

                    # Commit the transaction
                    await db.commit()

                    if success:
                        logger.info(f"Delivery {delivery_id} completed successfully")
                    else:
                        logger.debug(
                            f"Delivery {delivery_id} failed, "
                            f"attempt {delivery.attempt_count}/{delivery.max_attempts}"
                        )

                except Exception as e:
                    logger.error(f"Error processing delivery {delivery_id}: {e}")
                    await db.rollback()


class EventProcessor:
    """
    Processes incoming events and creates deliveries.

    Separate from the delivery worker to allow independent scaling.
    """

    POLL_INTERVAL = 0.5
    BATCH_SIZE = 100

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        poll_interval: float | None = None,
        batch_size: int | None = None,
    ):
        """Initialize the event processor."""
        self.session_factory = session_factory
        self.poll_interval = poll_interval or self.POLL_INTERVAL
        self.batch_size = batch_size or self.BATCH_SIZE

        self._running = False
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the event processor."""
        if self._running:
            return

        logger.info("Starting event processor")
        self._running = True
        self._shutdown_event.clear()

        try:
            await self._run_loop()
        finally:
            self._running = False
            logger.info("Event processor stopped")

    async def stop(self) -> None:
        """Stop the event processor."""
        if not self._running:
            return

        logger.info("Stopping event processor...")
        self._shutdown_event.set()

    async def _run_loop(self) -> None:
        """Main processing loop."""
        while not self._shutdown_event.is_set():
            try:
                processed = await self._process_pending_events()

                if processed == 0:
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.poll_interval,
                        )
                    except asyncio.TimeoutError:
                        pass

            except Exception as e:
                logger.error(f"Error in event processor loop: {e}", exc_info=True)
                await asyncio.sleep(5.0)

    async def _process_pending_events(self) -> int:
        """Process pending events and create deliveries."""
        from sqlalchemy import select

        from app.models import Event, EventStatus

        async with self.session_factory() as db:
            # Get pending events
            result = await db.execute(
                select(Event)
                .where(Event.status == EventStatus.PENDING)
                .order_by(Event.created_at.asc())
                .limit(self.batch_size)
            )
            events = list(result.scalars().all())

            if not events:
                return 0

            logger.debug(f"Processing {len(events)} pending events")

            service = DeliveryService(db)

            for event in events:
                try:
                    await service.create_deliveries_for_event(event)
                except Exception as e:
                    logger.error(f"Error creating deliveries for event {event.id}: {e}")
                    event.status = EventStatus.FAILED
                    event.last_error = str(e)

            await db.commit()

            return len(events)


async def run_workers(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """
    Run both the event processor and delivery worker.

    This is a convenience function for running both workers together.
    In production, these might run as separate processes for independent scaling.
    """
    event_processor = EventProcessor(session_factory)
    delivery_worker = DeliveryWorker(session_factory)

    async def shutdown_all():
        await asyncio.gather(
            event_processor.stop(),
            delivery_worker.stop(),
        )

    # Run both concurrently
    try:
        await asyncio.gather(
            event_processor.start(),
            delivery_worker.start(),
        )
    except asyncio.CancelledError:
        await shutdown_all()
