import { apiClient } from "@shared/api";
import type { CategoryRead, ProductRead } from "@shared/api";

export type ProductFilters = {
  active_only: boolean;
  category_id?: number;
  limit: number;
  max_price?: number;
  min_price?: number;
  offset: number;
  search?: string;
};

type RequestOptions = {
  signal?: AbortSignal;
};

export const catalogApi = {
  getCategories(options: RequestOptions = {}): Promise<CategoryRead[]> {
    return apiClient.get("/categories", {
      query: {
        limit: 100,
        offset: 0,
      },
      signal: options.signal,
    });
  },

  getProducts(filters: ProductFilters, options: RequestOptions = {}): Promise<ProductRead[]> {
    return apiClient.get("/products", {
      query: {
        active_only: filters.active_only,
        category_id: filters.category_id,
        limit: filters.limit,
        max_price: filters.max_price,
        min_price: filters.min_price,
        offset: filters.offset,
        search: filters.search,
      },
      signal: options.signal,
    });
  },

  getProduct(productId: string, options: RequestOptions = {}): Promise<ProductRead> {
    return apiClient.get("/products/{product_id}", {
      pathParams: {
        product_id: productId,
      },
      signal: options.signal,
    });
  },
};
