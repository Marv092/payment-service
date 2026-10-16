# Payment Service

Микросервис для асинхронной обработки платежей. Принимает запросы на оплату,
обрабатывает их через эмуляцию платёжного шлюза и уведомляет клиента о
результате через webhook.

Реализовано: Outbox pattern, идемпотентность по `Idempotency-Key`, retry при
ошибках webhook (3 попытки, экспоненциальный backoff), Dead Letter Queue.

---

## Стек

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + asyncpg
- PostgreSQL 16
- RabbitMQ 3.13 + FastStream
- Alembic
- Docker + docker-compose

---

## Запуск

```bash
git clone https://github.com/Marv092/payment-service.git
cd payment-service
cp .env.example .env
docker compose up --build
```

Поднимаются 4 контейнера:

| Сервис | Порт |
|---|---|
| `payments` (FastAPI) | 8000 |
| `consumer` | — |
| `postgres_payments` | 5432 |
| `rabbitmq` | 5672, 15672 |

- Swagger UI: http://localhost:8000/docs
- RabbitMQ UI: http://localhost:15672 (guest / guest)

Остановить:

```bash
docker compose down -v       # с удалением volume Postgres
```

---

## API

Все эндпоинты требуют `X-API-Key: api_key_for_auth`.
POST дополнительно требует `Idempotency-Key` (валидный UUID).

### Создать платёж

```bash
curl -i -X POST http://localhost:8000/api/v1/payments \
  -H 'X-API-Key: api_key_for_auth' \
  -H 'Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000' \
  -H 'Content-Type: application/json' \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Test payment",
    "meta": {"order_id": "42"},
    "webhook_url": "https://webhook.site/<your-id>"
  }'
```

Ответ `202 Accepted`:

```json
{
  "payment_id": "22278b98-6976-4dcc-8c9d-442e34554e3b",
  "status": "pending",
  "created_at": "2026-10-16T11:21:16.320716Z"
}
```

### Получить платёж

```bash
curl -i http://localhost:8000/api/v1/payments/22278b98-6976-4dcc-8c9d-442e34554e3b \
  -H 'X-API-Key: api_key_for_auth'
```

Ответ `200 OK`:

```json
{
  "id": "22278b98-6976-4dcc-8c9d-442e34554e3b",
  "amount": "100.50",
  "currency": "RUB",
  "description": "Test payment",
  "meta": {"order_id": "42"},
  "status": "succeeded",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "webhook_url": "https://webhook.site/...",
  "created_at": "2026-10-16T11:21:16.320716Z",
  "processed_at": "2026-10-16T11:21:23.123456Z"
}
```

### Коды ответов

| Код | Когда |
|---|---|
| `202` | Платёж принят |
| `200` | GET успешен |
| `401` | Неверный `X-API-Key` |
| `404` | Платёж не найден |
| `422` | Невалидное тело / не UUID в `Idempotency-Key` / нет заголовка |

### Проверка сценариев

**Идемпотентность** — два POST с одним `Idempotency-Key` → один `payment_id`,
одна строка в БД.

**Retry + DLQ** — POST с `webhook_url: "https://httpstat.us/500"` → 3 попытки
webhook → сообщение в `payments.dlq`:

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages
```

---

## Переменные окружения (`.env`)

| Переменная | Пример |
|---|---|
| `DATABASE_NAME` | `payments_db` |
| `DATABASE_USERNAME` | `db_user` |
| `DATABASE_PASSWORD` | `db_password` |
| `DATABASE_PORT` | `5432` |
| `AUTH_API_KEY` | `api_key_for_auth` |
| `RABBITMQ_USER` | `guest` |
| `RABBITMQ_PASSWORD` | `guest` |
| `LOG_LEVEL` | `INFO` |

Полный список — в `.env.example`.