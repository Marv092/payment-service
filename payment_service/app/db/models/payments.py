import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy import UUID, DECIMAL, String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import PAYMENT_MAX_DIGITS, PAYMENT_DECIMAL_PLACES
from app.db.database import Base


class Currency(str, enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, init=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending, init=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(PAYMENT_MAX_DIGITS, PAYMENT_DECIMAL_PLACES), nullable=False)
    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID (as_uuid=True), unique=True, index=True, nullable=False)
    webhook_url: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), init=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, init=False)
