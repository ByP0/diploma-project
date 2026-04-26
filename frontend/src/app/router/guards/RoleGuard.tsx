import type * as React from "react";

import type { UserRole } from "../../../features/auth";
import { useAuth } from "../../../features/auth";
import { RedirectTo } from "./RedirectTo";

export interface RoleGuardProps {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loginRedirectTo?: string;
  forbiddenRedirectTo?: string;
}

export function RoleGuard({
  roles,
  children,
  fallback = null,
  loginRedirectTo = "/login",
  forbiddenRedirectTo = "/403",
}: RoleGuardProps) {
  const { status, isAuthenticated, hasRole } = useAuth();

  if (status === "checking") {
    return <>{fallback}</>;
  }

  if (!isAuthenticated) {
    return <RedirectTo href={loginRedirectTo} />;
  }

  if (!hasRole(roles)) {
    return <RedirectTo href={forbiddenRedirectTo} />;
  }

  return <>{children}</>;
}
