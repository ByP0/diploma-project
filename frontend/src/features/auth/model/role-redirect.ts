import type { AuthUser, UserRole } from "./auth.types";

export const roleRedirectMap: Record<UserRole, string> = {
  admin: "/admin",
  manager: "/manager/orders",
  support: "/support-desk",
  user: "/account",
};

export function getRoleRedirect(role: UserRole) {
  return roleRedirectMap[role] ?? "/account";
}

export function getUserRedirect(user: AuthUser | null) {
  return user ? getRoleRedirect(user.role) : "/login";
}

export function redirectTo(path: string, replace = true) {
  if (typeof window === "undefined") {
    return;
  }

  if (replace) {
    window.location.replace(path);
    return;
  }

  window.location.assign(path);
}
