# API layer

`types.ts` mirrors the backend OpenAPI component names and path names. It is described from
`backend/app/schemas` and `backend/app/api` and is intentionally isolated so a future OpenAPI
generator can replace it without touching callers.

```ts
import { apiClient, isApiError } from "@shared/api";

const products = await apiClient.get("/products", {
  query: { limit: 20, active_only: true },
});

const product = await apiClient.get("/products/{product_id}", {
  pathParams: { product_id: "550e8400-e29b-41d4-a716-446655440000" },
});

try {
  await apiClient.post("/cart/items", {
    product_id: product.id,
    quantity: 1,
  });
} catch (error) {
  if (isApiError(error) && error.kind === "validation") {
    console.warn(error.validationErrors, error.correlationId);
  }
}
```

Client behavior:

- sends `credentials: "include"` for cookie auth;
- sends `X-CSRF-Token` from `csrf_token` cookie for unsafe methods;
- sends `X-Correlation-ID` on every request and stores the last response/request id;
- refreshes once through `POST /api/auth/refresh` after a `401`, then retries the original request;
- normalizes `401`, `403`, `422`, `429`, and server errors into `ApiError`.
