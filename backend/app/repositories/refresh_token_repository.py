# app/repositories/refresh_token_repository.py
from uuid import UUID
from datetime import datetime, timezone
from typing import List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, token: RefreshToken) -> None:
        self.session.add(token)
        await self.session.flush()

    async def get_valid(self, user_id: UUID) -> List[RefreshToken]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > now,
            )
        )
        return result.scalars().all()

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked = True
        self.session.add(token)
        await self.session.flush()

    async def revoke_all(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.session.flush()

    async def delete_expired(self) -> None:
        now = datetime.now(timezone.utc)
        await self.session.execute(delete(RefreshToken).where(RefreshToken.expires_at < now))
        await self.session.flush()
