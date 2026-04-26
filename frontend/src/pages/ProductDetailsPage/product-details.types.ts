export interface ProductImage {
  id: string;
  url: string;
  alt: string;
}

export interface ProductCharacteristic {
  label: string;
  value: string;
}

export interface ProductPricingTier {
  minQuantity: number;
  unitPrice: number;
  label: string;
}

export interface ProductReview {
  id: string;
  author: string;
  rating: number;
  createdAt: string;
  title: string;
  text: string;
  verifiedPurchase: boolean;
}

export interface RelatedProduct {
  id: string;
  title: string;
  href: string;
  imageUrl: string;
  price: number;
  unit: string;
  rating: number;
  stock: number;
}

export interface DeliveryEstimate {
  method: "courier" | "express" | "pickup";
  title: string;
  description: string;
  price: number;
  eta: string;
}

export type ProductStockStatus = "in_stock" | "low_stock" | "out_of_stock";

export interface ProductDetails {
  id: string;
  sku: string;
  title: string;
  brand: string;
  brandHref: string;
  category: string;
  categoryHref: string;
  rating: number;
  reviewsCount: number;
  description: string;
  images: ProductImage[];
  characteristics: ProductCharacteristic[];
  stock: number;
  reservedStock: number;
  unit: string;
  basePrice: number;
  oldPrice?: number;
  currency: "RUB";
  pricingTiers: ProductPricingTier[];
  isFavorite: boolean;
  relatedProducts: RelatedProduct[];
  reviews: ProductReview[];
  deliveryEstimates: DeliveryEstimate[];
}

export interface ProductDetailsResponse {
  product: ProductDetails;
  availableQuantity: number;
  stockStatus: ProductStockStatus;
  urgencyLabel?: string;
}

export interface ProductPriceQuote {
  productId: string;
  quantity: number;
  unitPrice: number;
  oldUnitPrice?: number;
  subtotal: number;
  discountAmount: number;
  currency: "RUB";
  appliedTier?: ProductPricingTier;
}

export interface AddToCartPayload {
  productId: string;
  quantity: number;
}

export interface AddToCartResult {
  cartItems: number;
  productId: string;
  quantity: number;
}
