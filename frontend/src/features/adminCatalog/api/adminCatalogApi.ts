import { apiClient } from "@shared/api";
import type {
  CategoryCreate,
  CategoryRead,
  CategoryUpdate,
  ImageUploadResponse,
  MessageResponse,
  ProductCreate,
  ProductRead,
  ProductUpdate,
  UUID,
} from "@shared/api";

type RequestOptions = {
  signal?: AbortSignal;
};

export type AdminProductFilters = {
  active_only?: boolean;
  category_id?: number;
  limit?: number;
  offset?: number;
  search?: string;
};

export const adminCatalogApi = {
  createCategory(data: CategoryCreate): Promise<CategoryRead> {
    return apiClient.post("/categories", data);
  },

  createProduct(data: ProductCreate): Promise<ProductRead> {
    return apiClient.post("/products", data);
  },

  deleteCategory(categoryId: number): Promise<MessageResponse> {
    return apiClient.delete("/categories/{category_id}", {
      pathParams: {
        category_id: categoryId,
      },
    });
  },

  deleteImage(imageId: string): Promise<MessageResponse> {
    return apiClient.delete("/images/{image_id}", {
      pathParams: {
        image_id: imageId,
      },
    });
  },

  deleteProduct(productId: UUID): Promise<MessageResponse> {
    return apiClient.delete("/products/{product_id}", {
      pathParams: {
        product_id: productId,
      },
    });
  },

  listCategories(options: RequestOptions = {}): Promise<CategoryRead[]> {
    return apiClient.get("/categories", {
      query: {
        limit: 100,
        offset: 0,
      },
      signal: options.signal,
    });
  },

  listProducts(filters: AdminProductFilters = {}, options: RequestOptions = {}): Promise<ProductRead[]> {
    return apiClient.get("/products", {
      query: {
        active_only: filters.active_only ?? false,
        category_id: filters.category_id,
        limit: filters.limit ?? 100,
        offset: filters.offset ?? 0,
        search: filters.search,
      },
      signal: options.signal,
    });
  },

  updateCategory(categoryId: number, data: CategoryUpdate): Promise<CategoryRead> {
    return apiClient.put("/categories/{category_id}", data, {
      pathParams: {
        category_id: categoryId,
      },
    });
  },

  updateProduct(productId: UUID, data: ProductUpdate): Promise<ProductRead> {
    return apiClient.put("/products/{product_id}", data, {
      pathParams: {
        product_id: productId,
      },
    });
  },

  uploadImage(file: File): Promise<ImageUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post("/images", formData);
  },
};
