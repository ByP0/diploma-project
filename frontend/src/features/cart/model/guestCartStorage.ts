const GUEST_CART_STORAGE_KEY = "diploma_guest_cart";

type StoredGuestCart = {
  expiresAt: string;
  id: string;
};

export function readGuestCartSession() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const value = window.localStorage.getItem(GUEST_CART_STORAGE_KEY);
    if (!value) {
      return null;
    }

    const parsed = JSON.parse(value) as Partial<StoredGuestCart>;
    if (!parsed.id || !parsed.expiresAt) {
      return null;
    }

    if (Date.parse(parsed.expiresAt) <= Date.now()) {
      clearGuestCartSession();
      return null;
    }

    return {
      expiresAt: parsed.expiresAt,
      id: parsed.id,
    };
  } catch {
    clearGuestCartSession();
    return null;
  }
}

export function saveGuestCartSession(session: StoredGuestCart) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(GUEST_CART_STORAGE_KEY, JSON.stringify(session));
}

export function clearGuestCartSession() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(GUEST_CART_STORAGE_KEY);
}
