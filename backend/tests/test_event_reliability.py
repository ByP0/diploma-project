import unittest
from uuid import uuid4

from sqlalchemy import UniqueConstraint

from app.events.inbox.models import InboxMessage
from app.events.inbox.service import InboxService
from app.events.outbox.models import OutboxMessage
from app.events.outbox.service import OutboxService


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeInboxSession:
    def __init__(self) -> None:
        self.existing = None
        self.added = []

    async def execute(self, _statement):
        return FakeScalarResult(self.existing)

    def add(self, value):
        self.added.append(value)
        self.existing = value

    async def flush(self):
        return None


class EventReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_outbox_failure_moves_to_dead_letter_after_max_attempts(self) -> None:
        message = OutboxMessage(
            event_id=uuid4(),
            event_name="OrderCreated",
            event_kind="domain",
            aggregate_type="order",
            aggregate_id="order-1",
            version=1,
            payload={},
            status="processing",
            destination="broker",
            attempts=1,
            max_attempts=2,
        )

        should_retry = await OutboxService(session=object()).mark_failed(message, "broker unavailable")

        self.assertFalse(should_retry)
        self.assertEqual(message.status, "dead_letter")
        self.assertIsNotNone(message.dead_lettered_at)
        self.assertEqual(message.last_error, "broker unavailable")

    async def test_inbox_deduplicates_processed_event_for_consumer(self) -> None:
        event_id = uuid4()
        session = FakeInboxSession()
        service = InboxService(session)

        message = await service.acquire(
            event_id=event_id,
            event_name="AnalyticsSyncRequested",
            source="shop.AnalyticsSyncRequested",
            consumer_name="analytics-worker",
            payload={"event_id": str(event_id)},
            correlation_id="corr-1",
        )
        self.assertIsNotNone(message)

        await service.mark_processed(message)
        duplicate = await service.acquire(
            event_id=event_id,
            event_name="AnalyticsSyncRequested",
            source="shop.AnalyticsSyncRequested",
            consumer_name="analytics-worker",
            payload={"event_id": str(event_id)},
            correlation_id="corr-1",
        )

        self.assertIsNone(duplicate)

    def test_inbox_uniqueness_is_scoped_by_consumer_name(self) -> None:
        unique_constraints = [
            constraint
            for constraint in InboxMessage.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        ]

        self.assertIn(
            ("event_id", "consumer_name"),
            {tuple(constraint.columns.keys()) for constraint in unique_constraints},
        )
