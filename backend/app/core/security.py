from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import HTTPException
import hashlib
import jwt
import uuid
import bcrypt
import re

from app.core.config import setting
from app.core.constans import PASSWORD_PATTERN
from app.models.user import User


class JWTService:

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_expire = timedelta(minutes=access_expire_minutes)
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
            "exp": now + expires_delta,
        }

        if role and token_type == "access":
            payload["role"] = role

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
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
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


class PasswordService:

    @staticmethod
    def validate(password: str) -> None:
        if re.match(PASSWORD_PATTERN, password) is None:
            raise HTTPException(
                status_code=400,
                detail="Password does not meet security requirements",
            )

    @staticmethod
    def hash(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password.encode(),
            hashed_password.encode(),
        )
    
class TokenHashService:

    @staticmethod
    def hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def verify(token: str, hashed: str) -> bool:
        return hashlib.sha256(token.encode()).hexdigest() == hashed
    

token_hash_service = TokenHashService()

jwt_service = JWTService(
    secret_key=setting.secret_key,
    algorithm=setting.algorithm,
    access_expire_minutes=setting.access_token_expire_minutes,
    refresh_expire_days=setting.refresh_token_expire_days,
)

password_service = PasswordService()
