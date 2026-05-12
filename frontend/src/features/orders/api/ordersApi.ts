import { apiClient } from "@shared/api";
import type { CartRead, OrderCancelRequest, OrderDocumentRead, OrderRead, OrderRefundRequest, UUID } from "@shared/api";

type ListOrdersParams = {
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
};

type RequestOptions = {
  signal?: AbortSignal;
};

export type OrderDocumentType = "invoice" | "receipt";

export const ordersApi = {
  cancel(orderId: UUID, data: OrderCancelRequest): Promise<OrderRead> {
    return apiClient.post("/orders/{order_id}/cancel", data, {
      pathParams: {
        order_id: orderId,
      },
    });
  },

  getById(orderId: UUID, options?: RequestOptions): Promise<OrderRead> {
    return apiClient.get("/orders/{order_id}", {
      pathParams: {
        order_id: orderId,
      },
      signal: options?.signal,
    });
  },

  getDocument(orderId: UUID, documentType: OrderDocumentType, options?: RequestOptions): Promise<OrderDocumentRead> {
    return apiClient.get("/orders/{order_id}/documents/{document_type}", {
      pathParams: {
        document_type: documentType,
        order_id: orderId,
      },
      signal: options?.signal,
    });
  },

  list(params: ListOrdersParams = {}): Promise<OrderRead[]> {
    return apiClient.get("/orders", {
      query: {
        limit: params.limit ?? 20,
        offset: params.offset ?? 0,
      },
      signal: params.signal,
    });
  },

  recheckPayment(orderId: UUID): Promise<OrderRead> {
    return apiClient.post("/payments/orders/{order_id}/recheck", undefined, {
      pathParams: {
        order_id: orderId,
      },
    });
  },

  refund(orderId: UUID, data: OrderRefundRequest): Promise<OrderRead> {
    return apiClient.post("/orders/{order_id}/refund", data, {
      pathParams: {
        order_id: orderId,
      },
    });
  },

  repeat(orderId: UUID): Promise<CartRead> {
    return apiClient.post("/orders/{order_id}/repeat", undefined, {
      pathParams: {
        order_id: orderId,
      },
    });
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
