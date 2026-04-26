from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_login_audit_log import UserLoginAuditLog


class LoginAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        email: str,
        success: bool,
        user: User | None = None,
        request: Request | None = None,
        event_type: str = "login",
        failure_reason: str | None = None,
        details: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> UserLoginAuditLog:
        entry = UserLoginAuditLog(
            user_id=user.id if user else None,
            email=email,
            event_type=event_type,
            success=success,
            failure_reason=failure_reason,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            details=details or {},
        )
        self.session.add(entry)
        if commit:
            await self.session.commit()
        return entry
