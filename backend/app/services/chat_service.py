from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import setting
from app.models.order import Order
from app.models.product import Product
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.services.support_service import SupportService

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - optional dependency fallback
    AsyncOpenAI = None


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatResult:
    answer: str
    used_ai: bool
    used_user_context: bool
    ticket: SupportTicket


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.support_service = SupportService(session)
        self.client = (
            AsyncOpenAI(api_key=setting.openai_api_key)
            if setting.openai_api_key and AsyncOpenAI
            else None
        )

    async def answer(
        self,
        *,
        message: str,
        user: User | None,
        ticket_id: UUID | None = None,
        contact_email: str | None = None,
        request_human: bool = False,
    ) -> ChatResult:
        human_handoff_requested = request_human or self._requires_human_operator(message)
        ticket = await self.support_service.get_or_create_ticket_for_chat(
            message=message,
            user=user,
            ticket_id=ticket_id,
            contact_email=contact_email,
            human_handoff_requested=human_handoff_requested,
        )
        self.support_service.add_customer_message(ticket=ticket, message=message, user=user)

        context = await self._build_context(user)
        has_user_context = bool(context.get("orders"))

        used_ai = False
        answer: str
        if self.client:
            try:
                answer = await self._answer_with_openai(
                    message=message,
                    context=context,
                    user=user,
                    human_handoff_requested=human_handoff_requested,
                )
                used_ai = True
            except Exception as exc:  # pragma: no cover - defensive runtime logging
                logger.exception("OpenAI support response failed: %s", exc)
                answer = self._fallback_answer(
                    message=message,
                    context=context,
                    user=user,
                    human_handoff_requested=human_handoff_requested,
                )
        else:
            answer = self._fallback_answer(
                message=message,
                context=context,
                user=user,
                human_handoff_requested=human_handoff_requested,
            )

        self.support_service.add_ai_message(
            ticket=ticket,
            message=answer,
            used_ai=used_ai,
        )
        if human_handoff_requested:
            saved_ticket = await self.support_service.mark_handoff_requested(ticket)
        else:
            saved_ticket = await self.support_service.commit_ticket(ticket)

        return ChatResult(
            answer=answer,
            used_ai=used_ai,
            used_user_context=has_user_context,
            ticket=saved_ticket,
        )

    async def _build_context(self, user: User | None) -> dict[str, Any]:
        products_result = await self.session.execute(
            select(Product)
            .where(Product.is_active.is_(True))
            .order_by(Product.created_at.desc())
            .limit(10)
        )
        products = products_result.scalars().all()

        orders = []
        if user:
            orders_result = await self.session.execute(
                select(Order)
                .where(Order.user_id == user.id)
                .options(selectinload(Order.items))
                .order_by(Order.created_at.desc())
                .limit(5)
            )
            orders = orders_result.scalars().all()

        return {
            "products": [
                {
                    "id": str(product.id),
                    "sku": product.sku,
                    "name": product.name,
                    "brand": product.brand,
                    "price": str(product.price),
                    "unit": product.unit.value,
                    "stock": product.stock,
                    "category_id": product.category_id,
                }
                for product in products
            ],
            "orders": [
                {
                    "id": str(order.id),
                    "status": order.status.value,
                    "total_amount": str(order.total_amount),
                    "created_at": order.created_at.isoformat(),
                    "items": [
                        {
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "line_total": str(item.line_total),
                        }
                        for item in order.items
                    ],
                }
                for order in orders
            ],
        }

    async def _answer_with_openai(
        self,
        *,
        message: str,
        context: dict[str, Any],
        user: User | None,
        human_handoff_requested: bool,
    ) -> str:
        user_state = "авторизованный пользователь" if user else "анонимный пользователь"
        system_prompt = (
            "Ты бот поддержки интернет-магазина продуктовых товаров. "
            "Отвечай только на русском языке. "
            "Пиши коротко, вежливо и по делу. "
            "Используй только переданный контекст. "
            "Если данных недостаточно, прямо скажи об этом и предложи следующий шаг. "
            "Если пользователь просит оператора или ситуация выглядит спорной, "
            "подтверди передачу обращения человеку."
        )

        response = await self.client.responses.create(
            model=setting.openai_model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"User state: {user_state}\n"
                                f"Human handoff requested: {human_handoff_requested}\n"
                                f"Контекст каталога и заказов:\n{context}\n\n"
                                f"Вопрос пользователя:\n{message}"
                            ),
                        }
                    ],
                },
            ],
            temperature=0.2,
        )

        output_text = getattr(response, "output_text", None)
        if output_text:
            answer = output_text.strip()
        else:
            answer = "Не удалось получить ответ от ИИ. Попробуйте повторить запрос позже."

        if human_handoff_requested:
            answer = self._append_handoff_note(answer)

        return answer

    def _fallback_answer(
        self,
        *,
        message: str,
        context: dict[str, Any],
        user: User | None,
        human_handoff_requested: bool,
    ) -> str:
        lower_message = message.lower()
        products = context.get("products", [])
        orders = context.get("orders", [])
        order_keywords = ("order", "заказ", "заказы", "статус")
        product_keywords = (
            "product",
            "catalog",
            "item",
            "товар",
            "товары",
            "продукт",
            "продукты",
            "каталог",
            "наличии",
            "ассортимент",
        )

        if any(keyword in lower_message for keyword in order_keywords) and not user:
            answer = "Чтобы посмотреть информацию по заказам, пожалуйста, войдите в аккаунт."
            return self._append_handoff_note(answer) if human_handoff_requested else answer

        if any(keyword in lower_message for keyword in order_keywords) and user:
            if not orders:
                answer = "У вас пока нет заказов. Могу помочь подобрать товары из каталога."
                return self._append_handoff_note(answer) if human_handoff_requested else answer

            latest_order = orders[0]
            answer = (
                f"Ваш последний заказ: {latest_order['id']}. "
                f"Статус: {latest_order['status']}. "
                f"Сумма: {latest_order['total_amount']}."
            )
            return self._append_handoff_note(answer) if human_handoff_requested else answer

        if any(keyword in lower_message for keyword in product_keywords):
            if not products:
                answer = "Сейчас каталог пуст. Попробуйте обновить запрос позже."
                return self._append_handoff_note(answer) if human_handoff_requested else answer

            shortlist = ", ".join(
                f"{item['name']} ({item['price']} за {item['unit']})"
                for item in products[:3]
            )
            answer = f"Сейчас в наличии, например: {shortlist}."
            return self._append_handoff_note(answer) if human_handoff_requested else answer

        answer = (
            "Я могу помочь с каталогом, корзиной и заказами. "
            "Например, спросите: «Что есть в наличии?» или «Какой статус моего заказа?»."
        )
        return self._append_handoff_note(answer) if human_handoff_requested else answer

    def _requires_human_operator(self, message: str) -> bool:
        lowered = message.lower()
        escalation_keywords = (
            "оператор",
            "администратор",
            "человек",
            "жалоба",
            "претенз",
            "возврат",
            "проблем",
            "списали деньги",
        )
        return any(keyword in lowered for keyword in escalation_keywords)

    def _append_handoff_note(self, answer: str) -> str:
        return (
            f"{answer}\n\n"
            "Я также отметил обращение для оператора поддержки, чтобы его мог обработать администратор."
        )
