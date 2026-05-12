import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";
import type { UserPermission } from "@entities/user/model";
import { useAuth } from "@features/auth/model/useAuth";
import { AppRoutes } from "@shared/config/routes";
import { hasRequiredPermissions } from "@shared/lib/access/access";
import { LoadingState } from "@shared/ui";

type PermissionGuardProps = {
  children: ReactElement;
  permissions: readonly UserPermission[];
};

export function PermissionGuard({ children, permissions }: PermissionGuardProps) {
  const location = useLocation();
  const { isInitializing, user } = useAuth();

  if (isInitializing) {
    return <LoadingState description="Checking your permissions." title="Loading access" />;
  }

  if (!user) {
    return <Navigate replace state={{ from: location }} to={AppRoutes.login} />;
  }

  if (!hasRequiredPermissions(user.permissions, permissions)) {
    return <Navigate replace to={AppRoutes.forbidden} />;
  }

  return children;
}
