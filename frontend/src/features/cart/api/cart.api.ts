import { apiRequest } from "../../../core/api";
import type { BackendCartRead } from "../model/cart.types";

export const cartApi = {
  getCart() {
    return apiRequest<BackendCartRead>("/api/cart");
  },

  addItem(productId: string, quantity: number) {
    return apiRequest<BackendCartRead>("/api/cart/items", {
      body: {
        product_id: productId,
        quantity,
      },
      method: "POST",
    });
  },

  updateItem(productId: string, quantity: number) {
    return apiRequest<BackendCartRead>(`/api/cart/items/${productId}`, {
      body: { quantity },
      method: "PUT",
    });
  },

  removeItem(productId: string) {
    return apiRequest<{ detail: string }>(`/api/cart/items/${productId}`, {
      method: "DELETE",
    });
  },

  clear() {
    return apiRequest<{ detail: string }>("/api/cart", {
      method: "DELETE",
    });
  },
};
