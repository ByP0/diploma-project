import type { ReactNode } from "react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@features/auth/model/AuthProvider";
import { CartProvider } from "@features/cart/model/CartProvider";
import { ToastProvider } from "@shared/ui";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <CartProvider>{children}</CartProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
