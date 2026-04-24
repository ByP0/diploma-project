from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUser, SessionDep
from app.api.docs import build_error_responses
from app.schemas.user import UserProfileUpdate, UserRead
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["Профиль"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Получить профиль текущего пользователя",
    responses=build_error_responses(401, 500),
)
async def get_me(
    session: SessionDep,
    current_user: CurrentUser,
):
    user = await UserService(session).get_profile(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    return user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновить профиль текущего пользователя",
    responses=build_error_responses(400, 401, 422, 500),
)
async def update_me(
    data: UserProfileUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    service = UserService(session)
    try:
        return await service.update_profile(
            current_user,
            name=data.name,
            current_password=data.current_password,
            new_password=data.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/me/avatar",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Загрузить или заменить аватарку",
    responses=build_error_responses(400, 401, 413, 415, 422, 500),
)
async def upload_my_avatar(
    file: Annotated[UploadFile, File(description="Файл аватарки пользователя")],
    session: SessionDep,
    current_user: CurrentUser,
):
    try:
        return await UserService(session).upload_avatar(current_user, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete(
    "/me/avatar",
    response_model=UserRead,
    summary="Удалить аватарку текущего пользователя",
    responses=build_error_responses(401, 500),
)
async def delete_my_avatar(
    session: SessionDep,
    current_user: CurrentUser,
):
    return await UserService(session).delete_avatar(current_user)
