from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.core.permissions import PermissionEnum, has_permission
from app.core.security import jwt_service
from app.db.postgres import db_postgres
from app.models.user import User, UserRoleEnum
from app.observability.context import bind_user_context

SessionDep = Annotated[AsyncSession, Depends(db_postgres.get_session)]


def get_access_token_from_cookie(request: Request) -> str:
    token = request.cookies.get(setting.access_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not authenticated.",
        )
    return token


async def get_current_user(
    token: Annotated[str, Depends(get_access_token_from_cookie)],
    session: SessionDep,
) -> User:
    payload = jwt_service.decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    user_id = payload.get("sub")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User was not found.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is blocked.",
        )

    bind_user_context(str(user.id))
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_current_user(
    request: Request,
    session: SessionDep,
) -> User | None:
    token = request.cookies.get(setting.access_cookie_name)
    if not token:
        return None

    try:
        payload = jwt_service.decode_token(token)
    except HTTPException:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await session.get(User, user_id)
    if not user or not user.is_active or user.is_blocked:
        return None

    bind_user_context(str(user.id))
    return user


OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]


async def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role is required.",
        )
    return current_user


CurrentAdmin = Annotated[User, Depends(require_admin)]


def require_permissions(*permissions: PermissionEnum):
    async def dependency(current_user: CurrentUser) -> User:
        missing = [
            permission.value
            for permission in permissions
            if not has_permission(current_user.role, permission)
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}.",
            )
        return current_user

    return dependency
