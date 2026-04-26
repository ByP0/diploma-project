from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import PaymentStatusEnum


class PaymentStatusCheckRead(BaseModel):
    transaction_id: UUID
    order_id: UUID
    provider_name: str
    status: PaymentStatusEnum
    checked_at: datetime


class PaymentRefundRequest(BaseModel):
    amount: Decimal | None = None
    idempotency_key: Annotated[str | None, Field(max_length=128)] = None
    reason: Annotated[str | None, Field(max_length=1000)] = None

    model_config = ConfigDict(extra="forbid")
