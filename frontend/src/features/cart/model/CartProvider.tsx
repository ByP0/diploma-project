import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "@features/auth/model/useAuth";
import { cartApi } from "@features/cart/api/cartApi";
import { clearGuestCartSession, readGuestCartSession, saveGuestCartSession } from "./guestCartStorage";
import { isApiError, type CartRead, type UUID } from "@shared/api";

type CartOwner = "guest" | "user";

type CartContextValue = {
  addItem: (productId: UUID, quantity?: number) => Promise<CartRead>;
  cart: CartRead;
  clearCart: () => Promise<void>;
  error: string | null;
  guestCartId: string | null;
  isLoading: boolean;
  isMerging: boolean;
  isMutating: boolean;
  owner: CartOwner;
  reloadCart: () => Promise<CartRead>;
  removeItem: (productId: UUID) => Promise<void>;
  totalAmount: number;
  totalItems: number;
  updateItem: (productId: UUID, quantity: number) => Promise<CartRead | void>;
};

export const CartContext = createContext<CartContextValue | null>(null);

function createEmptyCart(owner: CartOwner): CartRead {
  return {
    expires_at: null,
    guest_cart_id: null,
    is_guest_cart: owner === "guest",
    items: [],
    total_amount: 0,
    total_items: 0,
  };
}

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Cart request failed.";
}

type CartProviderProps = {
  children: ReactNode;
};

export function CartProvider({ children }: CartProviderProps) {
  const { isAuthenticated, isInitializing, user } = useAuth();
  const [cart, setCart] = useState<CartRead>(() => createEmptyCart("guest"));
  const [error, setError] = useState<string | null>(null);
  const [guestCartId, setGuestCartId] = useState<string | null>(() => readGuestCartSession()?.id ?? null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMerging, setIsMerging] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const mergedGuestForUserRef = useRef<string | null>(null);

  const owner: CartOwner = isAuthenticated ? "user" : "guest";

  const ensureGuestCartSession = useCallback(async () => {
    const storedSession = readGuestCartSession();
    if (storedSession) {
      setGuestCartId(storedSession.id);
      return storedSession.id;
    }

    const session = await cartApi.createGuestSession();
    saveGuestCartSession({
      expiresAt: session.expires_at,
      id: session.guest_cart_id,
    });
    setGuestCartId(session.guest_cart_id);
    return session.guest_cart_id;
  }, []);

  const reloadCart = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (isAuthenticated) {
        const userCart = await cartApi.getUserCart();
        setCart(userCart);
        return userCart;
      }

      const storedSession = readGuestCartSession();
      if (!storedSession) {
        setGuestCartId(null);
        const nextCart = createEmptyCart("guest");
        setCart(nextCart);
        return nextCart;
      }

      setGuestCartId(storedSession.id);
      const guestCart = await cartApi.getGuestCart(storedSession.id);
      setCart(guestCart);
      return guestCart;
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      throw caughtError;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const runMutation = useCallback(async <TResult,>(action: () => Promise<TResult>) => {
    setIsMutating(true);
    setError(null);

    try {
      return await action();
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
      throw caughtError;
    } finally {
      setIsMutating(false);
    }
  }, []);

  const addItem = useCallback(
    (productId: UUID, quantity = 1) =>
      runMutation(async () => {
        const nextCart = isAuthenticated
          ? await cartApi.addUserItem(productId, quantity)
          : await cartApi.addGuestItem(await ensureGuestCartSession(), productId, quantity);

        setCart(nextCart);
        return nextCart;
      }),
    [ensureGuestCartSession, isAuthenticated, runMutation],
  );

  const updateItem = useCallback(
    (productId: UUID, quantity: number) =>
      runMutation(async () => {
        if (quantity < 1) {
          await (isAuthenticated
            ? cartApi.removeUserItem(productId)
            : cartApi.removeGuestItem(await ensureGuestCartSession(), productId));
          return reloadCart();
        }

        const nextCart = isAuthenticated
          ? await cartApi.updateUserItem(productId, quantity)
          : await cartApi.updateGuestItem(await ensureGuestCartSession(), productId, quantity);

        setCart(nextCart);
        return nextCart;
      }),
    [ensureGuestCartSession, isAuthenticated, reloadCart, runMutation],
  );

  const removeItem = useCallback(
    (productId: UUID) =>
      runMutation(async () => {
        if (isAuthenticated) {
          await cartApi.removeUserItem(productId);
        } else {
          await cartApi.removeGuestItem(await ensureGuestCartSession(), productId);
        }

        await reloadCart();
      }),
    [ensureGuestCartSession, isAuthenticated, reloadCart, runMutation],
  );

  const clearCart = useCallback(
    () =>
      runMutation(async () => {
        if (isAuthenticated) {
          await cartApi.clearUserCart();
        } else {
          const storedSession = readGuestCartSession();
          if (storedSession) {
            await cartApi.clearGuestCart(storedSession.id);
            clearGuestCartSession();
          }

          setGuestCartId(null);
        }

        setCart(createEmptyCart(owner));
      }),
    [isAuthenticated, owner, runMutation],
  );

  const mergeGuestCartIntoUserCart = useCallback(async () => {
    const storedSession = readGuestCartSession();
    const mergeKey = user && storedSession ? `${user.id}:${storedSession.id}` : null;

    if (!isAuthenticated || !user || !storedSession || !mergeKey || mergedGuestForUserRef.current === mergeKey) {
      return;
    }

    setIsMerging(true);
    setError(null);

    try {
      const guestCart = await cartApi.getGuestCart(storedSession.id);

      for (const item of guestCart.items) {
        await cartApi.addUserItem(item.product_id, item.quantity);
      }

      await cartApi.clearGuestCart(storedSession.id);
      clearGuestCartSession();
      setGuestCartId(null);
      mergedGuestForUserRef.current = mergeKey;
      await reloadCart();
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsMerging(false);
    }
  }, [isAuthenticated, reloadCart, user]);

  useEffect(() => {
    if (isInitializing) {
      return;
    }

    if (isAuthenticated && user && readGuestCartSession()) {
      return;
    }

    void reloadCart().catch(() => undefined);
  }, [isAuthenticated, isInitializing, reloadCart, user]);

  useEffect(() => {
    if (isInitializing || !isAuthenticated) {
      return;
    }

    void mergeGuestCartIntoUserCart();
  }, [isAuthenticated, isInitializing, mergeGuestCartIntoUserCart]);

  const value = useMemo<CartContextValue>(
    () => ({
      addItem,
      cart,
      clearCart,
      error,
      guestCartId,
      isLoading,
      isMerging,
      isMutating,
      owner,
      reloadCart,
      removeItem,
      totalAmount: Number(cart.total_amount) || 0,
      totalItems: cart.total_items,
      updateItem,
    }),
    [
      addItem,
      cart,
      clearCart,
      error,
      guestCartId,
      isLoading,
      isMerging,
      isMutating,
      owner,
      reloadCart,
      removeItem,
      updateItem,
    ],
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
