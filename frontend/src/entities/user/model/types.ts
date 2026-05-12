import type { UserRead } from "@shared/api";

export const USER_ROLES = ["user", "manager", "support", "admin"] as const;

export type UserRole = (typeof USER_ROLES)[number];

export type UserPermission =
  | "handle_support"
  | "manage_delivery"
  | "manage_inventory"
  | "manage_notifications"
  | "manage_orders"
  | "manage_payments"
  | "manage_users"
  | "view_admin_audit"
  | "view_login_audit"
  | "view_orders";

export type User = UserRead;
