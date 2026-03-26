# app/api/v1/products.py
from fastapi import APIRouter, HTTPException, Query, status
from typing import Annotated

from app.api.deps import SessionDep
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=list[ProductRead])
async def get_products(
    session: SessionDep,
    search: Annotated[str | None, Query(default=None)] = None,
    min_price: Annotated[float | None, Query(default=None)] = None,
    max_price: Annotated[float | None, Query(default=None)] = None,
    category_id: Annotated[int | None, Query(default=None)] = None,
    in_stock: Annotated[bool | None, Query(default=None)] = None,
    sort_by: Annotated[str | None, Query(default=None)] = None,
    limit: Annotated[int, Query(default=20, ge=1, le=100)] = 20,
    offset: Annotated[int, Query(default=0, ge=0)] = 0,
):
    service = ProductService(session)
    return await service.get_list(search, min_price, max_price, category_id, in_stock, sort_by, limit, offset)

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, session: SessionDep):
    service = ProductService(session)
    return await service.create(
        name=data.name,
        description=data.description,
        price=data.price,
        category_id=data.category_id,
        stock=data.stock,
    )

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: str, session: SessionDep):
    service = ProductService(session)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(product_id: str, data: ProductUpdate, session: SessionDep):
    service = ProductService(session)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    updates = data.dict(exclude_none=True)
    for field, value in updates.items():
        setattr(product, field, value)
    updated = await service.update(product)
    return updated

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, session: SessionDep):
    service = ProductService(session)
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await service.delete(product)
    return {"detail": "Product deleted"}
