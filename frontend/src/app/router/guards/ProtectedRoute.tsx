import type { ReactElement } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@features/auth/model/useAuth";
import { AppRoutes } from "@shared/config/routes";
import { LoadingState } from "@shared/ui";

type ProtectedRouteProps = {
  children?: ReactElement;
};

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const { isInitializing, user } = useAuth();

  if (isInitializing) {
    return <LoadingState description="Checking your session." title="Signing you in" />;
  }

  if (!user) {
    return <Navigate replace state={{ from: location }} to={AppRoutes.login} />;
  }

  return children ?? <Outlet />;
}
