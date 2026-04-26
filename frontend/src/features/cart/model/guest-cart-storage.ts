import {
  CART_TTL_MS,
  createEmptyCart,
  getAvailableStock,
  recalculateCart,
  validateCartQuantity,
} from "./cart-calculations";
import type { CartAddInput, CartItem, CartState } from "./cart.types";

const STORAGE_KEY = "greenmart:guest-cart:v1";

export const guestCartStorage = {
  load(): CartState {
    if (!canUseStorage()) {
      return createEmptyCart("guest");
    }

    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return createEmptyCart("guest");
      }

      const parsed = JSON.parse(raw) as CartState;
      if (isExpired(parsed)) {
        localStorage.removeItem(STORAGE_KEY);
        return createEmptyCart("guest");
      }

      return normalizeGuestCart(parsed);
    } catch {
      return createEmptyCart("guest");
    }
  },

  save(cart: CartState) {
    if (!canUseStorage()) {
      return;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
  },

  clear() {
    if (!canUseStorage()) {
      return;
    }

    localStorage.removeItem(STORAGE_KEY);
  },

  addItem(input: CartAddInput): { cart: CartState; message?: string } {
    const cart = this.load();
    const existingItem = cart.items.find((item) => item.productId === input.product.id);
    const nextRequestedQuantity = (existingItem?.quantity ?? 0) + (input.quantity ?? 1);
    const validation = validateCartQuantity(input.product, nextRequestedQuantity);

    if (validation.quantity <= 0) {
      return { cart, message: validation.message ?? "Товар недоступен" };
    }

    const now = new Date().toISOString();
    const expiresAt = createExpiresAt();
    const nextItems = existingItem
      ? cart.items.map((item) =>
          item.productId === input.product.id
            ? {
                ...item,
                expiresAt,
                product: input.product,
                quantity: validation.quantity,
                unitPrice: input.product.price,
                updatedAt: now,
              }
            : item,
        )
      : [
          ...cart.items,
          {
            id: createItemId(input.product.id),
            productId: input.product.id,
            quantity: validation.quantity,
            unitPrice: input.product.price,
            subtotal: validation.quantity * input.product.price,
            createdAt: now,
            updatedAt: now,
            expiresAt,
            product: input.product,
          },
        ];

    const nextCart = recalculateCart({
      ...cart,
      items: refreshItemExpiration(nextItems, expiresAt),
      expiresAt,
    });
    this.save(nextCart);

    return { cart: nextCart, message: validation.message ?? undefined };
  },

  updateItem(productId: string, quantity: number): { cart: CartState; message?: string } {
    const cart = this.load();
    const item = cart.items.find((cartItem) => cartItem.productId === productId);

    if (!item) {
      return { cart };
    }

    const validation = validateCartQuantity(item.product, quantity);
    const expiresAt = createExpiresAt();
    const nextItems =
      validation.quantity <= 0
        ? cart.items.filter((cartItem) => cartItem.productId !== productId)
        : cart.items.map((cartItem) =>
            cartItem.productId === productId
              ? {
                  ...cartItem,
                  expiresAt,
                  quantity: validation.quantity,
                  subtotal: validation.quantity * cartItem.unitPrice,
                  updatedAt: new Date().toISOString(),
                }
              : cartItem,
          );

    const nextCart = recalculateCart({
      ...cart,
      items: refreshItemExpiration(nextItems, expiresAt),
      expiresAt,
    });
    this.save(nextCart);
    return { cart: nextCart, message: validation.message ?? undefined };
  },

  removeItem(productId: string): CartState {
    const cart = this.load();
    const nextCart = recalculateCart({
      ...cart,
      items: cart.items.filter((item) => item.productId !== productId),
    });
    this.save(nextCart);
    return nextCart;
  },
};

function normalizeGuestCart(cart: CartState): CartState {
  const expiresAt = cart.expiresAt ?? new Date(Date.now() + CART_TTL_MS).toISOString();
  const items = cart.items
    .filter((item) => getAvailableStock(item.product) > 0)
    .map<CartItem>((item) => {
      const quantity = Math.min(item.quantity, getAvailableStock(item.product));
      return {
        ...item,
        quantity,
        subtotal: quantity * item.unitPrice,
        expiresAt,
      };
    });

  return recalculateCart({
    ...cart,
    mode: "guest",
    items,
    expiresAt,
  });
}

function isExpired(cart: CartState) {
  return Boolean(cart.expiresAt && new Date(cart.expiresAt).getTime() <= Date.now());
}

function canUseStorage() {
  return typeof localStorage !== "undefined";
}

function createItemId(productId: string) {
  return `guest-item:${productId}`;
}

function createExpiresAt() {
  return new Date(Date.now() + CART_TTL_MS).toISOString();
}

function refreshItemExpiration(items: CartItem[], expiresAt: string) {
  return items.map((item) => ({ ...item, expiresAt }));
}
