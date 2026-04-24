from __future__ import annotations

from uuid import UUID

from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from app.core.security import password_service
from app.db.postgres import db_postgres
from app.models.user import User, UserRoleEnum


class AdminAuthBackend(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = str(form.get("username") or form.get("email") or "").strip().lower()
        password = str(form.get("password") or "")
        if not email or not password:
            return False

        async with db_postgres.session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user or user.role != UserRoleEnum.ADMIN:
            return False

        if not password_service.verify(password, user.hashed_password):
            return False

        request.session.update(
            {
                "admin_user_id": str(user.id),
                "admin_email": user.email,
                "is_admin": True,
            }
        )
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        raw_user_id = request.session.get("admin_user_id")
        if not raw_user_id or not request.session.get("is_admin"):
            return False

        try:
            user_id = UUID(str(raw_user_id))
        except ValueError:
            request.session.clear()
            return False

        async with db_postgres.session_factory() as session:
            user = await session.get(User, user_id)

        if not user or user.role != UserRoleEnum.ADMIN:
            request.session.clear()
            return False

        request.state.admin_user = user
        return True
