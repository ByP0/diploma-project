from __future__ import annotations

import logging
from typing import Protocol

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import password_service
from app.models.refresh_token import RefreshToken
from app.models.user import User


logger = logging.getLogger(__name__)


class AvatarStorage(Protocol):
    async def upload(self, file): ...
    async def delete(self, image_id: str) -> None: ...


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        image_service: AvatarStorage | None = None,
    ) -> None:
        self.session = session
        self.image_service = image_service

    async def get_profile(self, user_id) -> User | None:
        return await self.session.get(User, user_id)

    async def update_profile(
        self,
        user: User,
        *,
        name: str | None = None,
        current_password: str | None = None,
        new_password: str | None = None,
    ) -> User:
        changed = False

        if name is not None and name != user.name:
            user.name = name
            changed = True

        if new_password:
            if not current_password:
                raise ValueError("Для смены пароля нужно указать текущий пароль.")
            if not password_service.verify(current_password, user.hashed_password):
                raise ValueError("Текущий пароль указан неверно.")
            if current_password == new_password:
                raise ValueError("Новый пароль должен отличаться от текущего.")

            password_service.validate(new_password)
            user.hashed_password = password_service.hash(new_password)
            await self.session.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == user.id,
                    RefreshToken.revoked == False,
                )
                .values(revoked=True)
            )
            changed = True

        if not changed:
            raise ValueError("Нет данных для обновления профиля.")

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def upload_avatar(self, user: User, file) -> User:
        image_service = self._get_image_service()
        stored_image = await image_service.upload(file)
        old_avatar_image_id = user.avatar_image_id
        user.avatar_image_id = stored_image.id

        try:
            await self.session.commit()
            await self.session.refresh(user)
        except Exception:
            await self.session.rollback()
            await self._safe_delete_image(stored_image.id)
            raise

        if old_avatar_image_id and old_avatar_image_id != stored_image.id:
            await self._safe_delete_image(old_avatar_image_id)

        return user

    async def delete_avatar(self, user: User) -> User:
        if not user.avatar_image_id:
            return user

        old_avatar_image_id = user.avatar_image_id
        user.avatar_image_id = None
        await self.session.commit()
        await self.session.refresh(user)
        await self._safe_delete_image(old_avatar_image_id)
        return user

    def _get_image_service(self) -> AvatarStorage:
        if self.image_service is None:
            from app.services.image_service import ImageService

            self.image_service = ImageService()
        return self.image_service

    async def _safe_delete_image(self, image_id: str) -> None:
        try:
            await self._get_image_service().delete(image_id)
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.warning(
                "avatar_image_cleanup_failed",
                extra={
                    "event": "avatar_image_cleanup_failed",
                    "image_id": image_id,
                    "reason": str(exc),
                },
            )
