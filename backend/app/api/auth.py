from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import db_postgres
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.token import TokenPair
from app.services.auth_service import AuthService, AuthError
from app.api.deps import SessionDep

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    session: SessionDep,
):
    service = AuthService(session)

    try:
        user = await service.register(data.email, data.password)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return user

@router.post("/login", response_model=UserRead)
async def login(
    data: UserLogin,
    response: Response,
    session: SessionDep,
):
    service = AuthService(session)

    try:
        user = await service.login(data.email, data.password, response)
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user

@router.post("/refresh", response_model=TokenPair)
async def refresh(
    response: Response,
    request: Request,
    session: SessionDep,
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    service = AuthService(session)

    try:
        new_access, new_refresh = await service.refresh(refresh_token)
    except AuthError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    response.set_cookie("access_token", new_access, httponly=True, samesite="lax")
    response.set_cookie("refresh_token", new_refresh, httponly=True, samesite="lax")

    return TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
    )

@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    request: Request,
    session: SessionDep,
):
    refresh_token = request.cookies.get("refresh_token")

    service = AuthService(session)

    if refresh_token:
        await service.logout(refresh_token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
