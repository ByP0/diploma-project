from datetime import datetime, timedelta, timezone
import unittest

from pydantic import ValidationError

from app.models.order import DeliveryMethodEnum, PaymentMethodEnum
from app.schemas.order import OrderCheckoutCreate


class OrderCheckoutSchemaTests(unittest.TestCase):
    def test_courier_checkout_requires_address(self) -> None:
        with self.assertRaises(ValidationError):
            OrderCheckoutCreate(
                customer_name="Иван Иванов",
                customer_phone="+79990000000",
                delivery_method=DeliveryMethodEnum.COURIER,
                payment_method=PaymentMethodEnum.CARD_ONLINE,
            )

    def test_pickup_checkout_does_not_require_address(self) -> None:
        payload = OrderCheckoutCreate(
            customer_name="Иван Иванов",
            customer_phone="+79990000000",
            delivery_method=DeliveryMethodEnum.PICKUP,
            payment_method=PaymentMethodEnum.CARD_ONLINE,
        )
        self.assertEqual(payload.delivery_method, DeliveryMethodEnum.PICKUP)

    def test_delivery_window_must_be_valid(self) -> None:
        start = datetime.now(timezone.utc)
        end = start - timedelta(hours=1)

        with self.assertRaises(ValidationError):
            OrderCheckoutCreate(
                customer_name="Иван Иванов",
                customer_phone="+79990000000",
                delivery_method=DeliveryMethodEnum.COURIER,
                payment_method=PaymentMethodEnum.CARD_ONLINE,
                delivery_address_line1="Улица Пушкина, 1",
                delivery_city="Калининград",
                delivery_window_start=start,
                delivery_window_end=end,
            )
