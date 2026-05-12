import hashlib
import hmac
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
import unittest
from uuid import uuid4

from fastapi import HTTPException

from app.core.config import setting
from app.core.webhooks import verify_webhook_signature
from app.models.order import OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.services.payment_service import PaymentService


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeQuerySession:
    def __init__(self, value):
        self.value = value
        self.added = []

    async def execute(self, _statement):
        return FakeScalarResult(self.value)

    def add(self, value):
        self.added.append(value)


class WebhookSecurityTests(unittest.IsolatedAsyncioTestCase):
    def test_webhook_signature_accepts_hmac_sha256(self) -> None:
        body = b'{"external_payment_id":"pay_1","status":"succeeded"}'
        secret = "webhook-secret"
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

        verify_webhook_signature(body=body, signature=f"sha256={signature}", secret=secret)

    def test_webhook_signature_rejects_invalid_signature(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            verify_webhook_signature(body=b"{}", signature="sha256=bad", secret="webhook-secret")

        self.assertEqual(exc.exception.status_code, 401)

    def test_webhook_signature_allows_missing_secret_locally(self) -> None:
        original_environment = setting.environment
        setting.environment = "local"
        try:
            verify_webhook_signature(body=b"{}", signature=None, secret=None)
        finally:
            setting.environment = original_environment

    def test_webhook_signature_rejects_missing_secret_outside_local(self) -> None:
        original_environment = setting.environment
        setting.environment = "production"
        try:
            with self.assertRaises(HTTPException) as exc:
                verify_webhook_signature(body=b"{}", signature=None, secret=None)
        finally:
            setting.environment = original_environment

        self.assertEqual(exc.exception.status_code, 503)

    async def test_duplicate_payment_webhook_is_noop(self) -> None:
        processed_at = datetime.now(timezone.utc)
        order = SimpleNamespace(
            id=uuid4(),
            payment_method=PaymentMethodEnum.CARD_ONLINE,
            payment_status=PaymentStatusEnum.SUCCEEDED,
            status=OrderStatusEnum.PAID,
            currency="RUB",
        )
        transaction = SimpleNamespace(
            id=uuid4(),
            order=order,
            order_id=order.id,
            provider_name="stub",
            operation_type="webhook",
            status=PaymentStatusEnum.SUCCEEDED,
            amount=Decimal("100.00"),
            currency="RUB",
            response_payload={"webhook_status": PaymentStatusEnum.SUCCEEDED.value},
            external_payment_id="pay_1",
            processed_at=processed_at,
        )
        session = FakeQuerySession(transaction)

        result = await PaymentService(session).apply_webhook(
            provider_name="stub",
            external_payment_id="pay_1",
            status=PaymentStatusEnum.SUCCEEDED,
        )

        self.assertIs(result, transaction)
        self.assertEqual(transaction.processed_at, processed_at)
        self.assertEqual(session.added, [])
