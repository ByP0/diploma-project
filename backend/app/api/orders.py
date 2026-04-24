from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request, status

from app.api.docs import build_error_responses
from app.api.deps import CurrentAdmin, CurrentUser, SessionDep
from app.schemas.order import OrderCheckoutCreate, OrderRead, OrderStatusUpdate
from app.services.admin_audit_service import AdminAuditService
from app.services.order_service import OrderService


router = APIRouter(prefix="/orders", tags=["Заказы"])


@router.post(
    "/from-cart",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заказ из корзины",
    description="Оформляет заказ на основе текущей корзины пользователя с полными checkout-данными.",
    responses=build_error_responses(400, 401, 422, 500),
)
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


@router.post(
    "/{order_id}/payments/retry",
    response_model=OrderRead,
    summary="Повторить оплату заказа",
    description="Переинициализирует платёжную транзакцию для заказа с online payment flow.",
    responses=build_error_responses(400, 401, 404, 422, 500),
)
async def retry_order_payment(
    order_id: Annotated[
        UUID,
        Path(description="Идентификатор заказа"),
    ],
    session: SessionDep,
    current_user: CurrentUser,
):
    service = OrderService(session)
    try:
        order = await service.retry_payment(current_user.id, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден.")

    return order


@router.get(
    "",
    response_model=list[OrderRead],
    summary="Получить историю заказов",
    description="Возвращает историю заказов текущего пользователя с пагинацией.",
    responses=build_error_responses(401, 422, 500),
)
async def get_order_history(
    session: SessionDep,
    current_user: CurrentUser,
    limit: Annotated[
        int,
        Query(
            title="Лимит",
            description="Максимальное количество заказов в ответе",
            ge=1,
            le=100,
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            title="Смещение",
            description="Количество заказов, которое нужно пропустить",
            ge=0,
        ),
    ] = 0,
):
    service = OrderService(session)
    return await service.get_history(current_user.id, limit=limit, offset=offset)


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Получить заказ по идентификатору",
    description="Возвращает детальную информацию по одному заказу текущего пользователя.",
    responses=build_error_responses(401, 404, 422, 500),
)
async def get_order_by_id(
    order_id: Annotated[
        UUID,
        Path(
            title="Идентификатор заказа",
            description="Идентификатор заказа",
        ),
    ],
    session: SessionDep,
    current_user: CurrentUser,
):
    service = OrderService(session)
    order = await service.get_by_id_for_user(current_user.id, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден.")

    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Изменить статус заказа",
    description="Обновляет статус заказа. Доступно только администратору.",
    responses=build_error_responses(400, 401, 403, 404, 422, 500),
)
async def update_order_status(
    order_id: Annotated[
        UUID,
        Path(
            title="Идентификатор заказа",
            description="Идентификатор заказа для обновления статуса",
        ),
    ],
    data: OrderStatusUpdate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = OrderService(session)
    try:
        order = await service.update_status(order_id=order_id, status=data.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден.")

    audit_service = AdminAuditService(session)
    await audit_service.record(
        request=request,
        admin_user=current_admin,
        action="update_status",
        resource_type="order",
        resource_id=str(order.id),
        status_code=200,
        details={"status": order.status.value, "payment_status": order.payment_status.value},
    )

    return order
