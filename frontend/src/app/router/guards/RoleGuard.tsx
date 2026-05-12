import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";
import type { UserRole } from "@entities/user/model";
import { useAuth } from "@features/auth/model/useAuth";
import { AppRoutes } from "@shared/config/routes";
import { hasRequiredRole } from "@shared/lib/access/access";
import { LoadingState } from "@shared/ui";

type RoleGuardProps = {
  children: ReactElement;
  roles: readonly UserRole[];
};

export function RoleGuard({ children, roles }: RoleGuardProps) {
  const location = useLocation();
  const { isInitializing, user } = useAuth();

  if (isInitializing) {
    return <LoadingState description="Checking your role." title="Loading access" />;
  }

  if (!user) {
    return <Navigate replace state={{ from: location }} to={AppRoutes.login} />;
  }

  if (!hasRequiredRole(user.role, roles)) {
    return <Navigate replace to={AppRoutes.forbidden} />;
  }

  return children;
}
