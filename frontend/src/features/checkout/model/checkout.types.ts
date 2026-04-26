export type CheckoutStepId = "items" | "address" | "delivery" | "payment" | "summary";

export type DeliveryMethod = "courier" | "express" | "pickup";

export type PaymentMethod = "card_online" | "cash_on_delivery" | "card_on_delivery";

export type PaymentProviderId = "stub_auto" | "stub_redirect";

export type OrderStatus =
  | "created"
  | "awaiting_payment"
  | "paid"
  | "processing"
  | "packed"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "refunded"
  | "failed";

export type PaymentStatus = "pending" | "succeeded" | "failed" | "cancelled" | "refunded" | "partially_refunded";

export interface CheckoutFormState {
  customerName: string;
  customerPhone: string;
  customerComment: string;
  deliveryMethod: DeliveryMethod;
  deliveryWindowId: string;
  deliveryAddressLine1: string;
  deliveryAddressLine2: string;
  deliveryCity: string;
  deliveryRegion: string;
  deliveryPostalCode: string;
  deliveryCountry: string;
  deliveryFloor: string;
  deliveryApartment: string;
  deliveryEntrance: string;
  deliveryIntercom: string;
  deliveryInstructions: string;
  paymentMethod: PaymentMethod;
  paymentProvider: PaymentProviderId;
  currency: "RUB";
}

export type CheckoutField = keyof CheckoutFormState;

export type CheckoutFieldErrors = Partial<Record<CheckoutField | "cart", string>>;

export interface DeliveryOption {
  id: DeliveryMethod;
  title: string;
  description: string;
  eta: string;
  badge?: string;
  priceHint: string;
}

export interface DeliveryWindowOption {
  id: string;
  title: string;
  description: string;
  start: string;
  end: string;
}

export interface PaymentOption {
  id: PaymentMethod;
  title: string;
  description: string;
  badge?: string;
}

export interface PaymentProviderOption {
  id: PaymentProviderId;
  title: string;
  description: string;
  commissionLabel: string;
}

export interface CheckoutPayload {
  customer_name: string;
  customer_phone: string;
  customer_comment?: string | null;
  delivery_method: DeliveryMethod;
  payment_method: PaymentMethod;
  payment_provider?: string | null;
  delivery_window_start?: string | null;
  delivery_window_end?: string | null;
  delivery_address_line1?: string | null;
  delivery_address_line2?: string | null;
  delivery_city?: string | null;
  delivery_region?: string | null;
  delivery_postal_code?: string | null;
  delivery_country: string;
  delivery_floor?: string | null;
  delivery_apartment?: string | null;
  delivery_entrance?: string | null;
  delivery_intercom?: string | null;
  delivery_instructions?: string | null;
  currency: "RUB";
}

export interface CheckoutLineRead {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number | string;
  line_total: number | string;
}

export interface CheckoutPreviewRead {
  items: CheckoutLineRead[];
  items_total_amount: number | string;
  delivery_cost: number | string;
  total_amount: number | string;
  currency: string;
  delivery_method: DeliveryMethod;
  payment_method: PaymentMethod;
  calculated_at: string;
}

export interface OrderItemRead {
  id: string;
  product_id: string | null;
  product_name: string;
  unit_price: number | string;
  quantity: number;
  returned_quantity: number;
  line_total: number | string;
}

export interface PaymentTransactionRead {
  id: string;
  provider_name: string;
  operation_type: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  amount: number | string;
  currency: string;
  external_payment_id: string | null;
  redirect_url: string | null;
  failure_code: string | null;
  failure_reason: string | null;
  processed_at: string | null;
  created_at: string;
}

export interface DeliveryShipmentRead {
  id: string;
  provider_name: string;
  delivery_method: DeliveryMethod;
  status: string;
  quoted_cost: number | string;
  tracking_number: string | null;
  created_at: string;
}

export interface OrderRead {
  id: string;
  status: OrderStatus;
  items_total_amount: number | string;
  delivery_cost: number | string;
  total_amount: number | string;
  price_locked_at: string;
  customer_email: string | null;
  customer_name: string | null;
  customer_phone: string | null;
  customer_comment: string | null;
  delivery_method: DeliveryMethod;
  delivery_window_start: string | null;
  delivery_window_end: string | null;
  delivery_address_line1: string | null;
  delivery_address_line2: string | null;
  delivery_city: string | null;
  delivery_region: string | null;
  delivery_postal_code: string | null;
  delivery_country: string;
  delivery_floor: string | null;
  delivery_apartment: string | null;
  delivery_entrance: string | null;
  delivery_intercom: string | null;
  delivery_instructions: string | null;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  currency: string;
  cancellation_reason: string | null;
  invoice_number: string | null;
  receipt_number: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItemRead[];
  payment_transactions: PaymentTransactionRead[];
  delivery_shipments: DeliveryShipmentRead[];
}
