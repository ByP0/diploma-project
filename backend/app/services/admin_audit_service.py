from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_audit_log import AdminAuditLog
from app.models.user import User
from app.observability.metrics import metrics_registry


class AdminAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        request: Request,
        admin_user: User | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        status_code: int,
        details: dict[str, object] | None = None,
    ) -> AdminAuditLog:
        audit_entry = AdminAuditLog(
            admin_user_id=admin_user.id if admin_user else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_method=request.method,
            request_path=request.url.path,
            status_code=status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=details or {},
        )
        self.session.add(audit_entry)
        await self.session.commit()

        metrics_registry.increment(
            "shop_admin_audit_events_total",
            action=action,
            resource_type=resource_type,
        )
        return audit_entry
