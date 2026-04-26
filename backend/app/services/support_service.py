from __future__ import annotations

from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.support_message import SupportMessage, SupportMessageAuthorEnum
from app.models.support_ticket import (
    SupportTicket,
    SupportTicketPriorityEnum,
    SupportTicketStatusEnum,
)
from app.models.user import User
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService


SUPPORT_STATUS_TRANSITIONS: dict[
    SupportTicketStatusEnum,
    set[SupportTicketStatusEnum],
] = {
    SupportTicketStatusEnum.OPEN: {
        SupportTicketStatusEnum.IN_PROGRESS,
        SupportTicketStatusEnum.WAITING_CUSTOMER,
        SupportTicketStatusEnum.RESOLVED,
        SupportTicketStatusEnum.CLOSED,
    },
    SupportTicketStatusEnum.IN_PROGRESS: {
        SupportTicketStatusEnum.OPEN,
        SupportTicketStatusEnum.WAITING_CUSTOMER,
        SupportTicketStatusEnum.RESOLVED,
        SupportTicketStatusEnum.CLOSED,
    },
    SupportTicketStatusEnum.WAITING_CUSTOMER: {
        SupportTicketStatusEnum.OPEN,
        SupportTicketStatusEnum.IN_PROGRESS,
        SupportTicketStatusEnum.RESOLVED,
        SupportTicketStatusEnum.CLOSED,
    },
    SupportTicketStatusEnum.RESOLVED: {
        SupportTicketStatusEnum.IN_PROGRESS,
        SupportTicketStatusEnum.CLOSED,
    },
    SupportTicketStatusEnum.CLOSED: {
        SupportTicketStatusEnum.IN_PROGRESS,
    },
}


logger = logging.getLogger(__name__)


class SupportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService(session)
        self.alert_service = AlertService()

    async def get_or_create_ticket_for_chat(
        self,
        *,
        message: str,
        user: User | None,
        ticket_id: UUID | None,
        contact_email: str | None,
        human_handoff_requested: bool,
    ) -> SupportTicket:
        if ticket_id:
            ticket = await self.get_ticket_for_chat(
                ticket_id=ticket_id,
                user=user,
                contact_email=contact_email,
            )
            if not ticket:
                raise ValueError("Обращение поддержки не найдено.")
            return ticket

        ticket = SupportTicket(
            user_id=user.id if user else None,
            contact_email=contact_email or (user.email if user else None),
            subject=self._build_subject(message),
            status=SupportTicketStatusEnum.OPEN,
            priority=self._infer_priority(message, human_handoff_requested),
            human_handoff_requested=human_handoff_requested,
            ai_last_used=False,
            last_message_preview=self._build_preview(message),
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def get_ticket_for_chat(
        self,
        *,
        ticket_id: UUID,
        user: User | None,
        contact_email: str | None,
    ) -> SupportTicket | None:
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            return None

        if user and ticket.user_id == user.id:
            return ticket

        if not user and contact_email and ticket.contact_email == contact_email:
            return ticket

        return None

    async def get_ticket_by_id(self, ticket_id: UUID) -> SupportTicket | None:
        result = await self.session.execute(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(selectinload(SupportTicket.messages))
        )
        return result.scalar_one_or_none()

    async def get_ticket_for_user(self, user_id: UUID, ticket_id: UUID) -> SupportTicket | None:
        result = await self.session.execute(
            select(SupportTicket)
            .where(
                SupportTicket.id == ticket_id,
                SupportTicket.user_id == user_id,
            )
            .options(selectinload(SupportTicket.messages))
        )
        return result.scalar_one_or_none()

    async def list_tickets_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(
                SupportTicket.updated_at.desc(),
                SupportTicket.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    def add_customer_message(
        self,
        *,
        ticket: SupportTicket,
        message: str,
        user: User | None,
    ) -> SupportMessage:
        now = datetime.now(timezone.utc)
        support_message = SupportMessage(
            ticket_id=ticket.id,
            author_type=SupportMessageAuthorEnum.CUSTOMER,
            author_user_id=user.id if user else None,
            author_name=user.email if user else ticket.contact_email,
            body=message,
        )
        self.session.add(support_message)

        ticket.last_customer_message_at = now
        ticket.last_message_preview = self._build_preview(message)
        if ticket.status in {
            SupportTicketStatusEnum.WAITING_CUSTOMER,
            SupportTicketStatusEnum.RESOLVED,
            SupportTicketStatusEnum.CLOSED,
        }:
            ticket.status = (
                SupportTicketStatusEnum.IN_PROGRESS
                if ticket.assigned_admin_id
                else SupportTicketStatusEnum.OPEN
            )

        return support_message

    def add_ai_message(
        self,
        *,
        ticket: SupportTicket,
        message: str,
        used_ai: bool,
    ) -> SupportMessage:
        support_message = SupportMessage(
            ticket_id=ticket.id,
            author_type=SupportMessageAuthorEnum.AI,
            author_name="AI Support Bot",
            body=message,
        )
        self.session.add(support_message)
        ticket.ai_last_used = used_ai
        return support_message

    async def mark_handoff_requested(self, ticket: SupportTicket) -> SupportTicket:
        ticket.human_handoff_requested = True
        if ticket.status == SupportTicketStatusEnum.RESOLVED:
            ticket.status = SupportTicketStatusEnum.IN_PROGRESS
        elif ticket.status == SupportTicketStatusEnum.CLOSED:
            ticket.status = SupportTicketStatusEnum.OPEN

        await self.session.commit()
        reloaded_ticket = await self._reload_ticket(ticket.id)
        await self.alert_service.notify(
            kind="support_handoff_requested",
            severity="warning",
            message="Покупатель запросил подключение оператора поддержки.",
            context={
                "ticket_id": str(reloaded_ticket.id),
                "contact_email": reloaded_ticket.contact_email or "",
                "subject": reloaded_ticket.subject,
            },
        )
        return reloaded_ticket

    async def reply_as_admin(
        self,
        *,
        ticket_id: UUID,
        admin_user: User,
        message: str,
        status: SupportTicketStatusEnum | None = None,
    ) -> SupportTicket:
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError("Обращение поддержки не найдено.")

        now = datetime.now(timezone.utc)
        reply_status = status or SupportTicketStatusEnum.WAITING_CUSTOMER
        self._validate_transition(ticket.status, reply_status)

        support_message = SupportMessage(
            ticket_id=ticket.id,
            author_type=SupportMessageAuthorEnum.ADMIN,
            author_user_id=admin_user.id,
            author_name=admin_user.email,
            body=message.strip(),
        )
        self.session.add(support_message)

        ticket.assigned_admin_id = admin_user.id
        ticket.human_handoff_requested = False
        ticket.status = reply_status
        ticket.last_admin_reply_at = now
        ticket.last_message_preview = self._build_preview(message)

        await self.session.commit()
        reloaded_ticket = await self._reload_ticket(ticket.id)
        try:
            latest_reply = reloaded_ticket.messages[-1]
            await self.notification_service.send_support_reply(reloaded_ticket, latest_reply)
        except Exception as exc:  # pragma: no cover - defensive notification guard
            logger.exception("Support reply notification failed: %s", exc)
            await self.alert_service.notify(
                kind="support_reply_notification_failed",
                severity="warning",
                message="Не удалось отправить e-mail по ответу службы поддержки.",
                context={"ticket_id": str(reloaded_ticket.id)},
            )
        return reloaded_ticket

    async def update_ticket(
        self,
        *,
        ticket_id: UUID,
        status: SupportTicketStatusEnum | None = None,
        priority: SupportTicketPriorityEnum | None = None,
        assigned_admin_id: UUID | None = None,
    ) -> SupportTicket:
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError("Обращение поддержки не найдено.")

        if status and status != ticket.status:
            self._validate_transition(ticket.status, status)
            ticket.status = status

        if priority is not None:
            ticket.priority = priority

        if assigned_admin_id is not None:
            ticket.assigned_admin_id = assigned_admin_id

        await self.session.commit()
        return await self._reload_ticket(ticket.id)

    async def commit_ticket(self, ticket: SupportTicket) -> SupportTicket:
        await self.session.commit()
        return await self._reload_ticket(ticket.id)

    async def get_recent_active_tickets(self, *, limit: int = 20) -> list[SupportTicket]:
        result = await self.session.execute(
            select(SupportTicket)
            .where(
                SupportTicket.status.in_(
                    [
                        SupportTicketStatusEnum.OPEN,
                        SupportTicketStatusEnum.IN_PROGRESS,
                        SupportTicketStatusEnum.WAITING_CUSTOMER,
                    ]
                )
            )
            .order_by(
                SupportTicket.human_handoff_requested.desc(),
                SupportTicket.updated_at.desc(),
            )
            .limit(limit)
            .options(selectinload(SupportTicket.messages))
        )
        return list(result.scalars().unique().all())

    async def get_ticket_counts(self) -> dict[str, int]:
        active_tickets = await self.get_recent_active_tickets(limit=1000)
        return {
            "total_open": sum(
                1
                for ticket in active_tickets
                if ticket.status == SupportTicketStatusEnum.OPEN
            ),
            "in_progress": sum(
                1
                for ticket in active_tickets
                if ticket.status == SupportTicketStatusEnum.IN_PROGRESS
            ),
            "waiting_customer": sum(
                1
                for ticket in active_tickets
                if ticket.status == SupportTicketStatusEnum.WAITING_CUSTOMER
            ),
            "handoff_requested": sum(
                1 for ticket in active_tickets if ticket.human_handoff_requested
            ),
        }

    async def _reload_ticket(self, ticket_id: UUID) -> SupportTicket:
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError("Не удалось повторно загрузить обращение поддержки.")
        return ticket

    def _build_subject(self, message: str) -> str:
        normalized = " ".join(message.split())
        return normalized[:200] or "Обращение в поддержку"

    def _build_preview(self, message: str) -> str:
        return " ".join(message.split())[:280]

    def _infer_priority(
        self,
        message: str,
        human_handoff_requested: bool,
    ) -> SupportTicketPriorityEnum:
        lowered = message.lower()
        urgent_keywords = (
            "жалоб",
            "претенз",
            "возврат",
            "списали",
            "не привезли",
            "не пришел",
            "ошибка оплаты",
        )
        if any(keyword in lowered for keyword in urgent_keywords):
            return SupportTicketPriorityEnum.HIGH
        if human_handoff_requested:
            return SupportTicketPriorityEnum.NORMAL
        return SupportTicketPriorityEnum.LOW

    def _validate_transition(
        self,
        current_status: SupportTicketStatusEnum,
        next_status: SupportTicketStatusEnum,
    ) -> None:
        if next_status == current_status:
            return

        allowed = SUPPORT_STATUS_TRANSITIONS.get(current_status, set())
        if next_status not in allowed:
            raise ValueError(
                f"Нельзя перевести обращение из статуса '{current_status.value}' "
                f"в '{next_status.value}'."
            )
