import { apiClient } from "@shared/api";
import type { OrderCancelRequest, OrderRead, OrderStatusUpdate, UUID } from "@shared/api";

type ListAdminOrdersParams = {
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
};

type RequestOptions = {
  signal?: AbortSignal;
};

export const adminOrdersApi = {
  cancel(orderId: UUID, data: OrderCancelRequest): Promise<OrderRead> {
    return apiClient.post("/orders/management/{order_id}/cancel", data, {
      pathParams: {
        order_id: orderId,
      },
    });
  },

  getById(orderId: UUID, options?: RequestOptions): Promise<OrderRead> {
    return apiClient.get("/orders/management/{order_id}", {
      pathParams: {
        order_id: orderId,
      },
      signal: options?.signal,
    });
  },

  list(params: ListAdminOrdersParams = {}): Promise<OrderRead[]> {
    return apiClient.get("/orders/management/list", {
      query: {
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      },
      signal: params.signal,
    });
  },

  updateStatus(orderId: UUID, data: OrderStatusUpdate): Promise<OrderRead> {
    return apiClient.patch("/orders/{order_id}/status", data, {
      pathParams: {
        order_id: orderId,
      },
    });
  },
};
