import asyncio
import logging

from sqlalchemy import select

from app.constants import RABBIT_POLL_INTERVAL, RABBIT_BATCH_SIZE
from app.db.database import async_session_maker
from app.db.models.payment_outbox import PaymentOutbox
from app.rabbitmq.broker import broker

logger = logging.getLogger(__name__)


async def publish_pending() -> int:
    async with async_session_maker() as session:
        stmt = (
            select(PaymentOutbox)
            .where(PaymentOutbox.is_processed.is_(False))
            .order_by(PaymentOutbox.created_at)
            .limit(RABBIT_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        events = (await session.scalars(stmt)).all()

        if not events:
            return 0

        published = 0
        for event in events:
            try:
                await broker.publish(event.payload, queue='payments.new', persist=True)
                event.is_processed = True
                published += 1
            except Exception:
                logger.exception(f"Failed to publish outbox event {event.id}")

        await session.commit()
        return published


async def publisher_loop() -> None:
    logger.info(f"Publisher started, polling every {RABBIT_POLL_INTERVAL}s")
    while True:
        try:
            count = await publish_pending()
            if count:
                logger.info(f"Published {count} outbox event(s)")
        except Exception:
            logger.exception("Publisher iteration failed")
        await asyncio.sleep(RABBIT_POLL_INTERVAL)