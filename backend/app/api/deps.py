# app/api/deps.py
from fastapi import Depends, HTTPException, Request, status
from app.db.postgres import database
from app.models.user import User, UserRoleEnum
from app.core.security import jwt_service
from sqlalchemy.ext.asyncio import AsyncSession

SessionDep = Depends(database.get_session)

def get_access_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token

async def get_current_user(token: str = Depends(get_access_token_from_cookie), session: AsyncSession = SessionDep) -> User:
    try:
        payload = jwt_service.decode_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e.detail))
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

CurrentUser = Depends(get_current_user)

def require_admin(current_user: User = CurrentUser) -> User:
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user

CurrentAdmin = Depends(require_admin)
