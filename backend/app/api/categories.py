# app/api/v1/categories.py
from fastapi import APIRouter, HTTPException, status, Query
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.api.deps import SessionDep, CurrentAdmin

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=list[CategoryRead])
async def get_categories(session: SessionDep, limit: int = Query(20, ge=1, le=100), offset: int = 0):
    service = CategoryService(session)
    return await service.get_list(limit=limit, offset=offset)

@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(session: SessionDep, category_id: int):
    service = CategoryService(session)
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, session: SessionDep, admin: CurrentAdmin):
    service = CategoryService(session)
    return await service.create(data.name, data.slug)

@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, data: CategoryUpdate, session: SessionDep, admin: CurrentAdmin):
    service = CategoryService(session)
    category = await service.update(category_id, data.name, data.slug)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: SessionDep, admin: CurrentAdmin):
    service = CategoryService(session)
    deleted = await service.delete(category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return {"detail": "Category deleted"}
