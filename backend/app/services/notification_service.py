from __future__ import annotations

import logging
from datetime import datetime

from app.models.order import Order
from app.models.payment_transaction import PaymentTransaction
from app.models.support_message import SupportMessage
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services.email_service import EmailPayload, EmailService


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, email_service: EmailService | None = None) -> None:
        self.email_service = email_service or EmailService()

    async def send_registration_welcome(self, user: User) -> None:
        await self.email_service.send(
            EmailPayload(
                subject="Добро пожаловать в магазин",
                recipients=[user.email],
                template_name="welcome",
                text_body=(
                    "Здравствуйте!\n\n"
                    "Ваш аккаунт успешно создан. Теперь вы можете оформлять заказы и получать уведомления по e-mail.\n"
                ),
                html_body=(
                    "<p>Здравствуйте!</p>"
                    "<p>Ваш аккаунт успешно создан. Теперь вы можете оформлять заказы и получать уведомления по e-mail.</p>"
                ),
            )
        )

    async def send_order_created(
        self,
        order: Order,
        latest_payment: PaymentTransaction | None = None,
    ) -> None:
        recipient = order.customer_email
        if not recipient:
            return

        payment_block = ""
        if latest_payment:
            payment_block = (
                f"\nСтатус оплаты: {latest_payment.status.value}\n"
                f"Провайдер: {latest_payment.provider_name}\n"
            )
        window_block = self._format_delivery_window(order)
        address_block = self._format_address(order)

        await self.email_service.send(
            EmailPayload(
                subject=f"Заказ {order.id} создан",
                recipients=[recipient],
                template_name="order_created",
                text_body=(
                    f"Здравствуйте, {order.customer_name or 'покупатель'}!\n\n"
                    f"Мы приняли ваш заказ {order.id} на сумму {order.total_amount} {order.currency}.\n"
                    f"Способ доставки: {order.delivery_method.value}\n"
                    f"Способ оплаты: {order.payment_method.value}\n"
                    f"{address_block}"
                    f"{window_block}"
                    f"{payment_block}"
                ),
                html_body=(
                    f"<p>Здравствуйте, {order.customer_name or 'покупатель'}!</p>"
                    f"<p>Мы приняли ваш заказ <strong>{order.id}</strong> на сумму "
                    f"<strong>{order.total_amount} {order.currency}</strong>.</p>"
                    f"<p>Способ доставки: <strong>{order.delivery_method.value}</strong><br>"
                    f"Способ оплаты: <strong>{order.payment_method.value}</strong></p>"
                    f"<p>{address_block.replace(chr(10), '<br>')}{window_block.replace(chr(10), '<br>')}"
                    f"{payment_block.replace(chr(10), '<br>')}</p>"
                ),
            )
        )

    async def send_order_status_updated(self, order: Order) -> None:
        recipient = order.customer_email
        if not recipient:
            return

        await self.email_service.send(
            EmailPayload(
                subject=f"Статус заказа {order.id} обновлён",
                recipients=[recipient],
                template_name="order_status_updated",
                text_body=(
                    f"Здравствуйте, {order.customer_name or 'покупатель'}!\n\n"
                    f"Новый статус вашего заказа {order.id}: {order.status.value}.\n"
                    f"Статус оплаты: {order.payment_status.value}.\n"
                ),
                html_body=(
                    f"<p>Здравствуйте, {order.customer_name or 'покупатель'}!</p>"
                    f"<p>Новый статус вашего заказа <strong>{order.id}</strong>: "
                    f"<strong>{order.status.value}</strong>.</p>"
                    f"<p>Статус оплаты: <strong>{order.payment_status.value}</strong>.</p>"
                ),
            )
        )

    async def send_support_reply(self, ticket: SupportTicket, reply: SupportMessage) -> None:
        if not ticket.contact_email:
            return

        await self.email_service.send(
            EmailPayload(
                subject=f"Ответ по обращению {ticket.subject}",
                recipients=[ticket.contact_email],
                template_name="support_reply",
                text_body=(
                    f"Здравствуйте!\n\n"
                    f"По вашему обращению «{ticket.subject}» появился новый ответ.\n\n"
                    f"{reply.body}\n\n"
                    f"Текущий статус обращения: {ticket.status.value}\n"
                ),
                html_body=(
                    f"<p>Здравствуйте!</p>"
                    f"<p>По вашему обращению <strong>{ticket.subject}</strong> появился новый ответ.</p>"
                    f"<blockquote>{reply.body}</blockquote>"
                    f"<p>Текущий статус обращения: <strong>{ticket.status.value}</strong></p>"
                ),
            )
        )

    @staticmethod
    def _format_delivery_window(order: Order) -> str:
        if not order.delivery_window_start or not order.delivery_window_end:
            return ""
        start = NotificationService._format_dt(order.delivery_window_start)
        end = NotificationService._format_dt(order.delivery_window_end)
        return f"\nОкно доставки: {start} - {end}\n"

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
        return f"\nАдрес доставки: {address}\n"

    @staticmethod
    def _format_dt(value: datetime) -> str:
        return value.isoformat(timespec="minutes")
