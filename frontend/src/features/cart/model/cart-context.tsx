import * as React from "react";

import { normalizeApiError } from "../../../core/api";
import { useAuth } from "../../auth";
import { useToast } from "../../../shared/ui/Toast";
import { cartApi } from "../api";
import {
  createEmptyCart,
  formatCartRemaining,
  getCartRemainingMs,
  transformBackendCart,
  validateCartQuantity,
} from "./cart-calculations";
import { guestCartStorage } from "./guest-cart-storage";
import type { CartAddInput, CartState } from "./cart.types";

export interface CartContextValue {
  cart: CartState;
  loading: boolean;
  syncing: boolean;
  drawerOpen: boolean;
  isGuestCart: boolean;
  expirationRemainingMs: number | null;
  expirationLabel: string | null;
  openDrawer: () => void;
  closeDrawer: () => void;
  toggleDrawer: () => void;
  reload: () => Promise<void>;
  addItem: (input: CartAddInput) => Promise<void>;
  updateItem: (productId: string, quantity: number) => Promise<void>;
  removeItem: (productId: string) => Promise<void>;
  clearCart: () => Promise<void>;
}

const CartContext = React.createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const { toast } = useToast();
  const [cart, setCart] = React.useState<CartState>(() => guestCartStorage.load());
  const [loading, setLoading] = React.useState(true);
  const [syncing, setSyncing] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [expirationTick, setExpirationTick] = React.useState(0);
  const mergedUserRef = React.useRef<string | null>(null);

  const isGuestCart = auth.status !== "authenticated";

  const loadUserCart = React.useCallback(async () => {
    const backendCart = await cartApi.getCart();
    setCart(transformBackendCart(backendCart));
  }, []);

  const loadGuestCart = React.useCallback(() => {
    const guestCart = guestCartStorage.load();
    setCart(guestCart);
  }, []);

  const mergeGuestCart = React.useCallback(async () => {
    const guestCart = guestCartStorage.load();
    if (!guestCart.items.length) {
      return true;
    }

    setSyncing(true);

    try {
      for (const item of guestCart.items) {
        await cartApi.addItem(item.productId, item.quantity);
      }

      guestCartStorage.clear();
      toast({
        title: "Корзина объединена",
        description: "Товары из гостевой корзины перенесены в профиль.",
        variant: "success",
      });
      return true;
    } catch (error) {
      toast({
        title: "Не удалось объединить корзину",
        description: normalizeApiError(error),
        variant: "warning",
      });
      return false;
    } finally {
      setSyncing(false);
    }
  }, [toast]);

  React.useEffect(() => {
    let cancelled = false;

    async function bootstrapCart() {
      setLoading(true);

      if (auth.status === "checking") {
        return;
      }

      if (auth.status !== "authenticated" || !auth.user) {
        mergedUserRef.current = null;
        loadGuestCart();
        setLoading(false);
        return;
      }

      try {
        if (mergedUserRef.current !== auth.user.id) {
          const merged = await mergeGuestCart();
          if (merged) {
            mergedUserRef.current = auth.user.id;
          }
        }

        if (!cancelled) {
          await loadUserCart();
        }
      } catch (error) {
        if (!cancelled) {
          toast({
            title: "Корзина не загрузилась",
            description: normalizeApiError(error),
            variant: "danger",
          });
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    bootstrapCart();

    return () => {
      cancelled = true;
    };
  }, [auth.status, auth.user, loadGuestCart, loadUserCart, mergeGuestCart, toast]);

  React.useEffect(() => {
    const timer = globalThis.setInterval(() => setExpirationTick((value) => value + 1), 60_000);
    return () => globalThis.clearInterval(timer);
  }, []);

  React.useEffect(() => {
    if (!isGuestCart) {
      return;
    }

    const remainingMs = getCartRemainingMs(cart);
    if (remainingMs === 0) {
      guestCartStorage.clear();
      setCart(createEmptyCart("guest"));
      if (cart.items.length) {
        toast({
          title: "Гостевая корзина очищена",
          description: "Истёк срок хранения 10 дней.",
          variant: "info",
        });
      }
    }
  }, [cart, expirationTick, isGuestCart, toast]);

  const reload = React.useCallback(async () => {
    if (auth.status === "authenticated") {
      setLoading(true);
      try {
        await loadUserCart();
      } finally {
        setLoading(false);
      }
      return;
    }

    loadGuestCart();
  }, [auth.status, loadGuestCart, loadUserCart]);

  const addItem = React.useCallback(
    async (input: CartAddInput) => {
      if (auth.status === "authenticated") {
        setSyncing(true);
        try {
          const backendCart = await cartApi.addItem(input.product.id, input.quantity ?? 1);
          setCart(transformBackendCart(backendCart));
          setDrawerOpen(true);
          toast({
            title: "Товар добавлен",
            description: input.product.name,
            variant: "success",
          });
        } catch (error) {
          toast({
            title: "Не удалось добавить товар",
            description: normalizeApiError(error),
            variant: "danger",
          });
        } finally {
          setSyncing(false);
        }
        return;
      }

      const validation = validateCartQuantity(input.product, input.quantity ?? 1);
      if (!validation.valid && validation.quantity <= 0) {
        toast({
          title: "Товар недоступен",
          description: validation.message ?? input.product.name,
          variant: "warning",
        });
        return;
      }

      const result = guestCartStorage.addItem(input);
      setCart(result.cart);
      setDrawerOpen(true);
      toast({
        title: "Товар добавлен",
        description: result.message ?? input.product.name,
        variant: result.message ? "warning" : "success",
      });
    },
    [auth.status, toast],
  );

  const removeItemInternal = React.useCallback(
    async (productId: string) => {
      if (auth.status === "authenticated") {
        setSyncing(true);
        try {
          await cartApi.removeItem(productId);
          await loadUserCart();
          toast({
            title: "Товар удалён",
            variant: "info",
          });
        } catch (error) {
          toast({
            title: "Не удалось удалить товар",
            description: normalizeApiError(error),
            variant: "danger",
          });
        } finally {
          setSyncing(false);
        }
        return;
      }

      setCart(guestCartStorage.removeItem(productId));
      toast({
        title: "Товар удалён",
        variant: "info",
      });
    },
    [auth.status, loadUserCart, toast],
  );

  const updateItem = React.useCallback(
    async (productId: string, quantity: number) => {
      if (quantity <= 0) {
        await removeItemInternal(productId);
        return;
      }

      if (auth.status === "authenticated") {
        setSyncing(true);
        try {
          const backendCart = await cartApi.updateItem(productId, quantity);
          setCart(transformBackendCart(backendCart));
        } catch (error) {
          toast({
            title: "Количество не обновлено",
            description: normalizeApiError(error),
            variant: "danger",
          });
        } finally {
          setSyncing(false);
        }
        return;
      }

      const result = guestCartStorage.updateItem(productId, quantity);
      setCart(result.cart);
      if (result.message) {
        toast({
          title: "Количество скорректировано",
          description: result.message,
          variant: "warning",
        });
      }
    },
    [auth.status, removeItemInternal, toast],
  );

  const clearCart = React.useCallback(async () => {
    if (auth.status === "authenticated") {
      setSyncing(true);
      try {
        await cartApi.clear();
        await loadUserCart();
        toast({
          title: "Корзина очищена",
          variant: "info",
        });
      } catch (error) {
        toast({
          title: "Не удалось очистить корзину",
          description: normalizeApiError(error),
          variant: "danger",
        });
      } finally {
        setSyncing(false);
      }
      return;
    }

    guestCartStorage.clear();
    setCart(createEmptyCart("guest"));
    toast({
      title: "Корзина очищена",
      variant: "info",
    });
  }, [auth.status, loadUserCart, toast]);

  const expirationRemainingMs = getCartRemainingMs(cart);
  const value = React.useMemo<CartContextValue>(
    () => ({
      cart,
      loading,
      syncing,
      drawerOpen,
      isGuestCart,
      expirationRemainingMs,
      expirationLabel: formatCartRemaining(expirationRemainingMs),
      openDrawer: () => setDrawerOpen(true),
      closeDrawer: () => setDrawerOpen(false),
      toggleDrawer: () => setDrawerOpen((open) => !open),
      reload,
      addItem,
      updateItem,
      removeItem: removeItemInternal,
      clearCart,
    }),
    [
      addItem,
      cart,
      clearCart,
      drawerOpen,
      expirationRemainingMs,
      isGuestCart,
      loading,
      reload,
      removeItemInternal,
      syncing,
      updateItem,
    ],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = React.useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within CartProvider");
  }

  return context;
}
