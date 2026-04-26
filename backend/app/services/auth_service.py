from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cookies import set_access_cookie, set_refresh_cookie
from app.core.security import jwt_service, password_service, token_hash_service
from app.events.domain_events import EmailSendRequested, UserPasswordResetRequested, UserRegistered
from app.events.publishers.event_publisher import EventPublisher
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRoleEnum
from app.services.brute_force_service import brute_force_service
from app.services.login_audit_service import LoginAuditService


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_publisher = EventPublisher(session)
        self.login_audit_service = LoginAuditService(session)

    async def register(self, email: str, password: str, name: str | None = None) -> User:
        password_service.validate(password)

        query = await self.session.execute(select(User).where(User.email == email))
        existing = query.scalar_one_or_none()
        if existing:
            raise AuthError("User with this email already exists.")

        user = User(
            email=email,
            name=name,
            hashed_password=password_service.hash(password),
            role=UserRoleEnum.USER,
        )
        self.session.add(user)
        await self.session.flush()
        await self.event_publisher.publish_domain(
            UserRegistered(
                user_id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role.value,
            )
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(
        self,
        email: str,
        password: str,
        response: Response,
        request: Request | None = None,
    ) -> User:
        normalized_email = email.strip().lower()
        try:
            brute_force_service.ensure_allowed(email=normalized_email, request=request)
        except ValueError as exc:
            await self.login_audit_service.record(
                email=normalized_email,
                success=False,
                request=request,
                failure_reason="bruteforce_lockout",
            )
            raise AuthError(str(exc)) from exc

        query = await self.session.execute(select(User).where(User.email == normalized_email))
        user = query.scalar_one_or_none()
        if user is None:
            brute_force_service.record_failure(email=normalized_email, request=request)
            await self.login_audit_service.record(
                email=normalized_email,
                success=False,
                request=request,
                failure_reason="invalid_credentials",
            )
            raise AuthError("Invalid email or password.")

        if not password_service.verify(password, user.hashed_password):
            brute_force_service.record_failure(email=normalized_email, request=request)
            await self.login_audit_service.record(
                email=normalized_email,
                success=False,
                user=user,
                request=request,
                failure_reason="invalid_credentials",
            )
            raise AuthError("Invalid email or password.")

        if not user.is_active:
            brute_force_service.record_failure(email=normalized_email, request=request)
            await self.login_audit_service.record(
                email=normalized_email,
                success=False,
                user=user,
                request=request,
                failure_reason="inactive_user",
            )
            raise AuthError("User account is inactive.")

        if user.is_blocked:
            brute_force_service.record_failure(email=normalized_email, request=request)
            await self.login_audit_service.record(
                email=normalized_email,
                success=False,
                user=user,
                request=request,
                failure_reason="blocked_user",
            )
            raise AuthError("User account is blocked.")

        access_token = jwt_service.create_access_token(user)
        refresh_token = jwt_service.create_refresh_token(user)

        await self._store_refresh_token(user.id, refresh_token)
        brute_force_service.record_success(email=normalized_email, request=request)
        await self.login_audit_service.record(
            email=normalized_email,
            success=True,
            user=user,
            request=request,
            commit=False,
        )
        set_access_cookie(response, access_token)
        set_refresh_cookie(response, refresh_token)
        await self.session.commit()
        return user

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = jwt_service.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthError("Invalid token type.")

        user_id = UUID(payload["sub"])
        db_token = await self._get_valid_refresh_token(user_id, refresh_token)
        if db_token is None:
            await self._revoke_all_user_tokens(user_id)
            raise AuthError("Refresh token is invalid or revoked.")

        user = await self.session.get(User, user_id)
        if user is None or not user.is_active or user.is_blocked:
            await self._revoke_all_user_tokens(user_id)
            raise AuthError("User is unavailable for refresh.")

        db_token.revoked = True
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
            await self.session.commit()

    async def request_password_reset(self, email: str) -> str | None:
        query = await self.session.execute(select(User).where(User.email == email))
        user = query.scalar_one_or_none()
        if not user:
            return None

        raw_token = self._generate_raw_token()
        user.password_reset_token_hash = token_hash_service.hash(raw_token)
        user.password_reset_requested_at = datetime.now(timezone.utc)
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await self.event_publisher.publish_domain(
            UserPasswordResetRequested(
                user_id=str(user.id),
                email=user.email,
                reset_token=raw_token,
            )
        )
        await self.session.commit()
        return raw_token

    async def reset_password(self, token: str, new_password: str) -> User:
        password_service.validate(new_password)
        query = await self.session.execute(
            select(User).where(User.password_reset_expires_at > datetime.now(timezone.utc))
        )
        users = list(query.scalars().all())
        user = next(
            (item for item in users if item.password_reset_token_hash and token_hash_service.verify(token, item.password_reset_token_hash)),
            None,
        )
        if not user:
            raise AuthError("Password reset token is invalid or expired.")

        user.hashed_password = password_service.hash(new_password)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        user.password_reset_requested_at = None
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def request_email_verification_stub(self, email: str) -> str | None:
        query = await self.session.execute(select(User).where(User.email == email))
        user = query.scalar_one_or_none()
        if not user:
            return None

        raw_token = self._generate_raw_token()
        user.email_verification_token_hash = token_hash_service.hash(raw_token)
        user.email_verification_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        await self.event_publisher.publish_domain(
            EmailSendRequested(
                notification_key=uuid4().hex,
                template_name="email_verification_stub",
                recipient=user.email,
                subject="Email verification is available as a stub",
                body_text=(
                    "Email verification is present in the backend as a stub and is currently disabled.\n"
                    f"Stub verification token: {raw_token}"
                ),
                body_html=(
                    "<p>Email verification is present in the backend as a stub and is currently disabled.</p>"
                    f"<p><strong>Stub verification token:</strong> {raw_token}</p>"
                ),
                context_payload={"user_id": str(user.id)},
            )
        )
        await self.session.commit()
        return raw_token

    async def cleanup_expired_tokens(self) -> None:
        await self.session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc))
        )
        await self.session.commit()

    async def _store_refresh_token(self, user_id: UUID, refresh_token: str) -> None:
        payload = jwt_service.decode_token(refresh_token)
        exp_ts = payload.get("exp")
        if isinstance(exp_ts, (int, float)):
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        elif isinstance(exp_ts, str):
            expires_at = datetime.fromtimestamp(int(exp_ts), tz=timezone.utc)
        else:
            raise AuthError("Invalid refresh token expiration.")

        self.session.add(
            RefreshToken(
                user_id=user_id,
                hashed_token=token_hash_service.hash(refresh_token),
                expires_at=expires_at,
                revoked=False,
            )
        )
        if hasattr(self.session, "flush"):
            await self.session.flush()

    async def _get_valid_refresh_token(
        self,
        user_id: UUID,
        refresh_token: str,
    ) -> Optional[RefreshToken]:
        now = datetime.now(timezone.utc)
        query = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > now,
            )
        )
        tokens = query.scalars().all()
        for db_token in tokens:
            if token_hash_service.verify(refresh_token, db_token.hashed_token):
                return db_token
        return None

    async def _revoke_all_user_tokens(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.session.commit()

    @staticmethod
    def _generate_raw_token() -> str:
        return uuid4().hex + uuid4().hex
