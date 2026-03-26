# app/services/token_service.py
from datetime import datetime, timezone
from uuid import UUID

from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.core.security import jwt_service, token_hash_service
from app.models.refresh_token import RefreshToken

class TokenService:
    def __init__(self, repo: RefreshTokenRepository):
        self.repo = repo

    async def store_token(self, user_id: UUID, refresh_token: str) -> None:
        hashed = token_hash_service.hash(refresh_token)
        decoded = jwt_service.decode_token(refresh_token)
        exp_ts = decoded.get("exp")
        if isinstance(exp_ts, (int, float)):
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        else:
            expires_at = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)

        token_obj = RefreshToken(
            user_id=user_id,
            hashed_token=hashed,
            expires_at=expires_at,
            revoked=False
        )
        await self.repo.add(token_obj)
        await self.repo.session.commit()

    async def validate_token(self, user_id: UUID, refresh_token: str) -> RefreshToken | None:
        tokens = await self.repo.get_valid(user_id)
        for db_token in tokens:
            if token_hash_service.verify(refresh_token, db_token.hashed_token):
                return db_token
        return None

    async def revoke(self, db_token: RefreshToken) -> None:
        await self.repo.revoke(db_token)
        await self.repo.session.commit()

    async def revoke_all(self, user_id: UUID) -> None:
        await self.repo.revoke_all(user_id)
        await self.repo.session.commit()
