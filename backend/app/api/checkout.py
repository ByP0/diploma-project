from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.schemas.order import CheckoutPreviewRead, OrderCheckoutCreate
from app.services.order_service import OrderService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/preview", response_model=CheckoutPreviewRead)
async def preview_checkout(
    data: OrderCheckoutCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        return await OrderService(session).preview_checkout(current_user, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
