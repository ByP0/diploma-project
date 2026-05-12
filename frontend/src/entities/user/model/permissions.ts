import type { UserPermission, UserRole } from "./types";

export const rolePermissions: Record<UserRole, UserPermission[]> = {
  user: [],
  support: ["view_orders", "handle_support", "manage_notifications"],
  manager: [
    "view_orders",
    "manage_orders",
    "manage_inventory",
    "manage_delivery",
    "manage_payments",
    "manage_notifications",
    "view_login_audit",
  ],
  admin: [
    "handle_support",
    "manage_delivery",
    "manage_inventory",
    "manage_notifications",
    "manage_orders",
    "manage_payments",
    "manage_users",
    "view_admin_audit",
    "view_login_audit",
    "view_orders",
  ],
};

export function getRolePermissions(role: UserRole) {
  return rolePermissions[role];
}
