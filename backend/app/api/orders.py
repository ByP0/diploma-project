from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request, status

from app.api.deps import CurrentUser, SessionDep, require_permissions
from app.core.permissions import PermissionEnum
from app.schemas.cart import CartRead
from app.schemas.order import (
    OrderCancelRequest,
    OrderCheckoutCreate,
    OrderDocumentRead,
    OrderRead,
    OrderRefundRequest,
    OrderStatusUpdate,
)
from app.services.admin_audit_service import AdminAuditService
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/from-cart", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order_from_cart(
    data: OrderCheckoutCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    service = OrderService(session)
    try:
        return await service.create_from_cart(current_user, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/payments/retry", response_model=OrderRead)
async def retry_order_payment(
    order_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    service = OrderService(session)
    try:
        order = await service.retry_payment(
            current_user.id,
            order_id,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.post("/{order_id}/payments/sync", response_model=OrderRead)
async def sync_order_payment(
    order_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    order = await OrderService(session).sync_payment_status(
        order_id=order_id,
        user_id=current_user.id,
        actor_user=current_user,
        idempotency_key=idempotency_key,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.get("", response_model=list[OrderRead])
async def get_order_history(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await OrderService(session).get_history(current_user.id, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_by_id(
    order_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
):
    order = await OrderService(session).get_by_id_for_user(current_user.id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: Annotated[UUID, Path()],
    data: OrderCancelRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        order = await OrderService(session).cancel_order(
            order_id=order_id,
            user_id=current_user.id,
            actor_user=current_user,
            reason=data.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.post("/{order_id}/refund", response_model=OrderRead)
async def refund_order(
    order_id: Annotated[UUID, Path()],
    data: OrderRefundRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        order = await OrderService(session).refund_order(
            order_id=order_id,
            data=data,
            user_id=current_user.id,
            actor_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.post("/{order_id}/repeat", response_model=CartRead)
async def repeat_order(
    order_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        cart = await OrderService(session).reorder(user=current_user, order_id=order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not cart:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return cart


@router.get("/{order_id}/documents/{document_type}", response_model=OrderDocumentRead)
async def get_order_document(
    order_id: Annotated[UUID, Path()],
    document_type: Annotated[str, Path(pattern="^(invoice|receipt)$")],
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        document = await OrderService(session).build_document(
            order_id=order_id,
            document_type=document_type,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not document:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return document


@router.get(
    "/management/list",
    response_model=list[OrderRead],
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_ORDERS))],
)
async def list_orders_admin(
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return await OrderService(session).list_all(limit=limit, offset=offset)


@router.get(
    "/management/{order_id}",
    response_model=OrderRead,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_ORDERS))],
)
async def get_order_admin(order_id: Annotated[UUID, Path()], session: SessionDep):
    order = await OrderService(session).get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_ORDERS))],
)
async def update_order_status(
    order_id: Annotated[UUID, Path()],
    data: OrderStatusUpdate,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        order = await OrderService(session).update_status(
            order_id=order_id,
            status=data.status,
            actor_user=current_user,
            reason=data.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    await AdminAuditService(session).record(
        request=request,
        admin_user=current_user,
        action="update_status",
        resource_type="order",
        resource_id=str(order.id),
        status_code=200,
        details={"status": order.status.value, "reason": data.reason},
    )
    return order


@router.post(
    "/management/{order_id}/cancel",
    response_model=OrderRead,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_ORDERS))],
)
async def cancel_order_admin(
    order_id: Annotated[UUID, Path()],
    data: OrderCancelRequest,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        order = await OrderService(session).cancel_order(
            order_id=order_id,
            actor_user=current_user,
            reason=data.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Order was not found.")
    await AdminAuditService(session).record(
        request=request,
        admin_user=current_user,
        action="cancel",
        resource_type="order",
        resource_id=str(order.id),
        status_code=200,
        details={"reason": data.reason},
    )
    return order
