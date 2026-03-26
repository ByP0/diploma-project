# app/services/auth_service.py
from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.token_service import TokenService
from app.core.security import jwt_service, password_service
from app.models.user import User

class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.token_service = TokenService(self.token_repo)

    async def register(self, email: str, password: str) -> User:
        password_service.validate(password)
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        hashed = password_service.hash(password)
        user = User(email=email, hashed_password=hashed)
        created = await self.user_repo.create(user)
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(created)
        return created

    async def login(self, email: str, password: str, response) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user or not password_service.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = jwt_service.create_access_token(user)
        refresh_token = jwt_service.create_refresh_token(user)
        await self.token_service.store_token(user.id, refresh_token)
        response.set_cookie("access_token", access_token, httponly=True, samesite="lax")
        response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax")
        return user

    async def refresh(self, token: str) -> Tuple[str, str]:
        payload = jwt_service.decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = UUID(payload["sub"])
        db_token = await self.token_service.validate_token(user_id, token)
        if not db_token:
            await self.token_service.revoke_all(user_id)
            raise HTTPException(status_code=401, detail="Refresh token invalid or revoked")
        await self.token_service.revoke(db_token)
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        new_access = jwt_service.create_access_token(user)
        new_refresh = jwt_service.create_refresh_token(user)
        await self.token_service.store_token(user.id, new_refresh)
        await self.user_repo.session.commit()
        return new_access, new_refresh

    async def logout(self, token: str) -> None:
        try:
            payload = jwt_service.decode_token(token)
        except Exception:
            return
        if payload.get("type") != "refresh":
            return
        user_id = UUID(payload["sub"])
        db_token = await self.token_service.validate_token(user_id, token)
        if db_token:
            await self.token_service.revoke(db_token)
            await self.user_repo.session.commit()
