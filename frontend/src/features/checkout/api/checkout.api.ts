import { apiRequest } from "../../../core/api";
import type { BackendCartRead } from "../../cart";
import type { CheckoutPayload, CheckoutPreviewRead, OrderRead } from "../model";

export const checkoutApi = {
  revalidateCart() {
    return apiRequest<BackendCartRead>("/api/cart");
  },

  preview(payload: CheckoutPayload) {
    return apiRequest<CheckoutPreviewRead>("/api/checkout/preview", {
      body: payload,
      method: "POST",
    });
  },

  createOrder(payload: CheckoutPayload) {
    return apiRequest<OrderRead>("/api/orders/from-cart", {
      body: payload,
      method: "POST",
    });
  },
};
