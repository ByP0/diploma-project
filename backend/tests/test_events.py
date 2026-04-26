import unittest

from app.events.domain_events import SmsSendRequested, StockChanged, UserRegistered
from app.events.outbox.models import OutboxMessage
from app.events.publishers.event_publisher import EventPublisher
from app.events.schemas import event_from_envelope
from app.models.notification_message import NotificationMessage


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        return None


class EventLayerTests(unittest.IsolatedAsyncioTestCase):
    async def test_user_registered_event_queues_email_and_broker_messages(self) -> None:
        session = FakeSession()
        publisher = EventPublisher(session)

        await publisher.publish_domain(
            UserRegistered(
                user_id="user-1",
                email="buyer@example.com",
                name="Ivan",
                role="user",
            )
        )

        outbox_messages = [item for item in session.added if isinstance(item, OutboxMessage)]
        notification_messages = [item for item in session.added if isinstance(item, NotificationMessage)]

        self.assertEqual(len(outbox_messages), 4)
        self.assertEqual(len(notification_messages), 1)
        self.assertEqual(notification_messages[0].template_name, "welcome")
        self.assertEqual(notification_messages[0].recipient, "buyer@example.com")

        local_messages = [item for item in outbox_messages if item.destination == "local"]
        broker_messages = [item for item in outbox_messages if item.destination == "broker"]
        self.assertEqual({item.event_name for item in local_messages}, {"UserRegistered", "EmailSendRequested"})
        self.assertEqual({item.event_name for item in broker_messages}, {"AnalyticsSyncRequested", "CRMUserSyncRequested"})
        self.assertTrue(all(item.status == "processed" for item in local_messages))
        self.assertTrue(all(item.status == "pending" for item in broker_messages))

    async def test_low_stock_event_creates_admin_alert_in_outbox(self) -> None:
        session = FakeSession()
        publisher = EventPublisher(session)

        await publisher.publish_domain(
            StockChanged(
                product_id="product-1",
                stock=4,
                reserved_stock=0,
                available_stock=4,
                reason="manual_adjustment",
            )
        )

        outbox_messages = [item for item in session.added if isinstance(item, OutboxMessage)]
        self.assertEqual(len(outbox_messages), 3)
        self.assertEqual(
            {item.event_name for item in outbox_messages if item.destination == "local"},
            {"StockChanged", "LowStockDetected"},
        )
        self.assertEqual(
            {item.event_name for item in outbox_messages if item.destination == "broker"},
            {"AdminAlertRequested"},
        )

    async def test_sms_send_requested_queues_sms_notification(self) -> None:
        session = FakeSession()
        publisher = EventPublisher(session)

        await publisher.publish_domain(
            SmsSendRequested(
                notification_key="sms-1",
                recipient="+79990000000",
                body_text="Order shipped.",
            )
        )

        notification_messages = [item for item in session.added if isinstance(item, NotificationMessage)]
        self.assertEqual(len(notification_messages), 1)
        self.assertEqual(notification_messages[0].channel, "sms")
        self.assertEqual(notification_messages[0].recipient, "+79990000000")

    def test_event_can_be_rebuilt_from_envelope(self) -> None:
        event = UserRegistered(
            user_id="user-1",
            email="buyer@example.com",
            name="Ivan",
            role="user",
        )

        restored_event = event_from_envelope(event.to_envelope())

        self.assertIsInstance(restored_event, UserRegistered)
        self.assertEqual(restored_event.user_id, "user-1")
        self.assertEqual(restored_event.email, "buyer@example.com")
