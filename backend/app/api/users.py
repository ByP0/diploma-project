from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile

from app.api.deps import CurrentUser, SessionDep, require_permissions
from app.core.permissions import PermissionEnum
from app.schemas.user import UserAdminUpdate, UserLoginAuditRead, UserProfileUpdate, UserRead
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
):
    return await UserService(session).list_login_audit(
        limit=limit,
        offset=offset,
        user_id=user_id,
        email=email,
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
):
    return await UserService(session).list_users(limit=limit, offset=offset)


@router.patch(
    "/{user_id}/access",
    response_model=UserRead,
    dependencies=[Depends(require_permissions(PermissionEnum.MANAGE_USERS))],
)
async def update_user_access(
    user_id: Annotated[UUID, Path()],
    data: UserAdminUpdate,
    session: SessionDep,
):
    user = await UserService(session).update_user_access(
        user_id=user_id,
        data=data.model_dump(exclude_unset=True),
    )
    if not user:
        raise HTTPException(status_code=404, detail="User was not found.")
    return user
