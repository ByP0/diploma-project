from uuid import UUID
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, Request, UploadFile

from app.api.deps import CurrentUser, SessionDep, require_permissions
from app.core.permissions import PermissionEnum
from app.models.user import UserRoleEnum
from app.schemas.user import UserAdminUpdate, UserLoginAuditRead, UserProfileUpdate, UserRead
from app.services.admin_audit_service import AdminAuditService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def get_me(session: SessionDep, current_user: CurrentUser):
    user = await UserService(session).get_profile(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User was not found.")
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserProfileUpdate, session: SessionDep, current_user: CurrentUser):
    try:
        return await UserService(session).update_profile(
            current_user,
            name=data.name,
            current_password=data.current_password,
            new_password=data.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/me/avatar", response_model=UserRead)
async def upload_my_avatar(
    file: Annotated[UploadFile, File(description="User avatar file")],
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        return await UserService(session).upload_avatar(current_user, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/me/avatar", response_model=UserRead)
async def delete_my_avatar(session: SessionDep, current_user: CurrentUser):
    return await UserService(session).delete_avatar(current_user)


@router.get(
    "/login-audit",
    response_model=list[UserLoginAuditRead],
    dependencies=[Depends(require_permissions(PermissionEnum.VIEW_LOGIN_AUDIT))],
)
async def get_login_audit(
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user_id: UUID | None = Query(default=None),
    email: str | None = Query(default=None),
    success: bool | None = Query(default=None),
    event_type: str | None = Query(default=None, min_length=1, max_length=32),
    ip_address: str | None = Query(default=None, min_length=1, max_length=64),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
):
    return await UserService(session).list_login_audit(
        limit=limit,
        offset=offset,
        user_id=user_id,
        email=email,
        success=success,
        event_type=event_type,
        ip_address=ip_address,
        created_from=created_from,
        created_to=created_to,
    )


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_USERS))],
)
async def list_users(
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    role: UserRoleEnum | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_blocked: bool | None = Query(default=None),
    email_verified: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=120),
):
    return await UserService(session).list_users(
        limit=limit,
        offset=offset,
        role=role,
        is_active=is_active,
        is_blocked=is_blocked,
        email_verified=email_verified,
        search=search,
    )


@router.patch(
    "/{user_id}/access",
    response_model=UserRead,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_USERS))],
)
async def update_user_access(
    user_id: Annotated[UUID, Path()],
    data: UserAdminUpdate,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
):
    user = await UserService(session).update_user_access(
        user_id=user_id,
        data=data.model_dump(exclude_unset=True),
    )
    if not user:
        raise HTTPException(status_code=404, detail="User was not found.")
    await AdminAuditService(session).record(
        request=request,
        admin_user=current_user,
        action="update_access",
        resource_type="user",
        resource_id=str(user.id),
        status_code=200,
        details=data.model_dump(exclude_unset=True, mode="json"),
    )
    return user
