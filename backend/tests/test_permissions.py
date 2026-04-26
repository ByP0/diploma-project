import unittest

from app.core.permissions import PermissionEnum, get_role_permissions, has_permission
from app.models.user import UserRoleEnum


class PermissionsTests(unittest.TestCase):
    def test_manager_has_inventory_and_order_permissions(self) -> None:
        permissions = get_role_permissions(UserRoleEnum.MANAGER)
        self.assertIn(PermissionEnum.MANAGE_INVENTORY, permissions)
        self.assertIn(PermissionEnum.MANAGE_ORDERS, permissions)

    def test_support_cannot_manage_users(self) -> None:
        self.assertFalse(has_permission(UserRoleEnum.SUPPORT, PermissionEnum.MANAGE_USERS))
