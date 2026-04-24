from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.models.order import Order, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.models.payment_transaction import PaymentTransaction
from app.observability.metrics import metrics_registry


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PaymentProviderResult:
    status: PaymentStatusEnum
    response_payload: dict[str, Any]
    external_payment_id: str | None = None
    redirect_url: str | None = None
    failure_code: str | None = None
    failure_reason: str | None = None
    processed_at: datetime | None = None


class PaymentProvider(Protocol):
    provider_name: str

    async def initiate_payment(
        self,
        *,
        order: Order,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentProviderResult:
        ...


class StubPaymentProvider:
    provider_name = "stub"

    async def initiate_payment(
        self,
        *,
        order: Order,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentProviderResult:
        upper_comment = " ".join(
            part.upper()
            for part in (
                order.customer_comment or "",
                order.delivery_instructions or "",
            )
        )
        if setting.payment_stub_failure_keyword and setting.payment_stub_failure_keyword.upper() in upper_comment:
            return PaymentProviderResult(
                status=PaymentStatusEnum.FAILED,
                external_payment_id=f"stub_fail_{uuid4().hex[:12]}",
                failure_code="stub_declined",
                failure_reason="Платёж отклонён stub-провайдером.",
                response_payload={
                    "provider": self.provider_name,
                    "idempotency_key": idempotency_key,
                    "mode": "failure",
                },
                processed_at=datetime.now(timezone.utc),
            )

        if order.payment_method == PaymentMethodEnum.CARD_ONLINE and setting.payment_stub_auto_approve:
            return PaymentProviderResult(
                status=PaymentStatusEnum.SUCCEEDED,
                external_payment_id=f"stub_ok_{uuid4().hex[:12]}",
                response_payload={
                    "provider": self.provider_name,
                    "idempotency_key": idempotency_key,
                    "mode": "auto_approved",
                    "amount": str(amount),
                    "currency": currency,
                },
                processed_at=datetime.now(timezone.utc),
            )

        return PaymentProviderResult(
            status=PaymentStatusEnum.PENDING,
            external_payment_id=f"stub_pending_{uuid4().hex[:12]}",
            response_payload={
                "provider": self.provider_name,
                "idempotency_key": idempotency_key,
                "mode": "awaiting_offline_confirmation",
                "amount": str(amount),
                "currency": currency,
            },
        )


def get_payment_provider() -> PaymentProvider:
    provider_name = setting.payment_provider.strip().lower()
    if provider_name == "stub":
        return StubPaymentProvider()
    raise ValueError(f"Unsupported payment provider configured: {setting.payment_provider}")


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        provider: PaymentProvider | None = None,
    ) -> None:
        self.session = session
        self.provider = provider or get_payment_provider()

    async def create_checkout_payment(self, order: Order) -> PaymentTransaction:
        idempotency_key = f"checkout:{order.id}:{uuid4().hex}"
        return await self._create_transaction(order=order, idempotency_key=idempotency_key)

    async def retry_payment(self, order: Order) -> PaymentTransaction:
        if order.payment_method != PaymentMethodEnum.CARD_ONLINE:
            raise ValueError("Повторная оплата доступна только для онлайн-оплаты картой.")
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            raise ValueError("Заказ уже успешно оплачен.")

        idempotency_key = f"retry:{order.id}:{uuid4().hex}"
        return await self._create_transaction(order=order, idempotency_key=idempotency_key)

    async def mark_offline_payment_succeeded(self, order: Order) -> PaymentTransaction | None:
        if order.payment_method not in {
            PaymentMethodEnum.CASH_ON_DELIVERY,
            PaymentMethodEnum.CARD_ON_DELIVERY,
        }:
            return None
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            return None

        transaction = await self._get_latest_transaction(order)
        if transaction is None:
            transaction = PaymentTransaction(
                order_id=order.id,
                provider_name=self.provider.provider_name,
                payment_method=order.payment_method,
                status=PaymentStatusEnum.SUCCEEDED,
                amount=order.total_amount,
                currency=order.currency,
                idempotency_key=f"delivery:{order.id}:{uuid4().hex}",
                response_payload={"mode": "offline_completed"},
                processed_at=datetime.now(timezone.utc),
            )
            self.session.add(transaction)
        else:
            transaction.status = PaymentStatusEnum.SUCCEEDED
            transaction.failure_code = None
            transaction.failure_reason = None
            transaction.processed_at = datetime.now(timezone.utc)
            transaction.response_payload = {
                **(transaction.response_payload or {}),
                "mode": "offline_completed",
            }

        order.payment_status = PaymentStatusEnum.SUCCEEDED
        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=self.provider.provider_name,
            status=PaymentStatusEnum.SUCCEEDED.value,
            method=order.payment_method.value,
        )
        return transaction

    async def cancel_pending_payment(self, order: Order) -> PaymentTransaction | None:
        if order.payment_status != PaymentStatusEnum.PENDING:
            return None

        transaction = await self._get_latest_transaction(order)
        if transaction is None:
            return None

        transaction.status = PaymentStatusEnum.CANCELLED
        transaction.processed_at = datetime.now(timezone.utc)
        transaction.response_payload = {
            **(transaction.response_payload or {}),
            "mode": "cancelled",
        }
        order.payment_status = PaymentStatusEnum.CANCELLED
        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=transaction.provider_name,
            status=PaymentStatusEnum.CANCELLED.value,
            method=order.payment_method.value,
        )
        return transaction

    async def _create_transaction(
        self,
        *,
        order: Order,
        idempotency_key: str,
    ) -> PaymentTransaction:
        provider_result = await self.provider.initiate_payment(
            order=order,
            amount=order.total_amount,
            currency=order.currency,
            idempotency_key=idempotency_key,
        )
        transaction = PaymentTransaction(
            order_id=order.id,
            provider_name=self.provider.provider_name,
            payment_method=order.payment_method,
            status=provider_result.status,
            amount=order.total_amount,
            currency=order.currency,
            idempotency_key=idempotency_key,
            external_payment_id=provider_result.external_payment_id,
            redirect_url=provider_result.redirect_url,
            failure_code=provider_result.failure_code,
            failure_reason=provider_result.failure_reason,
            request_payload={
                "order_id": str(order.id),
                "payment_method": order.payment_method.value,
            },
            response_payload=provider_result.response_payload,
            processed_at=provider_result.processed_at,
        )
        self.session.add(transaction)

        order.payment_status = provider_result.status
        if provider_result.status == PaymentStatusEnum.SUCCEEDED:
            order.status = OrderStatusEnum.PAID
        elif provider_result.status == PaymentStatusEnum.CANCELLED:
            order.status = OrderStatusEnum.CANCELLED
        else:
            order.status = OrderStatusEnum.PENDING

        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=self.provider.provider_name,
            status=provider_result.status.value,
            method=order.payment_method.value,
        )
        logger.info(
            "payment_transaction_created",
            extra={
                "event": "payment_transaction_created",
                "order_id": str(order.id),
                "provider": self.provider.provider_name,
                "payment_status": provider_result.status.value,
                "payment_method": order.payment_method.value,
            },
        )
        return transaction

    async def _get_latest_transaction(self, order: Order) -> PaymentTransaction | None:
        if order.payment_transactions:
            return order.payment_transactions[-1]
        return None
