import type * as React from "react";

import { getUserRedirect, useAuth } from "../../../features/auth";
import { RedirectTo } from "./RedirectTo";

export interface GuestOnlyGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  redirectTo?: string;
}

export function GuestOnlyGuard({ children, fallback = null, redirectTo }: GuestOnlyGuardProps) {
  const { status, isAuthenticated, user } = useAuth();

  if (status === "checking") {
    return <>{fallback}</>;
  }

  if (isAuthenticated) {
    return <RedirectTo href={redirectTo ?? getUserRedirect(user)} />;
  }

  return <>{children}</>;
}
