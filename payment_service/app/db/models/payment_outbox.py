import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import UUID, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PaymentOutbox(Base):
    __tablename__ = "payment_outbox"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, init=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), init=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False, init=False)
