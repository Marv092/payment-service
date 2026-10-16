from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType
from faststream.rabbit.schemas.queue import ClassicQueueArgs

from app.config import settings

broker = RabbitBroker(settings.rabbitmq_url)

dlx = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)
dlq = RabbitQueue("payments.dlq", durable=True, routing_key="payments.new")

_queue_arguments: ClassicQueueArgs = {
    "x-dead-letter-exchange": "payments.dlx",
    "x-dead-letter-routing-key": "payments.new",
}

main_queue = RabbitQueue(
    "payments.new",
    durable=True,
    routing_key="payments.new",
    arguments=_queue_arguments,
)