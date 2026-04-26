from __future__ import annotations

from uuid import uuid4

from app.events.domain_events.notification_events import EmailSendRequested, SmsSendRequested
from app.events.domain_events.order_events import (
    OrderCancelled,
    OrderConfirmed,
    OrderCreated,
    OrderDelivered,
    OrderPacked,
    OrderPaid,
    OrderPaymentFailed,
    OrderProcessingStarted,
    OrderRefunded,
    OrderShipped,
)
from app.events.domain_events.user_events import UserBlocked, UserPasswordResetRequested, UserRegistered
from app.events.event_bus.base import EventContext
from app.models.notification_message import NotificationMessage


async def enqueue_email_request(event: EmailSendRequested, context: EventContext) -> None:
    message = NotificationMessage(
        channel="email",
        template_name=event.template_name,
        recipient=event.recipient,
        subject=event.subject,
        body_text=event.body_text,
        body_html=event.body_html,
        context_payload=event.context_payload,
        status="queued",
        attempts=0,
        max_attempts=event.max_attempts,
    )
    context.session.add(message)
    if hasattr(context.session, "flush"):
        await context.session.flush()


async def enqueue_sms_request(event: SmsSendRequested, context: EventContext) -> None:
    message = NotificationMessage(
        channel="sms",
        template_name="sms",
        recipient=event.recipient,
        subject="SMS notification",
        body_text=event.body_text,
        body_html=None,
        context_payload={"notification_key": event.notification_key},
        status="queued",
        attempts=0,
        max_attempts=3,
    )
    context.session.add(message)
    if hasattr(context.session, "flush"):
        await context.session.flush()


async def handle_user_registered(event: UserRegistered, context: EventContext) -> None:
    await _publish_email_request(
        context,
        template_name="welcome",
        recipient=event.email,
        subject="Welcome to the store",
        body_text="Your account has been created successfully.",
        body_html="<p>Your account has been created successfully.</p>",
        context_payload={"user_id": event.user_id},
    )


async def handle_user_password_reset_requested(event: UserPasswordResetRequested, context: EventContext) -> None:
    await _publish_email_request(
        context,
        template_name="password_reset",
        recipient=event.email,
        subject="Password reset request",
        body_text=(
            "A password reset request was created for your account.\n"
            f"Stub reset token: {event.reset_token}"
        ),
        body_html=(
            "<p>A password reset request was created for your account.</p>"
            f"<p><strong>Stub reset token:</strong> {event.reset_token}</p>"
        ),
        context_payload={"user_id": event.user_id},
    )


async def handle_user_blocked(event: UserBlocked, context: EventContext) -> None:
    await _publish_email_request(
        context,
        template_name="user_blocked",
        recipient=event.email,
        subject="Account access restricted",
        body_text=f"Your account has been blocked. Reason: {event.blocked_reason or 'Not specified'}",
        body_html=f"<p>Your account has been blocked.</p><p>Reason: {event.blocked_reason or 'Not specified'}</p>",
        context_payload={"user_id": event.user_id},
    )


async def handle_order_created(event: OrderCreated, context: EventContext) -> None:
    if not event.customer_email:
        return
    await _publish_email_request(
        context,
        template_name="order_created",
        recipient=event.customer_email,
        subject=f"Order {event.order_id} created",
        body_text=f"Your order {event.order_id} was created for {event.total_amount} {event.currency}.",
        body_html=(
            f"<p>Your order <strong>{event.order_id}</strong> was created "
            f"for <strong>{event.total_amount} {event.currency}</strong>.</p>"
        ),
        context_payload={"order_id": event.order_id},
    )


async def handle_order_confirmed(event: OrderConfirmed, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_confirmed",
        subject=f"Order {event.order_id} confirmed",
        body_text=f"The composition of order {event.order_id} has been confirmed.",
        body_html=f"<p>The composition of order <strong>{event.order_id}</strong> has been confirmed.</p>",
    )


async def handle_order_paid(event: OrderPaid, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_paid",
        subject=f"Order {event.order_id} paid",
        body_text=(
            f"Payment for order {event.order_id} was received.\n"
            f"Payment status: {event.payment_status}.\n"
            f"Total amount: {event.total_amount or 'n/a'} {event.currency or ''}".strip()
        ),
        body_html=(
            f"<p>Payment for order <strong>{event.order_id}</strong> was received.</p>"
            f"<p>Status: <strong>{event.payment_status}</strong>.</p>"
        ),
    )


async def handle_order_payment_failed(event: OrderPaymentFailed, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_payment_failed",
        subject=f"Payment failed for order {event.order_id}",
        body_text=(
            f"Payment for order {event.order_id} failed.\n"
            f"Reason: {event.reason or 'unknown'}."
        ),
        body_html=(
            f"<p>Payment for order <strong>{event.order_id}</strong> failed.</p>"
            f"<p>Reason: {event.reason or 'unknown'}.</p>"
        ),
    )


async def handle_order_processing_started(event: OrderProcessingStarted, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_processing_started",
        subject=f"Order {event.order_id} is being processed",
        body_text=f"Order {event.order_id} is now being processed.",
        body_html=f"<p>Order <strong>{event.order_id}</strong> is now being processed.</p>",
    )


async def handle_order_packed(event: OrderPacked, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_packed",
        subject=f"Order {event.order_id} packed",
        body_text=f"Order {event.order_id} has been packed and is awaiting shipment.",
        body_html=f"<p>Order <strong>{event.order_id}</strong> has been packed and is awaiting shipment.</p>",
    )


async def handle_order_cancelled(event: OrderCancelled, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_cancelled",
        subject=f"Order {event.order_id} cancelled",
        body_text=f"Order {event.order_id} was cancelled. Reason: {event.reason or 'not specified'}.",
        body_html=f"<p>Order <strong>{event.order_id}</strong> was cancelled.</p><p>Reason: {event.reason or 'not specified'}.</p>",
    )


async def handle_order_refunded(event: OrderRefunded, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_refunded",
        subject=f"Refund for order {event.order_id}",
        body_text=(
            f"Order {event.order_id} has been refunded.\n"
            f"Refund amount: {event.refunded_amount} {event.currency or ''}".strip()
        ),
        body_html=(
            f"<p>Order <strong>{event.order_id}</strong> has been refunded.</p>"
            f"<p>Refund amount: <strong>{event.refunded_amount} {event.currency or ''}</strong>.</p>"
        ),
    )


async def handle_order_shipped(event: OrderShipped, context: EventContext) -> None:
    tracking_line = f"\nTracking number: {event.tracking_number}" if event.tracking_number else ""
    tracking_html = f"<p>Tracking number: <strong>{event.tracking_number}</strong>.</p>" if event.tracking_number else ""
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_shipped",
        subject=f"Order {event.order_id} shipped",
        body_text=f"Order {event.order_id} has been shipped.{tracking_line}",
        body_html=f"<p>Order <strong>{event.order_id}</strong> has been shipped.</p>{tracking_html}",
    )


async def handle_order_delivered(event: OrderDelivered, context: EventContext) -> None:
    await _queue_order_status_email(
        event=event,
        context=context,
        template_name="order_delivered",
        subject=f"Order {event.order_id} delivered",
        body_text=f"Order {event.order_id} has been delivered.",
        body_html=f"<p>Order <strong>{event.order_id}</strong> has been delivered.</p>",
    )


async def _queue_order_status_email(
    *,
    event: OrderConfirmed
    | OrderPaid
    | OrderPaymentFailed
    | OrderProcessingStarted
    | OrderPacked
    | OrderCancelled
    | OrderRefunded
    | OrderShipped
    | OrderDelivered,
    context: EventContext,
    template_name: str,
    subject: str,
    body_text: str,
    body_html: str,
) -> None:
    customer_email = getattr(event, "customer_email", None)
    if not customer_email:
        return
    await _publish_email_request(
        context,
        template_name=template_name,
        recipient=customer_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        context_payload={"order_id": event.order_id},
    )


async def _publish_email_request(
    context: EventContext,
    *,
    template_name: str,
    recipient: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    context_payload: dict[str, str] | None = None,
    max_attempts: int = 3,
) -> None:
    await context.publisher.publish_domain(
        EmailSendRequested(
            notification_key=uuid4().hex,
            template_name=template_name,
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            context_payload=context_payload or {},
            max_attempts=max_attempts,
        )
    )
