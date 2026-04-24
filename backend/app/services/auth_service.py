from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple, Optional
from uuid import UUID

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Response

from app.core.cookies import set_access_cookie, set_refresh_cookie
from app.core.security import jwt_service, password_service, token_hash_service
from app.models.user import User
from app.models.user import UserRoleEnum
from app.models.refresh_token import RefreshToken
from app.services.notification_service import NotificationService


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_service = NotificationService()

    async def register(self, email: str, password: str) -> User:
        password_service.validate(password)

        q = await self.session.execute(select(User).where(User.email == email))
        existing = q.scalar_one_or_none()
        if existing:
            raise AuthError("Пользователь с таким email уже существует.")

        hashed = password_service.hash(password)

        user = User(
            email=email,
            hashed_password=hashed,
            role=UserRoleEnum.USER,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        await self.notification_service.send_registration_welcome(user)
        return user

    async def login(self, email: str, password: str, response: Response) -> User:
        q = await self.session.execute(select(User).where(User.email == email))

        user = q.scalar_one_or_none()
        if user is None:
            raise AuthError("Неверный email или пароль.")

        if not password_service.verify(password, user.hashed_password):
            raise AuthError("Неверный email или пароль.")

        access_token = jwt_service.create_access_token(user)
        refresh_token = jwt_service.create_refresh_token(user)

        await self._store_refresh_token(user.id, refresh_token)

        set_access_cookie(response, access_token)
        set_refresh_cookie(response, refresh_token)

        return user



    async def refresh(self, refresh_token: str) -> Tuple[str, str]:
        payload = jwt_service.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthError("Некорректный тип токена.")

        user_id = UUID(payload["sub"])
        db_token = await self._get_valid_refresh_token(user_id, refresh_token)

        if db_token is None:
            await self._revoke_all_user_tokens(user_id)
            raise AuthError("Токен обновления недействителен или уже отозван.")

        db_token.revoked = True
        self.session.add(db_token)

        user = await self.session.get(User, user_id)
        if user is None:
            raise AuthError("Пользователь для обновления токена не найден.")

        new_access = jwt_service.create_access_token(user)
        new_refresh = jwt_service.create_refresh_token(user)
        await self._store_refresh_token(user_id, new_refresh)

        await self.session.commit()
        return new_access, new_refresh

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = jwt_service.decode_token(refresh_token)
        except Exception:
            return

        if payload.get("type") != "refresh":
            return

        user_id = UUID(payload["sub"])
        db_token = await self._get_valid_refresh_token(user_id, refresh_token)
        if db_token:
            db_token.revoked = True
            self.session.add(db_token)
            await self.session.commit()

    async def cleanup_expired_tokens(self) -> None:
        now = datetime.now(timezone.utc)
        await self.session.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
        await self.session.commit()

    async def _store_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        hashed = token_hash_service.hash(refresh_token)

        payload = jwt_service.decode_token(refresh_token)
        exp_ts = payload.get("exp")
        if isinstance(exp_ts, (int, float)):
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        elif isinstance(exp_ts, str):
            expires_at = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
        else:
            raise AuthError("Некорректный формат времени жизни токена.")

        r = RefreshToken(
            user_id=user_id,
            hashed_token=hashed,
            expires_at=expires_at,
            revoked=False
        )

        self.session.add(r)
        await self.session.flush()
        await self.session.commit()

    async def _get_valid_refresh_token(self, user_id: UUID, refresh_token: str) -> Optional[RefreshToken]:
        now = datetime.now(timezone.utc)
        q = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > now,
            )
        )
        tokens = q.scalars().all()
        for db_t in tokens:
            if token_hash_service.verify(refresh_token, db_t.hashed_token):
                return db_t
        return None

    async def _revoke_all_user_tokens(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            ).values(revoked=True)
        )
        await self.session.commit()
