import { apiClient } from "@shared/api";
import type {
  CheckoutPreviewRead,
  DeliveryQuoteRead,
  DeliveryQuoteRequest,
  OrderCheckoutCreate,
  OrderRead,
  UUID,
} from "@shared/api";

type CheckoutRequestOptions = {
  signal?: AbortSignal;
};

export const checkoutApi = {
  createOrderFromCart(data: OrderCheckoutCreate): Promise<OrderRead> {
    return apiClient.post("/orders/from-cart", data);
  },

  getDeliveryQuote(data: DeliveryQuoteRequest, options?: CheckoutRequestOptions): Promise<DeliveryQuoteRead> {
    return apiClient.post("/delivery/quote", data, { signal: options?.signal });
  },

  getOrder(orderId: UUID, options?: CheckoutRequestOptions): Promise<OrderRead> {
    return apiClient.get("/orders/{order_id}", {
      pathParams: {
        order_id: orderId,
      },
      signal: options?.signal,
    });
  },

  previewCheckout(data: OrderCheckoutCreate): Promise<CheckoutPreviewRead> {
    return apiClient.post("/checkout/preview", data);
  },

  retryPayment(orderId: UUID): Promise<OrderRead> {
    return apiClient.post("/orders/{order_id}/payments/retry", undefined, {
      pathParams: {
        order_id: orderId,
      },
    });
  },

  syncPayment(orderId: UUID): Promise<OrderRead> {
    return apiClient.post("/orders/{order_id}/payments/sync", undefined, {
      pathParams: {
        order_id: orderId,
      },
    });
  },
};
