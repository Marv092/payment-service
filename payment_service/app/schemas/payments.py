from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from app.db.models.payments import Currency, PaymentStatus


class PaymentBase(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str
    meta:  Optional[Dict[str, Any]] = None
    webhook_url: HttpUrl

class PaymentCreate(PaymentBase):
    pass

class PaymentAccepted(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias="id", serialization_alias="payment_id")
    status: PaymentStatus
    created_at: datetime

class PaymentRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PaymentStatus
    idempotency_key: UUID
    created_at: datetime
    processed_at: Optional[datetime]

