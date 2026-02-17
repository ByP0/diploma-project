from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from typing import Literal
import bcrypt
import jwt
import uuid
import re

from app.core.config import setting
from app.models.user import User


class JWTService:
    def __init__(
        self,
        secret_key: str,
        algorith: str,
        access_expire_minutes: int,
        refresh_expire_days: int
    ):
        self.secret_key = secret_key,
        self.algorith = algorith,
        self.access_expire = timedelta(minutes=access_expire_minutes),
        self.refresh_expire = timedelta(days=refresh_expire_days)

    def _create_token(
        self, 
        user_id: uuid.UUID,
        token_type: Literal["access", "refresh"],
        expires_delta: timedelta,
        role: str | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)

        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta
        }

        if role and token_type == "access":
            payload["role"] = role

        return jwt.encode(
            payload=payload,
            key=self.secret_key,
            algorithm=self.algorith
        )
    
    def create_access_token(self, user: User) -> str:
        return self._create_token(
            user_id=user.id,
            token_type="access",
            expires_delta=self.access_expire,
            role=user.role.value,
        )

    def create_refresh_token(self, user: User) -> str:
        return self._create_token(
            user_id=user.id,
            token_type="refresh",
            expires_delta=self.refresh_expire,
        )

    def decode_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
        )
    
jwt_service = JWTService(
    secret_key=setting.secret_key,
    algorith=setting.algorithm,
    access_expire_minutes=setting.access_token_expire_minutes,
    refresh_expire_days=setting.refresh_token_expire_days
)


class PasswordService:
    pattern = r'[A-Za-z\d@$!%*#?&]{8,}'

    def validatepw(password, pattern=pattern):       
        if re.match(pattern, password) is None:
                raise HTTPException(status_code=500, detail="Bad password")

    def hashpw(password: str) -> bytes:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt)

    def verifypw(password: str, hashed_password: bytes) -> bool:
        return bcrypt.checkpw(password.encode(), hashed_password)
    
pw_service = PasswordService()