from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request, status

from app.api.deps import CurrentAdmin, SessionDep
from app.api.docs import build_error_responses, message_response
from app.cache import cache_service
from app.core.config import setting
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import MessageResponse
from app.services.admin_audit_service import AdminAuditService
from app.services.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["РљР°С‚РµРіРѕСЂРёРё"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РєР°С‚РµРіРѕСЂРёР№",
    responses=build_error_responses(422, 500),
)
async def get_categories(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    cache_key = f"catalog:categories:list:{limit}:{offset}"
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    categories = await CategoryService(session).get_list(limit=limit, offset=offset)
    payload = [CategoryRead.model_validate(category).model_dump(mode="json") for category in categories]
    await cache_service.set_json(cache_key, payload, ttl_seconds=setting.category_cache_ttl_seconds)
    return payload


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="РџРѕР»СѓС‡РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ РїРѕ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂСѓ",
    responses=build_error_responses(404, 422, 500),
)
async def get_category(
    session: SessionDep,
    category_id: Annotated[int, Path(ge=1)],
):
    cache_key = f"catalog:categories:item:{category_id}"
    cached = await cache_service.get_json(cache_key)
    if cached is not None:
        return cached

    category = await CategoryService(session).get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.")

    payload = CategoryRead.model_validate(category).model_dump(mode="json")
    await cache_service.set_json(cache_key, payload, ttl_seconds=setting.category_cache_ttl_seconds)
    return payload


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="РЎРѕР·РґР°С‚СЊ РєР°С‚РµРіРѕСЂРёСЋ",
    responses=build_error_responses(400, 401, 403, 422, 500),
)
async def create_category(
    data: CategoryCreate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = CategoryService(session)
    try:
        category = await service.create(data.id, data.name, data.slug)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="create",
        resource_type="category",
        resource_id=str(category.id),
        status_code=201,
        details={"slug": category.slug},
    )
    await cache_service.delete_by_prefix("catalog:categories:")
    await cache_service.delete_by_prefix("catalog:products:")
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="РћР±РЅРѕРІРёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ",
    responses=build_error_responses(400, 401, 403, 404, 422, 500),
)
async def update_category(
    category_id: Annotated[int, Path(ge=1)],
    data: CategoryUpdate,
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    category = await CategoryService(session).update(
        category_id=category_id,
        name=data.name,
        slug=data.slug,
    )
    if not category:
        raise HTTPException(status_code=404, detail="РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.")

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="update",
        resource_type="category",
        resource_id=str(category.id),
        status_code=200,
        details={"slug": category.slug},
    )
    await cache_service.delete_by_prefix("catalog:categories:")
    await cache_service.delete_by_prefix("catalog:products:")
    return category


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="РЈРґР°Р»РёС‚СЊ РєР°С‚РµРіРѕСЂРёСЋ",
    responses={
        **build_error_responses(400, 401, 403, 404, 422, 500),
        200: message_response("РљР°С‚РµРіРѕСЂРёСЏ СѓСЃРїРµС€РЅРѕ СѓРґР°Р»РµРЅР°."),
    },
)
async def delete_category(
    category_id: Annotated[int, Path(ge=1)],
    request: Request,
    session: SessionDep,
    current_admin: CurrentAdmin,
):
    service = CategoryService(session)
    try:
        deleted = await service.delete(category_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="РљР°С‚РµРіРѕСЂРёСЏ РЅРµ РЅР°Р№РґРµРЅР°.")

    await AdminAuditService(session).record(
        request=request,
        admin_user=current_admin,
        action="delete",
        resource_type="category",
        resource_id=str(category_id),
        status_code=200,
    )
    await cache_service.delete_by_prefix("catalog:categories:")
    await cache_service.delete_by_prefix("catalog:products:")
    return MessageResponse(detail="РљР°С‚РµРіРѕСЂРёСЏ СѓСЃРїРµС€РЅРѕ СѓРґР°Р»РµРЅР°.")
