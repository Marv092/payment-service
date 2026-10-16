import asyncio
import logging
import random
import uuid

import aio_pika
import httpx
from faststream.rabbit import RabbitMessage

from app.config import settings
from app.constants import WEBHOOK_RETRIES
from app.crud.payment import payment_crud
from app.db.database import async_session_maker
from app.db.models.payments import PaymentStatus
from app.logging.logging_config import setup_logging
from app.rabbitmq.broker import broker, main_queue, dlx, dlq

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


async def send_webhook_with_exponential_backoff(url: str, payload: dict, max_retries: int = WEBHOOK_RETRIES) -> bool:
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(url, json=payload, timeout=5.0)

                if 200 <= response.status_code < 300:
                    return True
                logger.warning(f"Client webhook endpoint responded with status code: {response.status_code}")
            except httpx.HTTPError as exc:
                logger.warning(f"Network error during webhook delivery on attempt {attempt + 1}: {exc}")

            if attempt < max_retries - 1:
                backoff_time = 2 ** (attempt + 1)
                await asyncio.sleep(backoff_time)

    return False


async def update_status(payment_id: str, new_status: PaymentStatus) -> None:
    async with async_session_maker() as session:
        payment = await payment_crud.get_by_id(
            session, payment_id=uuid.UUID(payment_id)
        )
        if payment is None:
            raise LookupError(f"Payment {payment_id} not found")

        if payment.status != PaymentStatus.pending:
            logger.info(f"Payment {payment_id} already in state {payment.status}, skipping")
            return

        await payment_crud.update_status(session, payment=payment, status=new_status)


async def process_payment(payment_id: str) -> PaymentStatus:
    await asyncio.sleep(random.uniform(2, 5))

    if random.random() < 0.9:
        logger.info(f"Payment {payment_id} succeeded")
        await update_status(payment_id, PaymentStatus.succeeded)
        return PaymentStatus.succeeded
    else:
        logger.warning(f"Payment {payment_id} failed")
        await update_status(payment_id, PaymentStatus.failed)
        return PaymentStatus.failed


@broker.subscriber(main_queue)
async def handle_new_payment(payload: dict, msg: RabbitMessage) -> None:
    payment_id = payload["payment_id"]
    webhook_url = payload["webhook_url"]

    final_status = await process_payment(payment_id)

    webhook_data = {"payment_id": payment_id, "status": final_status.value}

    webhook_sent = await send_webhook_with_exponential_backoff(
        url=str(webhook_url),
        payload=webhook_data,
        max_retries=WEBHOOK_RETRIES
    )

    if not webhook_sent:
        logger.error(f"Webhook delivery failed for payment {payment_id}, sending to DLQ")
        await msg.nack(requeue=False)
        return

    logger.info(f"Payment {payment_id} successfully processed and closed.")


async def setup_dlq_binding() -> None:
    """привязываем payments.dlq к payments.dlx с routing key payments.new."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            dlx.name, aio_pika.ExchangeType.DIRECT, durable=True
        )
        queue = await channel.declare_queue(dlq.name, durable=True)
        await queue.bind(exchange, routing_key=dlq.routing_key or "payments.new")
        logger.info(f"DLQ bound to DLX: {dlx.name} -> {dlq.name}")


async def main() -> None:
    logger.info("Starting consumer")
    await setup_dlq_binding()
    async with broker:
        await broker.declare_exchange(dlx)
        await broker.declare_queue(dlq)
        await broker.start()
        await asyncio.Event().wait()

    logger.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())
