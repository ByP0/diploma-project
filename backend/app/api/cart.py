from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from app.api.deps import CurrentUser, SessionDep
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead, GuestCartSessionRead
from app.schemas.common import MessageResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/guest/sessions", response_model=GuestCartSessionRead)
async def create_guest_cart_session(session: SessionDep):
    return await CartService(session).create_guest_cart_session()


@router.get("", response_model=CartRead)
async def get_cart(session: SessionDep, current_user: CurrentUser):
    return await CartService(session).get_cart(user_id=current_user.id)


@router.post("/items", response_model=CartRead)
async def add_to_cart(data: CartItemCreate, session: SessionDep, current_user: CurrentUser):
    try:
        return await CartService(session).add_item(
            user_id=current_user.id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/items/{product_id}", response_model=CartRead)
async def update_cart_item(
    product_id: Annotated[UUID, Path()],
    data: CartItemUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        return await CartService(session).update_item(
            user_id=current_user.id,
            product_id=product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/items/{product_id}", response_model=MessageResponse)
async def remove_cart_item(
    product_id: Annotated[UUID, Path()],
    session: SessionDep,
    current_user: CurrentUser,
):
    removed = await CartService(session).remove_item(
        user_id=current_user.id,
        product_id=product_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Cart item was not found.")
    return MessageResponse(detail="Cart item removed.")


@router.delete("", response_model=MessageResponse)
async def clear_cart(session: SessionDep, current_user: CurrentUser):
    await CartService(session).clear(user_id=current_user.id)
    return MessageResponse(detail="Cart cleared.")


@router.get("/guest/{guest_cart_id}", response_model=CartRead)
async def get_guest_cart(guest_cart_id: str, session: SessionDep):
    return await CartService(session).get_cart(guest_cart_id=guest_cart_id)


@router.post("/guest/{guest_cart_id}/items", response_model=CartRead)
async def add_to_guest_cart(guest_cart_id: str, data: CartItemCreate, session: SessionDep):
    try:
        return await CartService(session).add_item(
            guest_cart_id=guest_cart_id,
            product_id=data.product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/guest/{guest_cart_id}/items/{product_id}", response_model=CartRead)
async def update_guest_cart_item(
    guest_cart_id: str,
    product_id: Annotated[UUID, Path()],
    data: CartItemUpdate,
    session: SessionDep,
):
    try:
        return await CartService(session).update_item(
            guest_cart_id=guest_cart_id,
            product_id=product_id,
            quantity=data.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/guest/{guest_cart_id}/items/{product_id}", response_model=MessageResponse)
async def remove_guest_cart_item(
    guest_cart_id: str,
    product_id: Annotated[UUID, Path()],
    session: SessionDep,
):
    removed = await CartService(session).remove_item(
        guest_cart_id=guest_cart_id,
        product_id=product_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Cart item was not found.")
    return MessageResponse(detail="Guest cart item removed.")


@router.delete("/guest/{guest_cart_id}", response_model=MessageResponse)
async def clear_guest_cart(guest_cart_id: str, session: SessionDep):
    await CartService(session).clear(guest_cart_id=guest_cart_id)
    return MessageResponse(detail="Guest cart cleared.")
