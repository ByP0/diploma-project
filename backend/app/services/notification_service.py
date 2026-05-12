from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.domain_events import NotificationFailed, NotificationSent
from app.events.publishers.event_publisher import EventPublisher
from app.models.notification_message import NotificationMessage
from app.models.order import Order
from app.models.payment_transaction import PaymentTransaction
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services.email_service import EmailPayload, EmailService


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        session: AsyncSession | None = None,
        email_service: EmailService | None = None,
    ) -> None:
        self.session = session
        self.email_service = email_service or EmailService()
        self.event_publisher = EventPublisher(session) if session is not None else None

    async def list_messages(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        channel: str | None = None,
        template_name: str | None = None,
        recipient: str | None = None,
    ) -> list[NotificationMessage]:
        if self.session is None:
            return []
        statement = select(NotificationMessage)

        if status:
            statement = statement.where(NotificationMessage.status == status)
        if channel:
            statement = statement.where(NotificationMessage.channel == channel)
        if template_name:
            statement = statement.where(NotificationMessage.template_name == template_name.strip())
        if recipient:
            pattern = f"%{recipient.strip()}%"
            statement = statement.where(
                or_(
                    NotificationMessage.recipient.ilike(pattern),
                    NotificationMessage.subject.ilike(pattern),
                )
            )

        statement = statement.order_by(NotificationMessage.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def process_queue(self, *, limit: int = 50) -> int:
        if self.session is None:
            return 0
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(NotificationMessage)
            .where(
                NotificationMessage.status.in_(["queued", "retrying"]),
                (NotificationMessage.next_retry_at.is_(None) | (NotificationMessage.next_retry_at <= now)),
            )
            .order_by(NotificationMessage.created_at.asc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        for message in messages:
            if message.channel == "sms":
                await self._deliver_sms_message(message)
            else:
                payload = EmailPayload(
                    subject=message.subject,
                    recipients=[message.recipient],
                    template_name=message.template_name,
                    text_body=message.body_text,
                    html_body=message.body_html,
                )
                await self._deliver_message(message, payload)
            await self._publish_delivery_result(message)
        await self.session.commit()
        return len(messages)

    async def send_registration_welcome(self, user: User) -> NotificationMessage | object:
        return await self._send_email(
            EmailPayload(
                subject="Welcome to the store",
                recipients=[user.email],
                template_name="welcome",
                text_body=(
                    "Your account has been created successfully.\n"
                    "You can now sign in, create carts and place orders."
                ),
                html_body=(
                    "<p>Your account has been created successfully.</p>"
                    "<p>You can now sign in, create carts and place orders.</p>"
                ),
            )
        )

    async def send_password_reset_requested(self, user: User, raw_token: str) -> NotificationMessage | object:
        return await self._send_email(
            EmailPayload(
                subject="Password reset request",
                recipients=[user.email],
                template_name="password_reset",
                text_body=(
                    "A password reset request was created for your account.\n"
                    f"Stub reset token: {raw_token}\n"
                    "Use the /auth/password/reset endpoint to complete the reset."
                ),
                html_body=(
                    "<p>A password reset request was created for your account.</p>"
                    f"<p><strong>Stub reset token:</strong> {raw_token}</p>"
                    "<p>Use the <code>/auth/password/reset</code> endpoint to complete the reset.</p>"
                ),
            ),
            context_payload={"user_id": str(user.id)},
        )

    async def send_email_verification_stub(self, user: User, raw_token: str) -> NotificationMessage | object:
        return await self._send_email(
            EmailPayload(
                subject="Email verification is available as a stub",
                recipients=[user.email],
                template_name="email_verification_stub",
                text_body=(
                    "Email verification is present in the backend as a stub and is currently disabled.\n"
                    f"Stub verification token: {raw_token}"
                ),
                html_body=(
                    "<p>Email verification is present in the backend as a stub and is currently disabled.</p>"
                    f"<p><strong>Stub verification token:</strong> {raw_token}</p>"
                ),
            ),
            context_payload={"user_id": str(user.id)},
        )

    async def send_order_created(
        self,
        order: Order,
        latest_payment: PaymentTransaction | None = None,
    ) -> NotificationMessage | object | None:
        if not order.customer_email:
            return None

        payment_block = ""
        if latest_payment:
            payment_block = (
                f"\nPayment status: {latest_payment.status.value}\n"
                f"Provider: {latest_payment.provider_name}\n"
            )
        window_block = self._format_delivery_window(order)
        address_block = self._format_address(order)

        return await self._send_email(
            EmailPayload(
                subject=f"Order {order.id} created",
                recipients=[order.customer_email],
                template_name="order_created",
                text_body=(
                    f"Hello, {order.customer_name or 'customer'}.\n\n"
                    f"Your order {order.id} was created for {order.total_amount} {order.currency}.\n"
                    f"Delivery method: {order.delivery_method.value}\n"
                    f"Payment method: {order.payment_method.value}\n"
                    f"{address_block}"
                    f"{window_block}"
                    f"{payment_block}"
                ),
                html_body=(
                    f"<p>Hello, {order.customer_name or 'customer'}.</p>"
                    f"<p>Your order <strong>{order.id}</strong> was created for "
                    f"<strong>{order.total_amount} {order.currency}</strong>.</p>"
                    f"<p>Delivery method: <strong>{order.delivery_method.value}</strong><br>"
                    f"Payment method: <strong>{order.payment_method.value}</strong></p>"
                    f"<p>{address_block.replace(chr(10), '<br>')}{window_block.replace(chr(10), '<br>')}"
                    f"{payment_block.replace(chr(10), '<br>')}</p>"
                ),
            ),
            context_payload={"order_id": str(order.id)},
        )

    async def send_order_status_updated(self, order: Order) -> NotificationMessage | object | None:
        if not order.customer_email:
            return None

        return await self._send_email(
            EmailPayload(
                subject=f"Order {order.id} status updated",
                recipients=[order.customer_email],
                template_name="order_status_updated",
                text_body=(
                    f"Hello, {order.customer_name or 'customer'}.\n\n"
                    f"New order status: {order.status.value}\n"
                    f"Payment status: {order.payment_status.value}\n"
                ),
                html_body=(
                    f"<p>Hello, {order.customer_name or 'customer'}.</p>"
                    f"<p>New order status: <strong>{order.status.value}</strong>.</p>"
                    f"<p>Payment status: <strong>{order.payment_status.value}</strong>.</p>"
                ),
            ),
            context_payload={"order_id": str(order.id)},
        )

    async def send_support_reply(self, ticket: SupportTicket, reply: SupportMessage) -> NotificationMessage | object | None:
        if not ticket.contact_email:
            return None

        return await self._send_email(
            EmailPayload(
                subject=f"Reply for ticket {ticket.subject}",
                recipients=[ticket.contact_email],
                template_name="support_reply",
                text_body=(
                    "There is a new support reply.\n\n"
                    f"{reply.body}\n\n"
                    f"Current ticket status: {ticket.status.value}"
                ),
                html_body=(
                    "<p>There is a new support reply.</p>"
                    f"<blockquote>{reply.body}</blockquote>"
                    f"<p>Current ticket status: <strong>{ticket.status.value}</strong></p>"
                ),
            ),
            context_payload={"ticket_id": str(getattr(ticket, "id", ""))},
        )

    async def _send_email(
        self,
        payload: EmailPayload,
        *,
        context_payload: dict[str, str] | None = None,
        max_attempts: int = 3,
    ) -> NotificationMessage | object:
        if self.session is None:
            return await self.email_service.send(payload)

        message = NotificationMessage(
            channel="email",
            template_name=payload.template_name,
            recipient=payload.recipients[0],
            subject=payload.subject,
            body_text=payload.text_body,
            body_html=payload.html_body,
            context_payload=context_payload or {},
            status="queued",
            attempts=0,
            max_attempts=max_attempts,
        )
        self.session.add(message)
        if hasattr(self.session, "flush"):
            await self.session.flush()
        await self._deliver_message(message, payload)
        await self._publish_delivery_result(message)
        await self.session.commit()
        return message

    async def _deliver_message(self, message: NotificationMessage, payload: EmailPayload) -> None:
        try:
            result = await self.email_service.send(payload)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.exception("notification_delivery_failed: %s", exc)
            message.attempts += 1
            message.last_error = str(exc)
            message.provider_name = self.email_service.provider_name
            if message.attempts >= message.max_attempts:
                message.status = "failed"
                message.next_retry_at = None
            else:
                message.status = "retrying"
                message.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * message.attempts)
            return

        message.attempts += 1
        message.provider_name = result.provider
        if result.success:
            message.status = "sent"
            message.sent_at = datetime.now(timezone.utc)
            message.last_error = None
            message.next_retry_at = None
        else:
            message.last_error = result.error
            if message.attempts >= message.max_attempts:
                message.status = "failed"
                message.next_retry_at = None
            else:
                message.status = "retrying"
                message.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * message.attempts)

    async def _deliver_sms_message(self, message: NotificationMessage) -> None:
        message.attempts += 1
        message.provider_name = "stub_sms"
        if message.recipient and message.body_text:
            message.status = "sent"
            message.sent_at = datetime.now(timezone.utc)
            message.last_error = None
            message.next_retry_at = None
            return

        message.last_error = "SMS recipient and body are required."
        if message.attempts >= message.max_attempts:
            message.status = "failed"
            message.next_retry_at = None
        else:
            message.status = "retrying"
            message.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * message.attempts)

    @staticmethod
    def _format_delivery_window(order: Order) -> str:
        if not order.delivery_window_start or not order.delivery_window_end:
            return ""
        start = order.delivery_window_start.isoformat(timespec="minutes")
        end = order.delivery_window_end.isoformat(timespec="minutes")
        return f"\nDelivery window: {start} - {end}\n"

    @staticmethod
    def _format_address(order: Order) -> str:
        parts = [
            order.delivery_address_line1,
            order.delivery_address_line2,
            order.delivery_city,
            order.delivery_region,
            order.delivery_postal_code,
            order.delivery_country,
        ]
        address = ", ".join(part for part in parts if part)
        if not address:
            return ""
        return f"\nDelivery address: {address}\n"

    async def _publish_delivery_result(self, message: NotificationMessage) -> None:
        if self.event_publisher is None:
            return
        if message.status == "sent":
            await self.event_publisher.publish_domain(
                NotificationSent(
                    notification_id=str(message.id),
                    channel=message.channel,
                    template_name=message.template_name,
                    recipient=message.recipient,
                    provider_name=message.provider_name or self.email_service.provider_name,
                )
            )
        elif message.status == "failed":
            await self.event_publisher.publish_domain(
                NotificationFailed(
                    notification_id=str(message.id),
                    channel=message.channel,
                    template_name=message.template_name,
                    recipient=message.recipient,
                    error=message.last_error,
                )
            )
