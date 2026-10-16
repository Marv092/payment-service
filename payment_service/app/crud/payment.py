import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.payment_outbox import PaymentOutbox
from app.db.models.payments import Payment, PaymentStatus
from app.schemas.payments import PaymentCreate


class PaymentCRUD:
    async def get_by_id(self, db: AsyncSession, *, payment_id: uuid.UUID) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, db: AsyncSession, *, idempotency_key: uuid.UUID) -> Optional[Payment]:
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: PaymentCreate, idempotency_key: uuid.UUID) -> Payment:
        payment_data = obj_in.model_dump(mode="json")

        new_payment = Payment(
            amount=obj_in.amount,
            currency=obj_in.currency,
            description=obj_in.description,
            webhook_url=payment_data["webhook_url"],
            meta=obj_in.meta,
            idempotency_key=idempotency_key
        )
        db.add(new_payment)

        await db.flush()

        event_payload = {
            "payment_id": str(new_payment.id),
            "amount": payment_data["amount"],
            "currency": payment_data["currency"],
            "webhook_url": payment_data["webhook_url"]
        }

        outbox_entry = PaymentOutbox(
            event_type="payments.new",
            payload=event_payload
        )
        db.add(outbox_entry)

        await db.commit()
        await db.refresh(new_payment)

        return new_payment

    async def update_status(self, db: AsyncSession, *, payment: Payment, status: PaymentStatus) -> Payment:
        payment.status = status
        if status in (PaymentStatus.succeeded, PaymentStatus.failed):
            payment.processed_at = datetime.now(timezone.utc)

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment


payment_crud = PaymentCRUD()
