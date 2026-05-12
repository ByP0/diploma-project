import type { User, UserPermission, UserRole } from "@entities/user/model/types";

export type AccessRule = {
  permissions?: readonly UserPermission[];
  roles?: readonly UserRole[];
};

export function hasRequiredRole(userRole: UserRole, roles?: readonly UserRole[]) {
  return !roles?.length || roles.includes(userRole);
}

export function hasRequiredPermissions(
  userPermissions: readonly string[],
  permissions?: readonly UserPermission[],
) {
  return !permissions?.length || permissions.every((permission) => userPermissions.includes(permission));
}

export function canAccess(user: User | null | undefined, rule?: AccessRule | null) {
  if (!rule?.permissions?.length && !rule?.roles?.length) {
    return true;
  }

  if (!user) {
    return false;
  }

  return hasRequiredRole(user.role, rule.roles) && hasRequiredPermissions(user.permissions, rule.permissions);
}
