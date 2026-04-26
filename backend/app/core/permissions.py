from __future__ import annotations

import enum

from app.models.user import UserRoleEnum


class PermissionEnum(str, enum.Enum):
    MANAGE_USERS = "manage_users"
    VIEW_LOGIN_AUDIT = "view_login_audit"
    MANAGE_INVENTORY = "manage_inventory"
    MANAGE_ORDERS = "manage_orders"
    VIEW_ORDERS = "view_orders"
    MANAGE_PAYMENTS = "manage_payments"
    MANAGE_DELIVERY = "manage_delivery"
    MANAGE_NOTIFICATIONS = "manage_notifications"
    VIEW_ADMIN_AUDIT = "view_admin_audit"
    HANDLE_SUPPORT = "handle_support"


ROLE_PERMISSIONS: dict[UserRoleEnum, set[PermissionEnum]] = {
    UserRoleEnum.USER: set(),
    UserRoleEnum.SUPPORT: {
        PermissionEnum.VIEW_ORDERS,
        PermissionEnum.HANDLE_SUPPORT,
        PermissionEnum.MANAGE_NOTIFICATIONS,
    },
    UserRoleEnum.MANAGER: {
        PermissionEnum.VIEW_ORDERS,
        PermissionEnum.MANAGE_ORDERS,
        PermissionEnum.MANAGE_INVENTORY,
        PermissionEnum.MANAGE_DELIVERY,
        PermissionEnum.MANAGE_PAYMENTS,
        PermissionEnum.MANAGE_NOTIFICATIONS,
        PermissionEnum.VIEW_LOGIN_AUDIT,
    },
    UserRoleEnum.ADMIN: set(PermissionEnum),
}


def get_role_permissions(role: UserRoleEnum) -> set[PermissionEnum]:
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: UserRoleEnum, permission: PermissionEnum) -> bool:
    return permission in get_role_permissions(role)
