import type * as React from "react";

import type { AuthPermission } from "../../../features/auth";
import { useAuth } from "../../../features/auth";
import { RedirectTo } from "./RedirectTo";

export interface PermissionGuardProps {
  permissions: AuthPermission[];
  requireAll?: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loginRedirectTo?: string;
  forbiddenRedirectTo?: string;
}

export function PermissionGuard({
  permissions,
  requireAll = true,
  children,
  fallback = null,
  loginRedirectTo = "/login",
  forbiddenRedirectTo = "/403",
}: PermissionGuardProps) {
  const { status, isAuthenticated, hasPermission } = useAuth();

  if (status === "checking") {
    return <>{fallback}</>;
  }

  if (!isAuthenticated) {
    return <RedirectTo href={loginRedirectTo} />;
  }

  const allowed = requireAll
    ? permissions.every((permission) => hasPermission(permission))
    : permissions.some((permission) => hasPermission(permission));

  if (!allowed) {
    return <RedirectTo href={forbiddenRedirectTo} />;
  }

  return <>{children}</>;
}
