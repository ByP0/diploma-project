from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, require_permissions
from app.core.permissions import PermissionEnum
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationMessageRead
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/messages",
    response_model=list[NotificationMessageRead],
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_NOTIFICATIONS))],
)
async def list_notification_messages(
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
):
    return await NotificationService(session).list_messages(limit=limit, status=status)


@router.post(
    "/process",
    response_model=MessageResponse,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_NOTIFICATIONS))],
)
async def process_notification_queue(session: SessionDep):
    processed = await NotificationService(session).process_queue(limit=100)
    return MessageResponse(detail=f"Processed {processed} notification(s).")
