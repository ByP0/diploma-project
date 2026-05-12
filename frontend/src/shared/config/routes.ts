export const AppRoutes = {
  home: "/",
  login: "/login",
  catalog: "/catalog",
  product: "/products/:productId",
  cart: "/cart",
  checkout: "/checkout",
  orders: "/orders",
  support: "/support",
  integrationsDev: "/integrations/dev",
  admin: "/admin",
  profile: "/profile",
  forbidden: "/forbidden",
} as const;

export function buildProductRoute(productId: string) {
  return `/products/${encodeURIComponent(productId)}`;
}
