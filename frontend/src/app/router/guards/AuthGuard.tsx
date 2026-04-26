import type * as React from "react";

import { useAuth } from "../../../features/auth";
import { RedirectTo } from "./RedirectTo";

export interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

export function AuthGuard({ children, fallback = null, redirectTo = "/login" }: AuthGuardProps) {
  const { status, isAuthenticated } = useAuth();

  if (status === "checking") {
    return <>{fallback}</>;
  }

  if (!isAuthenticated) {
    return <RedirectTo href={redirectTo} />;
  }

  return <>{children}</>;
}
