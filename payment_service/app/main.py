import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import settings
from app.db.database import engine
from app.logging.logging_config import setup_logging
from app.rabbitmq.broker import broker
from app.rabbitmq.publisher import publisher_loop

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    logger.info("RabbitMQ connected")

    publisher_task = asyncio.create_task(publisher_loop())
    logger.info("Publisher background task started")

    yield

    publisher_task.cancel()
    try:
        await publisher_task
    except asyncio.CancelledError:
        pass

    await broker.close()
    await engine.dispose()
    logger.info("RabbitMQ shutdown complete")


app = FastAPI(title="Payment Service",  lifespan=lifespan)
app.include_router(api_router)

