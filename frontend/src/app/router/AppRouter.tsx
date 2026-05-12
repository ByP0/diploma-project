import { Route, Routes } from "react-router-dom";
import { AppLayout } from "@app/layouts/AppLayout/AppLayout";
import { PublicLayout } from "@app/layouts/PublicLayout/PublicLayout";
import { PermissionGuard } from "@app/router/guards/PermissionGuard";
import { ProtectedRoute } from "@app/router/guards/ProtectedRoute";
import { RoleGuard } from "@app/router/guards/RoleGuard";
import { AdminPage } from "@pages/AdminPage/AdminPage";
import { CartPage } from "@pages/CartPage/CartPage";
import { CatalogPage } from "@pages/CatalogPage/CatalogPage";
import { CheckoutPage } from "@pages/CheckoutPage/CheckoutPage";
import { ForbiddenPage } from "@pages/ForbiddenPage/ForbiddenPage";
import { HomePage } from "@pages/HomePage/HomePage";
import { IntegrationsDevPage } from "@pages/IntegrationsDevPage/IntegrationsDevPage";
import { LoginPage } from "@pages/LoginPage/LoginPage";
import { NotFoundPage } from "@pages/NotFoundPage/NotFoundPage";
import { OrdersPage } from "@pages/OrdersPage/OrdersPage";
import { ProductPage } from "@pages/ProductPage/ProductPage";
import { ProfilePage } from "@pages/ProfilePage/ProfilePage";
import { SupportPage } from "@pages/SupportPage/SupportPage";
import { AppRoutes } from "@shared/config/routes";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path={AppRoutes.login} element={<LoginPage />} />
      </Route>

      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="products/:productId" element={<ProductPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="support" element={<SupportPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="checkout" element={<CheckoutPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route
            path="integrations/dev"
            element={
              <RoleGuard roles={["admin", "manager"]}>
                <PermissionGuard permissions={["manage_payments", "manage_delivery"]}>
                  <IntegrationsDevPage />
                </PermissionGuard>
              </RoleGuard>
            }
          />
          <Route
            path="admin"
            element={
              <RoleGuard roles={["admin"]}>
                <PermissionGuard permissions={["manage_inventory", "manage_orders", "manage_users", "view_login_audit"]}>
                  <AdminPage />
                </PermissionGuard>
              </RoleGuard>
            }
          />
        </Route>

        <Route path="forbidden" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
