import * as React from "react";

import { productDetailsMockApi } from "./product-details.mock-api";
import type { ProductDetailsResponse, ProductPriceQuote } from "./product-details.types";

export interface UseProductDetailsState {
  data: ProductDetailsResponse | null;
  quote: ProductPriceQuote | null;
  loading: boolean;
  quoteLoading: boolean;
  error: string | null;
  reload: () => void;
}

export function useProductDetails(productId: string, quantity: number): UseProductDetailsState {
  const [data, setData] = React.useState<ProductDetailsResponse | null>(null);
  const [quote, setQuote] = React.useState<ProductPriceQuote | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [quoteLoading, setQuoteLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [reloadToken, setReloadToken] = React.useState(0);

  React.useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(null);

    productDetailsMockApi
      .getProduct(productId)
      .then((response) => {
        if (!cancelled) {
          setData(response);
        }
      })
      .catch((requestError: unknown) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить товар");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [productId, reloadToken]);

  React.useEffect(() => {
    if (!data) {
      return;
    }

    let cancelled = false;
    setQuoteLoading(true);

    productDetailsMockApi
      .getPriceQuote(productId, quantity)
      .then((response) => {
        if (!cancelled) {
          setQuote(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setQuote(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setQuoteLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [data, productId, quantity]);

  return {
    data,
    quote,
    loading,
    quoteLoading,
    error,
    reload: () => setReloadToken((value) => value + 1),
  };
}
