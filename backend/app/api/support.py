from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from app.api.deps import CurrentAdmin, CurrentUser, SessionDep, require_permissions
from app.core.permissions import PermissionEnum
from app.api.docs import build_error_responses
from app.models.support_ticket import SupportTicketPriorityEnum, SupportTicketStatusEnum
from app.schemas.support import (
    SupportAdminReplyCreate,
    SupportTicketAdminUpdate,
    SupportTicketListResponse,
    SupportTicketRead,
)
from app.services.admin_audit_service import AdminAuditService
from app.services.support_service import SupportService


router = APIRouter(prefix="/support", tags=["Поддержка"])


@router.get(
    "/tickets",
    response_model=SupportTicketListResponse,
    dependencies=[Depends(require_permissions(PermissionEnum.HANDLE_SUPPORT))],
    summary="Получить обращения поддержки для администратора",
    responses=build_error_responses(401, 403, 422, 500),
)
async def list_support_tickets_admin(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: SupportTicketStatusEnum | None = Query(default=None),
    priority: SupportTicketPriorityEnum | None = Query(default=None),
    assigned_admin_id: UUID | None = Query(default=None),
    human_handoff_requested: bool | None = Query(default=None),
    search: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
):
    tickets = await SupportService(session).list_tickets_admin(
        limit=limit,
        offset=offset,
        status=status,
        priority=priority,
        assigned_admin_id=assigned_admin_id,
        human_handoff_requested=human_handoff_requested,
        search=search,
    )
    return SupportTicketListResponse(items=tickets)


@router.get(
    "/tickets/admin/{ticket_id}",
    response_model=SupportTicketRead,
    dependencies=[Depends(require_permissions(PermissionEnum.HANDLE_SUPPORT))],
    summary="Получить детали обращения поддержки для администратора",
    responses=build_error_responses(401, 403, 404, 422, 500),
)
async def get_support_ticket_admin(
    ticket_id: Annotated[UUID, Path(description="Идентификатор обращения поддержки")],
    session: SessionDep,
):
    ticket = await SupportService(session).get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Обращение поддержки не найдено.")
    return ticket


@router.get(
    "/tickets/me",
    response_model=SupportTicketListResponse,
    summary="Получить обращения текущего пользователя",
    responses=build_error_responses(401, 422, 500),
)
async def get_my_support_tickets(
    session: SessionDep,
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    tickets = await SupportService(session).list_tickets_for_user(
        current_user.id,
        limit=limit,
        offset=offset,
    )
    return SupportTicketListResponse(items=tickets)


@router.get(
    "/tickets/me/{ticket_id}",
    response_model=SupportTicketRead,
    summary="Получить детали обращения",
    responses=build_error_responses(401, 404, 422, 500),
)
async def get_my_support_ticket(
    ticket_id: Annotated[UUID, Path(description="Идентификатор обращения поддержки")],
    session: SessionDep,
    current_user: CurrentUser,
):
    ticket = await SupportService(session).get_ticket_for_user(current_user.id, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Обращение поддержки не найдено.")
    return ticket


@router.post(
    "/tickets/{ticket_id}/admin-reply",
    response_model=SupportTicketRead,
    summary="Ответить на обращение от лица администратора",
    responses=build_error_responses(400, 401, 403, 404, 422, 500),
)
async def reply_to_support_ticket(
    ticket_id: Annotated[UUID, Path(description="Идентификатор обращения поддержки")],
    data: SupportAdminReplyCreate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = SupportService(session)
    try:
        ticket = await service.reply_as_admin(
            ticket_id=ticket_id,
            admin_user=current_admin,
            message=data.message,
            status=data.status,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "не найдено" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="reply",
        resource_type="support_ticket",
        resource_id=str(ticket_id),
        status_code=200,
        details={"status": ticket.status.value},
    )
    return ticket


@router.patch(
    "/tickets/{ticket_id}",
    response_model=SupportTicketRead,
    summary="Обновить обращение поддержки",
    responses=build_error_responses(400, 401, 403, 404, 422, 500),
)
async def update_support_ticket(
    ticket_id: Annotated[UUID, Path(description="Идентификатор обращения поддержки")],
    data: SupportTicketAdminUpdate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = SupportService(session)
    try:
        ticket = await service.update_ticket(
            ticket_id=ticket_id,
            status=data.status,
            priority=data.priority,
            assigned_admin_id=data.assigned_admin_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "не найдено" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="update",
        resource_type="support_ticket",
        resource_id=str(ticket_id),
        status_code=200,
        details={
            "status": ticket.status.value,
            "priority": ticket.priority.value,
        },
    )
    return ticket
