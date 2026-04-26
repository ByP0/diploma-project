from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.domain_events import (
    PaymentAuthorized,
    PaymentCaptured,
    PaymentCreated,
    PaymentFailed,
    PaymentRefunded,
    WebhookPaymentReceived,
)
from app.events.publishers.event_publisher import EventPublisher
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

    async def check_status(
        self,
        *,
        transaction: PaymentTransaction,
    ) -> PaymentProviderResult:
        ...

    async def refund(
        self,
        *,
        transaction: PaymentTransaction,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentProviderResult:
        ...


class StubAutoApprovePaymentProvider:
    provider_name = "stub_auto"

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
                failure_reason="Payment was declined by stub provider.",
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

    async def check_status(
        self,
        *,
        transaction: PaymentTransaction,
    ) -> PaymentProviderResult:
        return PaymentProviderResult(
            status=transaction.status,
            response_payload={
                **(transaction.response_payload or {}),
                "checked_with": self.provider_name,
            },
            external_payment_id=transaction.external_payment_id,
            redirect_url=transaction.redirect_url,
            processed_at=datetime.now(timezone.utc),
        )

    async def refund(
        self,
        *,
        transaction: PaymentTransaction,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentProviderResult:
        return PaymentProviderResult(
            status=PaymentStatusEnum.SUCCEEDED,
            external_payment_id=f"stub_refund_{uuid4().hex[:12]}",
            response_payload={
                "provider": self.provider_name,
                "mode": "refund",
                "amount": str(amount),
                "currency": currency,
                "idempotency_key": idempotency_key,
                "parent_transaction_id": str(transaction.id),
            },
            processed_at=datetime.now(timezone.utc),
        )


class StubRedirectPaymentProvider:
    provider_name = "stub_redirect"

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
            final_status = "failed"
        elif "STAY_PENDING" in upper_comment:
            final_status = "pending"
        else:
            final_status = "succeeded"

        return PaymentProviderResult(
            status=PaymentStatusEnum.PENDING,
            external_payment_id=f"stub_redirect_{uuid4().hex[:12]}",
            redirect_url=f"https://stub-pay.local/intent/{uuid4().hex}",
            response_payload={
                "provider": self.provider_name,
                "mode": "redirect",
                "simulate_final_status": final_status,
                "idempotency_key": idempotency_key,
                "amount": str(amount),
                "currency": currency,
            },
        )

    async def check_status(
        self,
        *,
        transaction: PaymentTransaction,
    ) -> PaymentProviderResult:
        simulated = (transaction.response_payload or {}).get("simulate_final_status", "succeeded")
        if simulated == "failed":
            return PaymentProviderResult(
                status=PaymentStatusEnum.FAILED,
                external_payment_id=transaction.external_payment_id,
                redirect_url=transaction.redirect_url,
                failure_code="stub_redirect_failed",
                failure_reason="Redirect payment failed in stub provider.",
                response_payload={
                    **(transaction.response_payload or {}),
                    "checked_with": self.provider_name,
                    "mode": "redirect_failed",
                },
                processed_at=datetime.now(timezone.utc),
            )
        if simulated == "pending":
            return PaymentProviderResult(
                status=PaymentStatusEnum.PENDING,
                external_payment_id=transaction.external_payment_id,
                redirect_url=transaction.redirect_url,
                response_payload={
                    **(transaction.response_payload or {}),
                    "checked_with": self.provider_name,
                    "mode": "redirect_pending",
                },
            )
        return PaymentProviderResult(
            status=PaymentStatusEnum.SUCCEEDED,
            external_payment_id=transaction.external_payment_id,
            redirect_url=transaction.redirect_url,
            response_payload={
                **(transaction.response_payload or {}),
                "checked_with": self.provider_name,
                "mode": "redirect_succeeded",
            },
            processed_at=datetime.now(timezone.utc),
        )

    async def refund(
        self,
        *,
        transaction: PaymentTransaction,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentProviderResult:
        return PaymentProviderResult(
            status=PaymentStatusEnum.SUCCEEDED,
            external_payment_id=f"stub_redirect_refund_{uuid4().hex[:12]}",
            response_payload={
                "provider": self.provider_name,
                "mode": "refund",
                "amount": str(amount),
                "currency": currency,
                "idempotency_key": idempotency_key,
                "parent_transaction_id": str(transaction.id),
            },
            processed_at=datetime.now(timezone.utc),
        )


StubPaymentProvider = StubAutoApprovePaymentProvider


def get_payment_provider(provider_name: str | None = None) -> PaymentProvider:
    selected = (provider_name or setting.payment_provider).strip().lower()
    if selected in {"stub", "stub_auto"}:
        return StubAutoApprovePaymentProvider()
    if selected == "stub_redirect":
        return StubRedirectPaymentProvider()
    raise ValueError(f"Unsupported payment provider configured: {selected}")


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        provider: PaymentProvider | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.event_publisher = EventPublisher(session)

    async def create_checkout_payment(
        self,
        order: Order,
        *,
        provider_name: str | None = None,
        idempotency_key: str | None = None,
    ) -> PaymentTransaction:
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            raise ValueError("Order is already paid.")

        key = idempotency_key or f"checkout:{order.id}:{uuid4().hex}"
        existing = await self._get_by_idempotency_key(key)
        if existing:
            return existing

        provider = self._resolve_provider(provider_name)
        return await self._create_payment_transaction(
            order=order,
            provider=provider,
            operation_type="payment_intent",
            idempotency_key=key,
        )

    async def retry_payment(
        self,
        order: Order,
        *,
        provider_name: str | None = None,
        idempotency_key: str | None = None,
    ) -> PaymentTransaction:
        if order.payment_method != PaymentMethodEnum.CARD_ONLINE:
            raise ValueError("Payment retry is supported only for online card payments.")
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            raise ValueError("Order is already paid.")

        key = idempotency_key or f"retry:{order.id}:{uuid4().hex}"
        existing = await self._get_by_idempotency_key(key)
        if existing:
            return existing

        provider = self._resolve_provider(provider_name)
        return await self._create_payment_transaction(
            order=order,
            provider=provider,
            operation_type="retry_payment",
            idempotency_key=key,
        )

    async def check_order_payment_status(
        self,
        order: Order,
        *,
        idempotency_key: str | None = None,
    ) -> PaymentTransaction | None:
        latest_charge = await self._get_latest_charge_transaction(order)
        if latest_charge is None:
            return None

        key = idempotency_key or f"status-check:{latest_charge.id}:{uuid4().hex}"
        existing = await self._get_by_idempotency_key(key)
        if existing:
            return existing

        provider = self._resolve_provider(latest_charge.provider_name)
        previous_status = latest_charge.status
        result = await provider.check_status(transaction=latest_charge)
        status_log = PaymentTransaction(
            order_id=order.id,
            parent_transaction_id=latest_charge.id,
            provider_name=provider.provider_name,
            operation_type="status_check",
            payment_method=order.payment_method,
            status=result.status,
            amount=latest_charge.amount,
            currency=latest_charge.currency,
            idempotency_key=key,
            external_payment_id=latest_charge.external_payment_id,
            redirect_url=latest_charge.redirect_url,
            failure_code=result.failure_code,
            failure_reason=result.failure_reason,
            request_payload={"parent_transaction_id": str(latest_charge.id)},
            response_payload=result.response_payload,
            processed_at=result.processed_at,
        )
        self.session.add(status_log)

        latest_charge.status = result.status
        latest_charge.failure_code = result.failure_code
        latest_charge.failure_reason = result.failure_reason
        latest_charge.response_payload = result.response_payload
        latest_charge.processed_at = result.processed_at
        self._apply_payment_result(order, result.status)
        await self._publish_payment_status_events(
            order=order,
            transaction=latest_charge,
            previous_status=previous_status,
        )
        return status_log

    async def refund(
        self,
        order: Order,
        *,
        amount: Decimal | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> PaymentTransaction:
        charge = await self._get_latest_successful_charge(order)
        if charge is None:
            raise ValueError("Successful payment transaction was not found.")

        refundable_amount = order.total_amount - self.get_refunded_amount(order)
        refund_amount = (amount or refundable_amount).quantize(Decimal("0.01"))
        if refund_amount <= Decimal("0.00"):
            raise ValueError("Refund amount must be greater than zero.")
        if refund_amount > refundable_amount:
            raise ValueError("Refund amount exceeds remaining paid amount.")

        key = idempotency_key or f"refund:{order.id}:{uuid4().hex}"
        existing = await self._get_by_idempotency_key(key)
        if existing:
            return existing

        provider = self._resolve_provider(charge.provider_name)
        result = await provider.refund(
            transaction=charge,
            amount=refund_amount,
            currency=order.currency,
            idempotency_key=key,
        )
        refund_transaction = PaymentTransaction(
            order_id=order.id,
            parent_transaction_id=charge.id,
            provider_name=provider.provider_name,
            operation_type="refund",
            payment_method=order.payment_method,
            status=result.status,
            amount=refund_amount,
            currency=order.currency,
            idempotency_key=key,
            external_payment_id=result.external_payment_id,
            redirect_url=result.redirect_url,
            failure_code=result.failure_code,
            failure_reason=result.failure_reason,
            request_payload={"reason": reason or "", "parent_transaction_id": str(charge.id)},
            response_payload=result.response_payload,
            processed_at=result.processed_at,
        )
        self.session.add(refund_transaction)

        if result.status == PaymentStatusEnum.SUCCEEDED:
            refunded_total = self.get_refunded_amount(order) + refund_amount
            if refunded_total >= order.total_amount:
                order.payment_status = PaymentStatusEnum.REFUNDED
            else:
                order.payment_status = PaymentStatusEnum.PARTIALLY_REFUNDED
            await self.event_publisher.publish_domain(
                PaymentRefunded(
                    transaction_id=str(refund_transaction.id),
                    order_id=str(order.id),
                    provider_name=provider.provider_name,
                    amount=str(refund_amount),
                    currency=order.currency,
                )
            )

        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=provider.provider_name,
            status=result.status.value,
            method=order.payment_method.value,
        )
        return refund_transaction

    async def mark_offline_payment_succeeded(self, order: Order) -> PaymentTransaction | None:
        if order.payment_method not in {
            PaymentMethodEnum.CASH_ON_DELIVERY,
            PaymentMethodEnum.CARD_ON_DELIVERY,
        }:
            return None
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            return None

        latest_transaction = await self._get_latest_transaction(order)
        if latest_transaction is None:
            transaction = PaymentTransaction(
                order_id=order.id,
                provider_name=self._resolve_provider().provider_name,
                operation_type="offline_capture",
                payment_method=order.payment_method,
                status=PaymentStatusEnum.SUCCEEDED,
                amount=order.total_amount,
                currency=order.currency,
                idempotency_key=f"delivery:{order.id}:{uuid4().hex}",
                response_payload={"mode": "offline_completed"},
                processed_at=datetime.now(timezone.utc),
            )
            self.session.add(transaction)
            previous_status = None
        else:
            transaction = latest_transaction
            previous_status = transaction.status
            transaction.operation_type = "offline_capture"
            transaction.status = PaymentStatusEnum.SUCCEEDED
            transaction.failure_code = None
            transaction.failure_reason = None
            transaction.processed_at = datetime.now(timezone.utc)
            transaction.response_payload = {
                **(transaction.response_payload or {}),
                "mode": "offline_completed",
            }

        order.payment_status = PaymentStatusEnum.SUCCEEDED
        order.status = OrderStatusEnum.PAID if order.status == OrderStatusEnum.CREATED else order.status
        await self._publish_payment_status_events(
            order=order,
            transaction=transaction,
            previous_status=previous_status,
        )
        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=transaction.provider_name,
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

        transaction.operation_type = "cancel"
        transaction.status = PaymentStatusEnum.CANCELLED
        transaction.processed_at = datetime.now(timezone.utc)
        transaction.response_payload = {
            **(transaction.response_payload or {}),
            "mode": "cancelled",
        }
        order.payment_status = PaymentStatusEnum.CANCELLED
        order.status = OrderStatusEnum.CANCELLED
        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=transaction.provider_name,
            status=PaymentStatusEnum.CANCELLED.value,
            method=order.payment_method.value,
        )
        return transaction

    async def apply_webhook(
        self,
        *,
        provider_name: str,
        external_payment_id: str,
        status: PaymentStatusEnum,
    ) -> PaymentTransaction | None:
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.external_payment_id == external_payment_id)
            .order_by(PaymentTransaction.created_at.desc())
        )
        transaction = result.scalar_one_or_none()
        if transaction is None:
            return None

        payload = transaction.response_payload or {}
        if (
            transaction.operation_type == "webhook"
            and transaction.provider_name == provider_name
            and payload.get("webhook_status") == status.value
        ):
            return transaction

        transaction.provider_name = provider_name
        previous_status = transaction.status
        transaction.status = status
        transaction.operation_type = "webhook"
        transaction.processed_at = datetime.now(timezone.utc)
        transaction.response_payload = {
            **payload,
            "webhook_status": status.value,
        }
        self._apply_payment_result(transaction.order, status)
        await self._publish_payment_status_events(
            order=transaction.order,
            transaction=transaction,
            previous_status=previous_status,
            webhook_status=status,
        )
        return transaction

    def get_refunded_amount(self, order: Order) -> Decimal:
        total = Decimal("0.00")
        for transaction in order.payment_transactions:
            if transaction.operation_type == "refund" and transaction.status == PaymentStatusEnum.SUCCEEDED:
                total += transaction.amount
        return total.quantize(Decimal("0.01"))

    async def _create_payment_transaction(
        self,
        *,
        order: Order,
        provider: PaymentProvider,
        operation_type: str,
        idempotency_key: str,
    ) -> PaymentTransaction:
        provider_result = await provider.initiate_payment(
            order=order,
            amount=order.total_amount,
            currency=order.currency,
            idempotency_key=idempotency_key,
        )
        transaction = PaymentTransaction(
            order_id=order.id,
            provider_name=provider.provider_name,
            operation_type=operation_type,
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
        self._apply_payment_result(order, provider_result.status)
        await self._publish_payment_status_events(
            order=order,
            transaction=transaction,
            previous_status=None,
            include_created=True,
        )

        metrics_registry.increment(
            "shop_payment_transactions_total",
            provider=provider.provider_name,
            status=provider_result.status.value,
            method=order.payment_method.value,
        )
        logger.info(
            "payment_transaction_created",
            extra={
                "event": "payment_transaction_created",
                "order_id": str(order.id),
                "provider": provider.provider_name,
                "payment_status": provider_result.status.value,
                "payment_method": order.payment_method.value,
            },
        )
        return transaction

    def _apply_payment_result(self, order: Order, status: PaymentStatusEnum) -> None:
        order.payment_status = status
        if status == PaymentStatusEnum.SUCCEEDED:
            order.status = OrderStatusEnum.PAID
        elif status == PaymentStatusEnum.FAILED:
            order.status = OrderStatusEnum.FAILED
        elif status == PaymentStatusEnum.CANCELLED:
            order.status = OrderStatusEnum.CANCELLED
        elif status == PaymentStatusEnum.PENDING:
            order.status = (
                OrderStatusEnum.AWAITING_PAYMENT
                if order.payment_method == PaymentMethodEnum.CARD_ONLINE
                else OrderStatusEnum.CREATED
            )

    async def _get_by_idempotency_key(self, idempotency_key: str) -> PaymentTransaction | None:
        if not hasattr(self.session, "execute"):
            return None
        result = await self.session.execute(
            select(PaymentTransaction).where(PaymentTransaction.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def _get_latest_transaction(self, order: Order) -> PaymentTransaction | None:
        if order.payment_transactions:
            return order.payment_transactions[-1]
        if not hasattr(self.session, "execute"):
            return None
        result = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.order_id == order.id)
            .order_by(PaymentTransaction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_latest_charge_transaction(self, order: Order) -> PaymentTransaction | None:
        charges = [
            transaction
            for transaction in order.payment_transactions
            if transaction.operation_type in {"payment_intent", "retry_payment", "offline_capture", "webhook"}
        ]
        if charges:
            return charges[-1]
        if not hasattr(self.session, "execute"):
            return None

        result = await self.session.execute(
            select(PaymentTransaction)
            .where(
                PaymentTransaction.order_id == order.id,
                PaymentTransaction.operation_type.in_(["payment_intent", "retry_payment", "offline_capture", "webhook"]),
            )
            .order_by(PaymentTransaction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_latest_successful_charge(self, order: Order) -> PaymentTransaction | None:
        charge = await self._get_latest_charge_transaction(order)
        if charge and charge.status == PaymentStatusEnum.SUCCEEDED:
            return charge
        return None

    async def _publish_payment_status_events(
        self,
        *,
        order: Order,
        transaction: PaymentTransaction,
        previous_status: PaymentStatusEnum | None,
        include_created: bool = False,
        webhook_status: PaymentStatusEnum | None = None,
    ) -> None:
        if include_created:
            await self.event_publisher.publish_domain(
                PaymentCreated(
                    transaction_id=str(transaction.id),
                    order_id=str(order.id),
                    provider_name=transaction.provider_name,
                    operation_type=transaction.operation_type,
                    amount=str(transaction.amount),
                    currency=transaction.currency,
                )
            )

        status_changed = previous_status != transaction.status
        if transaction.status == PaymentStatusEnum.SUCCEEDED and (include_created or status_changed):
            await self.event_publisher.publish_domain(
                PaymentCaptured(
                    transaction_id=str(transaction.id),
                    order_id=str(order.id),
                    provider_name=transaction.provider_name,
                    amount=str(transaction.amount),
                    currency=transaction.currency,
                )
            )
        elif (
            transaction.status == PaymentStatusEnum.PENDING
            and order.payment_method == PaymentMethodEnum.CARD_ONLINE
            and (include_created or status_changed)
        ):
            await self.event_publisher.publish_domain(
                PaymentAuthorized(
                    transaction_id=str(transaction.id),
                    order_id=str(order.id),
                    provider_name=transaction.provider_name,
                    amount=str(transaction.amount),
                    currency=transaction.currency,
                )
            )
        elif transaction.status == PaymentStatusEnum.FAILED and (include_created or status_changed):
            await self.event_publisher.publish_domain(
                PaymentFailed(
                    transaction_id=str(transaction.id),
                    order_id=str(order.id),
                    provider_name=transaction.provider_name,
                    reason=transaction.failure_reason,
                )
            )

        if webhook_status is not None:
            await self.event_publisher.publish_domain(
                WebhookPaymentReceived(
                    transaction_id=str(transaction.id),
                    order_id=str(order.id),
                    provider_name=transaction.provider_name,
                    payment_status=webhook_status.value,
                )
            )

    def _resolve_provider(self, provider_name: str | None = None) -> PaymentProvider:
        if self.provider is not None and provider_name is None:
            return self.provider
        return get_payment_provider(provider_name)
