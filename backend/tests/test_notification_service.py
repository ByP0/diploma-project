from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
import unittest
from uuid import uuid4

from app.models.order import DeliveryMethodEnum, PaymentMethodEnum, PaymentStatusEnum
from app.models.support_ticket import SupportTicketStatusEnum
from app.services.email_service import EmailDeliveryResult
from app.services.notification_service import NotificationService


class FakeEmailService:
    def __init__(self) -> None:
        self.payloads = []

    async def send(self, payload):
        self.payloads.append(payload)
        return EmailDeliveryResult(success=True, provider="fake")


class NotificationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_order_created_notification_contains_checkout_details(self) -> None:
        email_service = FakeEmailService()
        service = NotificationService(email_service=email_service)
        order = SimpleNamespace(
            id=uuid4(),
            customer_email="buyer@example.com",
            customer_name="Иван",
            total_amount=Decimal("299.90"),
            currency="RUB",
            delivery_method=DeliveryMethodEnum.COURIER,
            payment_method=PaymentMethodEnum.CARD_ONLINE,
            delivery_address_line1="Ленинский проспект, 5",
            delivery_address_line2=None,
            delivery_city="Калининград",
            delivery_region="Калининградская область",
            delivery_postal_code="236000",
            delivery_country="RU",
            delivery_window_start=datetime(2026, 4, 25, 10, 0, tzinfo=timezone.utc),
            delivery_window_end=datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc),
        )
        payment = SimpleNamespace(
            status=PaymentStatusEnum.SUCCEEDED,
            provider_name="stub",
        )

        await service.send_order_created(order, payment)

        self.assertEqual(len(email_service.payloads), 1)
        self.assertIn("Заказ", email_service.payloads[0].subject)
        self.assertIn("Калининград", email_service.payloads[0].text_body)

    async def test_support_reply_notification_targets_ticket_email(self) -> None:
        email_service = FakeEmailService()
        service = NotificationService(email_service=email_service)
        ticket = SimpleNamespace(
            subject="Проблема с доставкой",
            contact_email="buyer@example.com",
            status=SupportTicketStatusEnum.WAITING_CUSTOMER,
        )
        reply = SimpleNamespace(body="Мы уже проверяем ваш заказ.")

        await service.send_support_reply(ticket, reply)

        self.assertEqual(email_service.payloads[0].recipients, ["buyer@example.com"])
        self.assertIn("Мы уже проверяем", email_service.payloads[0].text_body)
