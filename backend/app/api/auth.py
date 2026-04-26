from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import SessionDep
from app.core.config import setting
from app.core.cookies import clear_auth_cookies, set_access_cookie, set_csrf_cookie, set_refresh_cookie
from app.schemas.common import MessageResponse
from app.schemas.token import TokenPair
from app.schemas.user import (
    EmailVerificationStubRequest,
    UserCreate,
    UserLogin,
    UserPasswordRecoveryRequest,
    UserPasswordReset,
    UserRead,
)
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class EmailVerificationConfirmStub(BaseModel):
    token: Annotated[str, Field(min_length=16, max_length=255)]

    model_config = ConfigDict(extra="forbid")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: SessionDep):
    service = AuthService(session)
    try:
        return await service.register(data.email, data.password, name=data.name)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=UserRead)
async def login(
    data: UserLogin,
    request: Request,
    response: Response,
    session: SessionDep,
):
    service = AuthService(session)
    try:
        user = await service.login(data.email, data.password, response, request=request)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    set_csrf_cookie(response)
    return user


@router.post("/refresh", response_model=TokenPair)
async def refresh(response: Response, request: Request, session: SessionDep):
    refresh_token = request.cookies.get(setting.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is missing.")

    service = AuthService(session)
    try:
        new_access, new_refresh = await service.refresh(refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    set_access_cookie(response, new_access)
    set_refresh_cookie(response, new_refresh)
    set_csrf_cookie(response)
    return TokenPair(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout", status_code=204)
async def logout(response: Response, request: Request, session: SessionDep):
    refresh_token = request.cookies.get(setting.refresh_cookie_name)
    if refresh_token:
        await AuthService(session).logout(refresh_token)
    clear_auth_cookies(response)


@router.post("/password/recover", response_model=MessageResponse)
async def recover_password(data: UserPasswordRecoveryRequest, session: SessionDep):
    await AuthService(session).request_password_reset(data.email)
    return MessageResponse(detail="Password recovery request accepted.")


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password(data: UserPasswordReset, session: SessionDep):
    service = AuthService(session)
    try:
        await service.reset_password(data.token, data.new_password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MessageResponse(detail="Password was updated.")


@router.post("/email-verification/request", response_model=MessageResponse)
async def request_email_verification(data: EmailVerificationStubRequest, session: SessionDep):
    await AuthService(session).request_email_verification_stub(data.email)
    return MessageResponse(detail="Email verification stub request has been registered.")


@router.post("/email-verification/confirm", response_model=MessageResponse)
async def confirm_email_verification_stub(
    _data: EmailVerificationConfirmStub,
):
    return MessageResponse(detail="Email verification is intentionally disabled in this build.")
