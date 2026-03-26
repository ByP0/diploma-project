# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Response, status, Request
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.token import TokenPair
from app.api.deps import SessionDep

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(data: UserCreate, session: SessionDep):
    service = AuthService(session)
    user = await service.register(data.email, data.password)
    return user

@router.post("/login", response_model=UserRead)
async def login_user(data: UserLogin, response: Response, session: SessionDep):
    service = AuthService(session)
    user = await service.login(data.email, data.password, response)
    return user

@router.post("/refresh", response_model=TokenPair)
async def refresh_token(response: Response, request: Request, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")
    service = AuthService(session)
    new_access, new_refresh = await service.refresh(refresh_token)
    response.set_cookie("access_token", new_access, httponly=True, samesite="lax")
    response.set_cookie("refresh_token", new_refresh, httponly=True, samesite="lax")
    return TokenPair(access_token=new_access, refresh_token=new_refresh)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(request: Request, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    service = AuthService(session)
    if refresh_token:
        await service.logout(refresh_token)
    return {"detail": "Logged out"}
