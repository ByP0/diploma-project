from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import password_service
from app.events.domain_events import UserBlocked, UserEmailVerified
from app.events.publishers.event_publisher import EventPublisher
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_login_audit_log import UserLoginAuditLog


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
        self.event_publisher = EventPublisher(session)

    async def get_profile(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def list_users(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update_user_access(self, *, user_id: UUID, data: dict[str, object]) -> User | None:
        user = await self.session.get(User, user_id)
        if not user:
            return None

        was_blocked = user.is_blocked
        was_email_verified = user.email_verified_at is not None

        if "role" in data and data["role"] is not None:
            user.role = data["role"]
        if "is_active" in data and data["is_active"] is not None:
            user.is_active = bool(data["is_active"])
        if "is_blocked" in data and data["is_blocked"] is not None:
            user.is_blocked = bool(data["is_blocked"])
            if user.is_blocked:
                user.blocked_reason = str(data.get("blocked_reason") or "Blocked by staff")
                user.blocked_at = datetime.now(timezone.utc)
            else:
                user.blocked_reason = None
                user.blocked_at = None
        if "email_verified" in data and data["email_verified"] is not None:
            user.email_verified_at = datetime.now(timezone.utc) if data["email_verified"] else None

        if not was_blocked and user.is_blocked:
            await self.event_publisher.publish_domain(
                UserBlocked(
                    user_id=str(user.id),
                    email=user.email,
                    blocked_reason=user.blocked_reason,
                )
            )

        if not was_email_verified and user.email_verified_at is not None:
            await self.event_publisher.publish_domain(
                UserEmailVerified(
                    user_id=str(user.id),
                    email=user.email,
                )
            )

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_login_audit(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        user_id: UUID | None = None,
        email: str | None = None,
    ) -> list[UserLoginAuditLog]:
        statement = select(UserLoginAuditLog).order_by(UserLoginAuditLog.created_at.desc()).limit(limit).offset(offset)
        if user_id:
            statement = statement.where(UserLoginAuditLog.user_id == user_id)
        if email:
            statement = statement.where(UserLoginAuditLog.email == email.strip().lower())
        result = await self.session.execute(statement)
        return list(result.scalars().all())

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
                raise ValueError("Current password is required.")
            if not password_service.verify(current_password, user.hashed_password):
                raise ValueError("Current password is invalid.")
            if current_password == new_password:
                raise ValueError("New password must differ from current password.")

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
            raise ValueError("No profile changes were provided.")

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
