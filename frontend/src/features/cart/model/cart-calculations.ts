import type { BackendCartRead, CartItem, CartProductSnapshot, CartState, CartTotals } from "./cart.types";

export const CART_TTL_DAYS = 10;
export const CART_TTL_MS = CART_TTL_DAYS * 24 * 60 * 60 * 1000;

export function createEmptyCart(mode: CartState["mode"] = "guest"): CartState {
  const now = new Date().toISOString();

  return {
    id: mode === "guest" ? createCartId() : "user-cart",
    mode,
    items: [],
    totals: createTotals([]),
    expiresAt: mode === "guest" ? new Date(Date.now() + CART_TTL_MS).toISOString() : null,
    updatedAt: now,
  };
}

export function createTotals(items: CartItem[]): CartTotals {
  return items.reduce<CartTotals>(
    (totals, item) => {
      const availableStock = getAvailableStock(item.product);
      totals.totalItems += item.quantity;
      totals.totalAmount += item.subtotal;
      totals.totalDiscount += Math.max((item.product.oldPrice ?? item.unitPrice) - item.unitPrice, 0) * item.quantity;
      if (availableStock <= 0 || item.quantity > availableStock) {
        totals.unavailableItems += 1;
      }
      return totals;
    },
    {
      totalItems: 0,
      totalAmount: 0,
      totalDiscount: 0,
      unavailableItems: 0,
    },
  );
}

export function recalculateCart(cart: CartState): CartState {
  const items = cart.items.map((item) => ({
    ...item,
    subtotal: item.quantity * item.unitPrice,
  }));

  return {
    ...cart,
    items,
    totals: createTotals(items),
    updatedAt: new Date().toISOString(),
  };
}

export function getAvailableStock(product: CartProductSnapshot) {
  return Math.max(product.stock - product.reservedStock, 0);
}

export function validateCartQuantity(product: CartProductSnapshot, quantity: number) {
  const availableStock = getAvailableStock(product);
  const normalizedQuantity = Math.max(Math.floor(quantity), 1);

  if (availableStock <= 0) {
    return {
      quantity: 0,
      valid: false,
      message: "Товар закончился",
    };
  }

  if (normalizedQuantity > availableStock) {
    return {
      quantity: availableStock,
      valid: false,
      message: `Доступно только ${availableStock} ${product.unit}`,
    };
  }

  return {
    quantity: normalizedQuantity,
    valid: true,
    message: null,
  };
}

export function transformBackendCart(cart: BackendCartRead): CartState {
  const items = cart.items.map<CartItem>((item) => {
    const product: CartProductSnapshot = {
      id: item.product.id,
      sku: item.product.sku,
      name: item.product.name,
      brand: item.product.brand,
      price: toNumber(item.product.price),
      unit: item.product.unit,
      stock: item.product.stock,
      reservedStock: item.product.reserved_stock,
      imageUrl: item.product.primary_photo_url ?? item.product.photo_urls?.[0] ?? null,
      href: `/products/${item.product.id}`,
    };

    return {
      id: item.id,
      productId: item.product_id,
      quantity: item.quantity,
      unitPrice: product.price,
      subtotal: toNumber(item.subtotal),
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      expiresAt: item.expires_at,
      product,
    };
  });

  return {
    id: cart.guest_cart_id ?? "user-cart",
    mode: cart.guest_cart_id ? "guest" : "user",
    items,
    totals: {
      ...createTotals(items),
      totalItems: cart.total_items,
      totalAmount: toNumber(cart.total_amount),
    },
    expiresAt: cart.expires_at,
    updatedAt: new Date().toISOString(),
  };
}

export function getCartRemainingMs(cart: CartState | null) {
  if (!cart?.expiresAt) {
    return null;
  }

  return Math.max(new Date(cart.expiresAt).getTime() - Date.now(), 0);
}

export function formatCartRemaining(ms: number | null) {
  if (ms === null) {
    return null;
  }

  const totalMinutes = Math.ceil(ms / 60_000);
  const days = Math.floor(totalMinutes / (24 * 60));
  const hours = Math.floor((totalMinutes - days * 24 * 60) / 60);
  const minutes = totalMinutes % 60;

  if (days > 0) {
    return `${days} д ${hours} ч`;
  }

  if (hours > 0) {
    return `${hours} ч ${minutes} мин`;
  }

  return `${minutes} мин`;
}

export function toNumber(value: number | string) {
  return typeof value === "number" ? value : Number(value);
}

function createCartId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `guest-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
