import type * as React from "react";

import { AuthProvider } from "../../features/auth";
import { CartProvider, StickyCartDrawer } from "../../features/cart";
import { ToastProvider } from "../../shared/ui/Toast";

export interface AppProvidersProps {
  children: React.ReactNode;
  enableStickyCart?: boolean;
  onCartCheckout?: () => void;
}

export function AppProviders({ children, enableStickyCart = true, onCartCheckout }: AppProvidersProps) {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          {children}
          {enableStickyCart ? <StickyCartDrawer onCheckout={onCartCheckout} /> : null}
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
