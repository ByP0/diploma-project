from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class UserRegistered(DomainEvent):
    __aggregate_type__ = "user"
    __aggregate_id_field__ = "user_id"

    user_id: str
    email: str
    name: str | None = None
    role: str


class UserEmailVerified(DomainEvent):
    __aggregate_type__ = "user"
    __aggregate_id_field__ = "user_id"

    user_id: str
    email: str


class UserPasswordResetRequested(DomainEvent):
    __aggregate_type__ = "user"
    __aggregate_id_field__ = "user_id"

    user_id: str
    email: str
    reset_token: str


class UserBlocked(DomainEvent):
    __aggregate_type__ = "user"
    __aggregate_id_field__ = "user_id"

    user_id: str
    email: str
    blocked_reason: str | None = None
