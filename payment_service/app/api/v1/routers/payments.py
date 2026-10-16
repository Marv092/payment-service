import uuid

from fastapi import APIRouter, status, Header, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.payment import payment_crud
from app.db.database import get_async_session
from app.schemas.payments import PaymentAccepted, PaymentCreate, PaymentRead

payments = APIRouter(prefix="/payments", tags=["payments"])

@payments.post("", response_model=PaymentAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(data: PaymentCreate,
                         idempotency_key: uuid.UUID = Header(..., alias="Idempotency-Key"),
                         db: AsyncSession = Depends(get_async_session)):
    try:
        payment = await payment_crud.create(db, obj_in=data, idempotency_key=idempotency_key)
    except IntegrityError:
        await db.rollback()
        existing = await payment_crud.get_by_idempotency_key(db, idempotency_key=idempotency_key)
        return existing

    return payment


@payments.get("/{payment_id}", response_model=PaymentRead, status_code=status.HTTP_200_OK)
async def get_payment(payment_id: uuid.UUID,
                      db: AsyncSession = Depends(get_async_session)):
    payment = await payment_crud.get_by_id(db, payment_id=payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    return payment