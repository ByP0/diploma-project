export interface CartProductSnapshot {
  id: string;
  sku?: string;
  name: string;
  brand?: string | null;
  price: number;
  oldPrice?: number | null;
  unit: string;
  stock: number;
  reservedStock: number;
  imageUrl?: string | null;
  href?: string;
}

export interface CartItem {
  id: string;
  productId: string;
  quantity: number;
  unitPrice: number;
  subtotal: number;
  createdAt: string;
  updatedAt: string;
  expiresAt?: string | null;
  product: CartProductSnapshot;
}

export interface CartTotals {
  totalItems: number;
  totalAmount: number;
  totalDiscount: number;
  unavailableItems: number;
}

export interface CartState {
  id: string;
  mode: "guest" | "user";
  items: CartItem[];
  totals: CartTotals;
  expiresAt?: string | null;
  updatedAt: string;
}

export interface CartAddInput {
  product: CartProductSnapshot;
  quantity?: number;
}

export interface CartUpdateInput {
  productId: string;
  quantity: number;
}

export interface CartOperationResult {
  cart: CartState;
  message?: string;
}

export interface BackendCartProductSummary {
  id: string;
  sku: string;
  name: string;
  brand: string | null;
  price: number | string;
  unit: string;
  stock: number;
  reserved_stock: number;
  photo_ids: string[];
  available_stock?: number;
  photo_urls?: string[];
  primary_photo_url?: string | null;
}

export interface BackendCartItemRead {
  id: string;
  product_id: string;
  quantity: number;
  subtotal: number | string;
  created_at: string;
  updated_at: string;
  expires_at: string;
  product: BackendCartProductSummary;
}

export interface BackendCartRead {
  items: BackendCartItemRead[];
  total_items: number;
  total_amount: number | string;
  guest_cart_id: string | null;
  expires_at: string | null;
  is_guest_cart?: boolean;
}
