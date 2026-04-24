from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, Request, status

from app.api.deps import CurrentAdmin, SessionDep
from app.api.docs import build_error_responses, message_response
from app.schemas.common import MessageResponse
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.admin_audit_service import AdminAuditService
from app.services.product_service import ProductService


router = APIRouter(prefix="/products", tags=["Товары"])


@router.get(
    "",
    response_model=list[ProductRead],
    summary="Получить список товаров",
    responses=build_error_responses(400, 422, 500),
)
async def get_products(
    session: SessionDep,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    active_only: bool = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=400,
            detail="Минимальная цена не может быть больше максимальной.",
        )

    return await ProductService(session).get_list(
        limit=limit,
        offset=offset,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
        active_only=active_only,
    )


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Получить товар по идентификатору",
    responses=build_error_responses(404, 422, 500),
)
async def get_product(
    session: SessionDep,
    product_id: Annotated[UUID, Path()],
):
    product = await ProductService(session).get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден.")
    return product


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать товар",
    responses=build_error_responses(400, 401, 403, 422, 500),
)
async def create_product(
    data: ProductCreate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = ProductService(session)
    try:
        product = await service.create(
            sku=data.sku,
            name=data.name,
            brand=data.brand,
            description=data.description,
            price=data.price,
            unit=data.unit,
            is_active=data.is_active,
            photo_ids=data.photo_ids,
            category_id=data.category_id,
            stock=data.stock,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="create",
        resource_type="product",
        resource_id=str(product.id),
        status_code=201,
        details={"sku": product.sku},
    )
    return product


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Обновить товар",
    responses=build_error_responses(400, 401, 403, 404, 422, 500),
)
async def update_product(
    product_id: Annotated[UUID, Path()],
    data: ProductUpdate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = ProductService(session)
    try:
        product = await service.update(
            product_id=product_id,
            sku=data.sku,
            name=data.name,
            brand=data.brand,
            description=data.description,
            price=data.price,
            unit=data.unit,
            is_active=data.is_active,
            photo_ids=data.photo_ids,
            category_id=data.category_id,
            stock=data.stock,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден.")

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="update",
        resource_type="product",
        resource_id=str(product.id),
        status_code=200,
        details={"sku": product.sku},
    )
    return product


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Удалить товар",
    responses={
        **build_error_responses(401, 403, 404, 422, 500),
        200: message_response("Товар успешно удалён."),
    },
)
async def delete_product(
    product_id: Annotated[UUID, Path()],
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    deleted = await ProductService(session).delete(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден.")

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="delete",
        resource_type="product",
        resource_id=str(product_id),
        status_code=200,
    )
    return MessageResponse(detail="Товар успешно удалён.")
