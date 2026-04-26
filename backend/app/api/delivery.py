from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path, Request

from app.api.deps import CurrentUser, SessionDep
from app.core.config import setting
from app.core.webhooks import verify_webhook_request
from app.schemas.common import MessageResponse
from app.schemas.delivery import (
    DeliveryAddressCreate,
    DeliveryAddressRead,
    DeliveryAddressUpdate,
    DeliveryQuoteRead,
    DeliveryQuoteRequest,
    DeliveryWebhookPayload,
)
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/delivery", tags=["Delivery"])


@router.post("/quote", response_model=DeliveryQuoteRead)
async def calculate_delivery_quote(data: DeliveryQuoteRequest, session: SessionDep):
    quote = await DeliveryService(session).calculate_quote(
        delivery_method=data.delivery_method,
        city=data.city,
        region=data.region,
        country=data.country,
        order_amount=data.order_amount,
    )
    return DeliveryQuoteRead(
        provider_name=quote.provider_name,
        delivery_method=quote.delivery_method,
        cost=quote.cost,
        currency=quote.currency,
        estimated_days=quote.estimated_days,
        details=quote.details,
    )


@router.get("/addresses", response_model=list[DeliveryAddressRead])
async def list_delivery_addresses(session: SessionDep, current_user: CurrentUser):
    return await DeliveryService(session).list_addresses(user_id=current_user.id)


@router.post("/addresses", response_model=DeliveryAddressRead)
async def create_delivery_address(data: DeliveryAddressCreate, session: SessionDep, current_user: CurrentUser):
    return await DeliveryService(session).create_address(
        user_id=current_user.id,
        data=data.model_dump(),
    )


@router.patch("/addresses/{address_id}", response_model=DeliveryAddressRead)
async def update_delivery_address(
    address_id: Annotated[UUID, Path()],
    data: DeliveryAddressUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    address = await DeliveryService(session).update_address(
        user_id=current_user.id,
        address_id=address_id,
        data=data.model_dump(exclude_unset=True),
    )
    if not address:
        raise HTTPException(status_code=404, detail="Delivery address was not found.")
    return address


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_delivery_address(
    address_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
):
    deleted = await DeliveryService(session).delete_address(user_id=current_user.id, address_id=address_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Delivery address was not found.")
    return MessageResponse(detail="Delivery address deleted.")


@router.post("/webhooks/{provider_name}", response_model=MessageResponse)
async def delivery_webhook(
    provider_name: str,
    payload: DeliveryWebhookPayload,
    request: Request,
    session: SessionDep,
    x_webhook_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
):
    await verify_webhook_request(
        request=request,
        signature=x_webhook_signature,
        secret=setting.delivery_webhook_secret,
    )
    shipment = await DeliveryService(session).apply_webhook(
        provider_name=provider_name,
        external_delivery_id=payload.external_delivery_id,
        tracking_number=payload.tracking_number,
        status=payload.status,
        delivered=payload.delivered,
    )
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment was not found.")
    return MessageResponse(detail="Delivery webhook processed.")
