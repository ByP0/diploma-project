from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, Request
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentUser, SessionDep
from app.core.config import setting
from app.core.webhooks import verify_webhook_request
from app.models.order import PaymentStatusEnum
from app.schemas.common import MessageResponse
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentWebhookPayload(BaseModel):
    external_payment_id: str = Field(min_length=3, max_length=255)
    status: PaymentStatusEnum

    model_config = ConfigDict(extra="forbid")


@router.post("/orders/{order_id}/recheck")
async def recheck_payment_status(
    order_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
):
    order = await OrderService(session).sync_payment_status(
        order_id=order_id,
        user_id=current_user.id,
        actor_user=current_user,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.post("/webhooks/{provider_name}", response_model=MessageResponse)
async def payment_webhook(
    provider_name: str,
    payload: PaymentWebhookPayload,
    request: Request,
    session: SessionDep,
    x_webhook_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
):
    await verify_webhook_request(
        request=request,
        signature=x_webhook_signature,
        secret=setting.payment_webhook_secret,
    )
    transaction = await PaymentService(session).apply_webhook(
        provider_name=provider_name,
        external_payment_id=payload.external_payment_id,
        status=payload.status,
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment transaction was not found.")
    await session.commit()
    return MessageResponse(detail="Payment webhook processed.")
