from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.api.docs import build_error_responses, message_response
from app.api.deps import CurrentUser, SessionDep
from app.schemas.common import MessageResponse
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.cart_service import CartService


router = APIRouter(prefix="/cart", tags=["Корзина"])


@router.get(
    "",
    response_model=CartRead,
    summary="Получить корзину",
    description="Возвращает текущее содержимое корзины авторизованного пользователя.",
    responses=build_error_responses(401, 500),
)
async def get_cart(
    session: SessionDep,
    current_user: CurrentUser,
):
    service = CartService(session)
    return await service.get_cart(current_user.id)


@router.post(
    "/items",
    response_model=CartRead,
    summary="Добавить товар в корзину",
    description="Добавляет товар в корзину пользователя или увеличивает его количество.",
    responses=build_error_responses(400, 401, 422, 500),
)
async def add_to_cart(
    data: CartItemCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    service = CartService(session)

    try:
        return await service.add_item(
            user_id=current_user.id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put(
    "/items/{product_id}",
    response_model=CartRead,
    summary="Изменить количество товара в корзине",
    description="Обновляет количество выбранного товара в корзине пользователя.",
    responses=build_error_responses(400, 401, 422, 500),
)
async def update_cart_item(
    product_id: Annotated[
        UUID,
        Path(
            title="Идентификатор товара",
            description="Идентификатор товара в корзине",
        ),
    ],
    data: CartItemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    service = CartService(session)

    try:
        return await service.update_item(
            user_id=current_user.id,
            product_id=product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete(
    "/items/{product_id}",
    response_model=MessageResponse,
    summary="Удалить товар из корзины",
    description="Удаляет конкретный товар из корзины пользователя.",
    responses={
        **build_error_responses(401, 404, 422, 500),
        200: message_response("Товар успешно удален из корзины."),
    },
)
async def remove_cart_item(
    product_id: Annotated[
        UUID,
        Path(
            title="Идентификатор товара",
            description="Идентификатор товара, который нужно удалить из корзины",
        ),
    ],
    session: SessionDep,
    current_user: CurrentUser,
):
    service = CartService(session)
    removed = await service.remove_item(current_user.id, product_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Позиция корзины не найдена.")

    return MessageResponse(detail="Товар успешно удален из корзины.")


@router.delete(
    "",
    response_model=MessageResponse,
    summary="Очистить корзину",
    description="Удаляет все товары из корзины текущего пользователя.",
    responses={
        **build_error_responses(401, 500),
        200: message_response("Корзина успешно очищена."),
    },
)
async def clear_cart(
    session: SessionDep,
    current_user: CurrentUser,
):
    service = CartService(session)
    await service.clear(current_user.id)
    return MessageResponse(detail="Корзина успешно очищена.")
