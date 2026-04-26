from decimal import Decimal
from types import SimpleNamespace
import unittest
from uuid import uuid4

from app.models.order import OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.services.payment_service import PaymentService, StubPaymentProvider, StubRedirectPaymentProvider


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)


class PaymentServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_card_online_payment_is_auto_approved(self) -> None:
        session = FakeSession()
        order = SimpleNamespace(
            id=uuid4(),
            total_amount=Decimal("149.90"),
            payment_method=PaymentMethodEnum.CARD_ONLINE,
            payment_status=PaymentStatusEnum.PENDING,
            status=OrderStatusEnum.CREATED,
            currency="RUB",
            customer_comment=None,
            delivery_instructions=None,
            payment_transactions=[],
        )

        transaction = await PaymentService(session, provider=StubPaymentProvider()).create_checkout_payment(order)

        self.assertEqual(transaction.status, PaymentStatusEnum.SUCCEEDED)
        self.assertEqual(order.payment_status, PaymentStatusEnum.SUCCEEDED)
        self.assertEqual(order.status, OrderStatusEnum.PAID)
        self.assertTrue(session.added)

    async def test_stub_can_force_payment_failure(self) -> None:
        session = FakeSession()
        order = SimpleNamespace(
            id=uuid4(),
            total_amount=Decimal("149.90"),
            payment_method=PaymentMethodEnum.CARD_ONLINE,
            payment_status=PaymentStatusEnum.PENDING,
            status=OrderStatusEnum.CREATED,
            currency="RUB",
            customer_comment="FAIL_PAYMENT",
            delivery_instructions=None,
            payment_transactions=[],
        )

        transaction = await PaymentService(session, provider=StubPaymentProvider()).create_checkout_payment(order)

        self.assertEqual(transaction.status, PaymentStatusEnum.FAILED)
        self.assertEqual(order.payment_status, PaymentStatusEnum.FAILED)
        self.assertEqual(order.status, OrderStatusEnum.FAILED)

    async def test_offline_payment_stays_pending_until_delivery(self) -> None:
        session = FakeSession()
        order = SimpleNamespace(
            id=uuid4(),
            total_amount=Decimal("149.90"),
            payment_method=PaymentMethodEnum.CASH_ON_DELIVERY,
            payment_status=PaymentStatusEnum.PENDING,
            status=OrderStatusEnum.CREATED,
            currency="RUB",
            customer_comment=None,
            delivery_instructions=None,
            payment_transactions=[],
        )

        transaction = await PaymentService(session, provider=StubPaymentProvider()).create_checkout_payment(order)

        self.assertEqual(transaction.status, PaymentStatusEnum.PENDING)
        self.assertEqual(order.payment_status, PaymentStatusEnum.PENDING)
        self.assertEqual(order.status, OrderStatusEnum.CREATED)

    async def test_redirect_stub_creates_pending_payment_with_redirect_url(self) -> None:
        session = FakeSession()
        order = SimpleNamespace(
            id=uuid4(),
            total_amount=Decimal("149.90"),
            payment_method=PaymentMethodEnum.CARD_ONLINE,
            payment_status=PaymentStatusEnum.PENDING,
            status=OrderStatusEnum.CREATED,
            currency="RUB",
            customer_comment=None,
            delivery_instructions=None,
            payment_transactions=[],
        )

        transaction = await PaymentService(session, provider=StubRedirectPaymentProvider()).create_checkout_payment(order)

        self.assertEqual(transaction.status, PaymentStatusEnum.PENDING)
        self.assertIsNotNone(transaction.redirect_url)
        self.assertEqual(order.status, OrderStatusEnum.AWAITING_PAYMENT)
