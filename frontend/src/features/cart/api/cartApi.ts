import { apiClient } from "@shared/api";
import type { CartRead, UUID } from "@shared/api";

export const cartApi = {
  addGuestItem(guestCartId: string, productId: UUID, quantity: number): Promise<CartRead> {
    return apiClient.post(
      "/cart/guest/{guest_cart_id}/items",
      {
        product_id: productId,
        quantity,
      },
      {
        pathParams: {
          guest_cart_id: guestCartId,
        },
      },
    );
  },

  addUserItem(productId: UUID, quantity: number): Promise<CartRead> {
    return apiClient.post("/cart/items", {
      product_id: productId,
      quantity,
    });
  },

  clearGuestCart(guestCartId: string) {
    return apiClient.delete("/cart/guest/{guest_cart_id}", {
      pathParams: {
        guest_cart_id: guestCartId,
      },
    });
  },

  clearUserCart() {
    return apiClient.delete("/cart");
  },

  createGuestSession() {
    return apiClient.post("/cart/guest/sessions", undefined, { skipAuthRefresh: true });
  },

  getGuestCart(guestCartId: string): Promise<CartRead> {
    return apiClient.get("/cart/guest/{guest_cart_id}", {
      pathParams: {
        guest_cart_id: guestCartId,
      },
      skipAuthRefresh: true,
    });
  },

  getUserCart(): Promise<CartRead> {
    return apiClient.get("/cart");
  },

  removeGuestItem(guestCartId: string, productId: UUID) {
    return apiClient.delete("/cart/guest/{guest_cart_id}/items/{product_id}", {
      pathParams: {
        guest_cart_id: guestCartId,
        product_id: productId,
      },
    });
  },

  removeUserItem(productId: UUID) {
    return apiClient.delete("/cart/items/{product_id}", {
      pathParams: {
        product_id: productId,
      },
    });
  },

  updateGuestItem(guestCartId: string, productId: UUID, quantity: number): Promise<CartRead> {
    return apiClient.put(
      "/cart/guest/{guest_cart_id}/items/{product_id}",
      { quantity },
      {
        pathParams: {
          guest_cart_id: guestCartId,
          product_id: productId,
        },
      },
    );
  },

  updateUserItem(productId: UUID, quantity: number): Promise<CartRead> {
    return apiClient.put("/cart/items/{product_id}", { quantity }, { pathParams: { product_id: productId } });
  },
};
