import { Navigate, useLocation } from "react-router-dom";
import { AppRoutes } from "@shared/config/routes";

export function CatalogPage() {
  const location = useLocation();

  return <Navigate replace to={{ pathname: AppRoutes.home, search: location.search }} />;
}
