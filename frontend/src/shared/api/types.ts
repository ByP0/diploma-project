// API contract described from the backend FastAPI OpenAPI source
// (backend/app/schemas and backend/app/api routers). Keep names aligned with
// OpenAPI component schema names so this file can be replaced by a generator.

export type UUID = string;
export type DateTime = string;
export type DecimalString = string | number;

export type UserRole = "admin" | "manager" | "support" | "user";
export type ProductUnit = "г" | "кг" | "л" | "мл" | "уп" | "шт";
export type DeliveryMethod = "courier" | "express" | "pickup";
export type PaymentMethod = "card_on_delivery" | "card_online" | "cash_on_delivery";
export type PaymentStatus = "cancelled" | "failed" | "partially_refunded" | "pending" | "refunded" | "succeeded";
export type SupportMessageAuthor = "admin" | "ai" | "customer";
export type SupportTicketPriority = "high" | "low" | "normal" | "urgent";
export type SupportTicketStatus = "closed" | "in_progress" | "open" | "resolved" | "waiting_customer";
export type OrderStatus =
  | "awaiting_payment"
  | "cancelled"
  | "created"
  | "delivered"
  | "failed"
  | "packed"
  | "paid"
  | "processing"
  | "refunded"
  | "shipped";

export type OrderStatusUpdate = {
  reason?: string | null;
  status: OrderStatus;
};

export type ValidationErrorItem = {
  error_type: string;
  field: string;
  message: string;
};

export type ErrorResponse = {
  detail: string;
  errors?: ValidationErrorItem[] | null;
};

export type MessageResponse = {
  detail: string;
};

export type ImageUploadResponse = {
  content_type: string;
  filename: string;
  id: string;
  size_bytes: number;
  url: string;
};

export type HealthResponse = {
  detail: string;
  status: string;
};

export type ChatRequest = {
  contact_email?: string | null;
  message: string;
  request_human?: boolean;
  ticket_id?: UUID | null;
};

export type ChatResponse = {
  answer: string;
  human_handoff_requested: boolean;
  ticket_id: UUID;
  ticket_status: SupportTicketStatus;
  used_ai: boolean;
  used_user_context: boolean;
};

export type SupportMessageRead = {
  author_name: string | null;
  author_type: SupportMessageAuthor;
  body: string;
  created_at: DateTime;
  id: UUID;
};

export type SupportTicketSummary = {
  ai_last_used: boolean;
  contact_email: string | null;
  created_at: DateTime;
  human_handoff_requested: boolean;
  id: UUID;
  last_admin_reply_at: DateTime | null;
  last_customer_message_at: DateTime | null;
  last_message_preview: string;
  priority: SupportTicketPriority;
  status: SupportTicketStatus;
  subject: string;
  updated_at: DateTime;
};

export type SupportTicketRead = SupportTicketSummary & {
  assigned_admin_id: UUID | null;
  messages: SupportMessageRead[];
};

export type SupportTicketListResponse = {
  items: SupportTicketSummary[];
};

export type SupportAdminReplyCreate = {
  message: string;
  status?: SupportTicketStatus | null;
};

export type SupportTicketAdminUpdate = {
  assigned_admin_id?: UUID | null;
  priority?: SupportTicketPriority | null;
  status?: SupportTicketStatus | null;
};

export type NotificationMessageRead = {
  attempts: number;
  body_html: string | null;
  body_text: string;
  channel: string;
  context_payload: Record<string, unknown> | null;
  created_at: DateTime;
  id: UUID;
  last_error: string | null;
  max_attempts: number;
  next_retry_at: DateTime | null;
  provider_name: string | null;
  recipient: string;
  sent_at: DateTime | null;
  status: string;
  subject: string;
  template_name: string;
};

export type CategoryCreate = {
  id: number;
  name: string;
  slug: string;
};

export type CategoryRead = {
  created_at: DateTime;
  id: number;
  name: string;
  slug: string;
  updated_at: DateTime;
};

export type CategoryUpdate = {
  name?: string | null;
  slug?: string | null;
};

export type UserCreate = {
  email: string;
  name?: string | null;
  password: string;
};

export type UserLogin = {
  email: string;
  password: string;
};

export type UserPasswordRecoveryRequest = {
  email: string;
};

export type UserPasswordReset = {
  new_password: string;
  token: string;
};

export type EmailVerificationStubRequest = {
  email: string;
};

export type EmailVerificationConfirmStub = {
  token: string;
};

export type UserRead = {
  avatar_image_id: string | null;
  avatar_url: string | null;
  blocked_at: DateTime | null;
  blocked_reason: string | null;
  created_at: DateTime;
  email: string;
  email_verified_at: DateTime | null;
  id: UUID;
  is_active: boolean;
  is_blocked: boolean;
  is_email_verified: boolean;
  name: string | null;
  permissions: string[];
  role: UserRole;
  updated_at: DateTime;
};

export type UserProfileUpdate = {
  current_password?: string | null;
  name?: string | null;
  new_password?: string | null;
};

export type UserAdminUpdate = {
  blocked_reason?: string | null;
  email_verified?: boolean | null;
  is_active?: boolean | null;
  is_blocked?: boolean | null;
  role?: UserRole | null;
};

export type UserLoginAuditRead = {
  created_at: DateTime;
  email: string;
  event_type: string;
  failure_reason: string | null;
  id: UUID;
  ip_address: string | null;
  success: boolean;
  user_agent: string | null;
  user_id: UUID | null;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type ProductRead = {
  brand: string | null;
  category_id: number;
  created_at: DateTime;
  description: string;
  id: UUID;
  is_active: boolean;
  name: string;
  photo_ids: string[];
  photo_urls: string[];
  price: DecimalString;
  primary_photo_url: string | null;
  sku: string;
  stock: number;
  unit: ProductUnit;
  updated_at: DateTime;
};

export type ProductCreate = {
  brand?: string | null;
  category_id: number;
  description: string;
  is_active?: boolean;
  name: string;
  photo_ids?: string[];
  price: DecimalString;
  sku: string;
  stock: number;
  unit?: ProductUnit;
};

export type ProductUpdate = Partial<ProductCreate>;

export type CartItemCreate = {
  product_id: UUID;
  quantity: number;
};

export type CartItemUpdate = {
  quantity: number;
};

export type GuestCartSessionRead = {
  expires_at: DateTime;
  guest_cart_id: string;
};

export type DeliveryQuoteRequest = {
  city?: string | null;
  country?: string;
  delivery_method: DeliveryMethod;
  order_amount: DecimalString;
  region?: string | null;
};

export type DeliveryQuoteRead = {
  cost: DecimalString;
  currency: string;
  delivery_method: DeliveryMethod;
  details: Record<string, string>;
  estimated_days: number;
  provider_name: string;
};

export type PaymentWebhookPayload = {
  external_payment_id: string;
  status: PaymentStatus;
};

export type DeliveryWebhookPayload = {
  delivered?: boolean;
  external_delivery_id?: string | null;
  status: string;
  tracking_number?: string | null;
};

export type DeliveryAddressCreate = {
  apartment?: string | null;
  city: string;
  country?: string;
  entrance?: string | null;
  floor?: string | null;
  instructions?: string | null;
  intercom?: string | null;
  is_default?: boolean;
  label?: string | null;
  line1: string;
  line2?: string | null;
  phone: string;
  postal_code?: string | null;
  recipient_name: string;
  region?: string | null;
};

export type DeliveryAddressUpdate = Partial<DeliveryAddressCreate>;

export type DeliveryAddressRead = {
  apartment: string | null;
  city: string;
  country: string;
  created_at: DateTime;
  entrance: string | null;
  floor: string | null;
  id: UUID;
  instructions: string | null;
  intercom: string | null;
  is_default: boolean;
  label: string | null;
  line1: string;
  line2: string | null;
  phone: string;
  postal_code: string | null;
  recipient_name: string;
  region: string | null;
  updated_at: DateTime;
};

export type CartProductSummary = {
  available_stock: number;
  brand: string | null;
  id: UUID;
  name: string;
  photo_ids: string[];
  photo_urls: string[];
  price: DecimalString;
  primary_photo_url: string | null;
  reserved_stock: number;
  sku: string;
  stock: number;
  unit: string;
};

export type CartItemRead = {
  created_at: DateTime;
  expires_at: DateTime;
  id: UUID;
  product: CartProductSummary;
  product_id: UUID;
  quantity: number;
  subtotal: DecimalString;
  updated_at: DateTime;
};

export type CartRead = {
  expires_at: DateTime | null;
  guest_cart_id: string | null;
  is_guest_cart: boolean;
  items: CartItemRead[];
  total_amount: DecimalString;
  total_items: number;
};

export type OrderItemRead = {
  id: UUID;
  line_total: DecimalString;
  product_id: UUID | null;
  product_name: string;
  quantity: number;
  returned_quantity: number;
  unit_price: DecimalString;
};

export type PaymentTransactionRead = {
  amount: DecimalString;
  created_at: DateTime;
  currency: string;
  external_payment_id: string | null;
  failure_code: string | null;
  failure_reason: string | null;
  id: UUID;
  operation_type: string;
  parent_transaction_id: UUID | null;
  payment_method: PaymentMethod;
  processed_at: DateTime | null;
  provider_name: string;
  redirect_url: string | null;
  status: PaymentStatus;
};

export type DeliveryShipmentRead = {
  created_at: DateTime;
  delivered_at: DateTime | null;
  delivery_method: DeliveryMethod;
  external_delivery_id: string | null;
  id: UUID;
  provider_name: string;
  quoted_cost: DecimalString;
  shipped_at: DateTime | null;
  status: string;
  tracking_number: string | null;
};

export type OrderStatusHistoryRead = {
  actor_role: string | null;
  actor_user_id: UUID | null;
  created_at: DateTime;
  from_status: string | null;
  id: UUID;
  reason: string | null;
  to_status: string;
};

export type OrderRead = {
  cancellation_reason: string | null;
  created_at: DateTime;
  currency: string;
  customer_comment: string | null;
  customer_email: string | null;
  customer_name: string | null;
  customer_phone: string | null;
  delivery_address_line1: string | null;
  delivery_address_line2: string | null;
  delivery_apartment: string | null;
  delivery_city: string | null;
  delivery_cost: DecimalString;
  delivery_country: string;
  delivery_entrance: string | null;
  delivery_floor: string | null;
  delivery_instructions: string | null;
  delivery_intercom: string | null;
  delivery_method: DeliveryMethod;
  delivery_postal_code: string | null;
  delivery_region: string | null;
  delivery_shipments: DeliveryShipmentRead[];
  delivery_window_end: DateTime | null;
  delivery_window_start: DateTime | null;
  id: UUID;
  invoice_number: string | null;
  items: OrderItemRead[];
  items_total_amount: DecimalString;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  payment_transactions: PaymentTransactionRead[];
  price_locked_at: DateTime;
  receipt_number: string | null;
  status: OrderStatus;
  status_history: OrderStatusHistoryRead[];
  total_amount: DecimalString;
  updated_at: DateTime;
};

export type OrderCheckoutCreate = {
  currency?: string;
  customer_comment?: string | null;
  customer_name: string;
  customer_phone: string;
  delivery_address_line1?: string | null;
  delivery_address_line2?: string | null;
  delivery_apartment?: string | null;
  delivery_city?: string | null;
  delivery_country?: string;
  delivery_entrance?: string | null;
  delivery_floor?: string | null;
  delivery_instructions?: string | null;
  delivery_intercom?: string | null;
  delivery_method?: DeliveryMethod;
  delivery_postal_code?: string | null;
  delivery_region?: string | null;
  delivery_window_end?: DateTime | null;
  delivery_window_start?: DateTime | null;
  payment_method?: PaymentMethod;
  payment_provider?: string | null;
};

export type CheckoutPreviewRead = {
  calculated_at: DateTime;
  currency: string;
  delivery_cost: DecimalString;
  delivery_method: DeliveryMethod;
  items: Array<{
    line_total: DecimalString;
    product_id: UUID;
    product_name: string;
    quantity: number;
    unit_price: DecimalString;
  }>;
  items_total_amount: DecimalString;
  payment_method: PaymentMethod;
  total_amount: DecimalString;
};

export type OrderCancelRequest = {
  reason?: string | null;
};

export type OrderRefundItemRequest = {
  order_item_id: UUID;
  quantity: number;
};

export type OrderRefundRequest = {
  idempotency_key?: string | null;
  items: OrderRefundItemRequest[];
  reason?: string | null;
};

export type OrderDocumentRead = {
  amount: DecimalString;
  currency: string;
  document_number: string;
  document_type: string;
  issued_at: DateTime;
  items: OrderItemRead[];
  order_id: UUID;
};

export type ApiPaths = {
  "/auth/login": {
    post: {
      body: UserLogin;
      response: UserRead;
    };
  };
  "/auth/logout": {
    post: {
      body: undefined;
      response: void;
    };
  };
  "/auth/password/recover": {
    post: {
      body: UserPasswordRecoveryRequest;
      response: MessageResponse;
    };
  };
  "/auth/password/reset": {
    post: {
      body: UserPasswordReset;
      response: MessageResponse;
    };
  };
  "/auth/refresh": {
    post: {
      body: undefined;
      response: TokenPair;
    };
  };
  "/auth/register": {
    post: {
      body: UserCreate;
      response: UserRead;
    };
  };
  "/auth/email-verification/confirm": {
    post: {
      body: EmailVerificationConfirmStub;
      response: MessageResponse;
    };
  };
  "/auth/email-verification/request": {
    post: {
      body: EmailVerificationStubRequest;
      response: MessageResponse;
    };
  };
  "/cart": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    get: {
      body: undefined;
      response: CartRead;
    };
  };
  "/cart/items": {
    post: {
      body: CartItemCreate;
      response: CartRead;
    };
  };
  "/cart/items/{product_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    put: {
      body: CartItemUpdate;
      response: CartRead;
    };
  };
  "/cart/guest/sessions": {
    post: {
      body: undefined;
      response: GuestCartSessionRead;
    };
  };
  "/cart/guest/{guest_cart_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    get: {
      body: undefined;
      response: CartRead;
    };
  };
  "/cart/guest/{guest_cart_id}/items": {
    post: {
      body: CartItemCreate;
      response: CartRead;
    };
  };
  "/cart/guest/{guest_cart_id}/items/{product_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    put: {
      body: CartItemUpdate;
      response: CartRead;
    };
  };
  "/categories": {
    get: {
      body: undefined;
      response: CategoryRead[];
    };
    post: {
      body: CategoryCreate;
      response: CategoryRead;
    };
  };
  "/categories/{category_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    get: {
      body: undefined;
      response: CategoryRead;
    };
    put: {
      body: CategoryUpdate;
      response: CategoryRead;
    };
  };
  "/chat": {
    post: {
      body: ChatRequest;
      response: ChatResponse;
    };
  };
  "/checkout/preview": {
    post: {
      body: OrderCheckoutCreate;
      response: CheckoutPreviewRead;
    };
  };
  "/delivery/quote": {
    post: {
      body: DeliveryQuoteRequest;
      response: DeliveryQuoteRead;
    };
  };
  "/delivery/webhooks/{provider_name}": {
    post: {
      body: DeliveryWebhookPayload;
      response: MessageResponse;
    };
  };
  "/delivery/addresses": {
    get: {
      body: undefined;
      response: DeliveryAddressRead[];
    };
    post: {
      body: DeliveryAddressCreate;
      response: DeliveryAddressRead;
    };
  };
  "/delivery/addresses/{address_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    patch: {
      body: DeliveryAddressUpdate;
      response: DeliveryAddressRead;
    };
  };
  "/images": {
    post: {
      body: FormData;
      response: ImageUploadResponse;
    };
  };
  "/images/{image_id}": {
    get: {
      body: undefined;
      response: Blob;
    };
    delete: {
      body: undefined;
      response: MessageResponse;
    };
  };
  "/notifications/messages": {
    get: {
      body: undefined;
      response: NotificationMessageRead[];
    };
  };
  "/notifications/process": {
    post: {
      body: undefined;
      response: MessageResponse;
    };
  };
  "/orders": {
    get: {
      body: undefined;
      response: OrderRead[];
    };
  };
  "/orders/from-cart": {
    post: {
      body: OrderCheckoutCreate;
      response: OrderRead;
    };
  };
  "/orders/{order_id}": {
    get: {
      body: undefined;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/cancel": {
    post: {
      body: OrderCancelRequest;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/documents/{document_type}": {
    get: {
      body: undefined;
      response: OrderDocumentRead;
    };
  };
  "/orders/{order_id}/payments/retry": {
    post: {
      body: undefined;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/payments/sync": {
    post: {
      body: undefined;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/status": {
    patch: {
      body: OrderStatusUpdate;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/refund": {
    post: {
      body: OrderRefundRequest;
      response: OrderRead;
    };
  };
  "/orders/{order_id}/repeat": {
    post: {
      body: undefined;
      response: CartRead;
    };
  };
  "/orders/management/list": {
    get: {
      body: undefined;
      response: OrderRead[];
    };
  };
  "/orders/management/{order_id}": {
    get: {
      body: undefined;
      response: OrderRead;
    };
  };
  "/orders/management/{order_id}/cancel": {
    post: {
      body: OrderCancelRequest;
      response: OrderRead;
    };
  };
  "/payments/orders/{order_id}/recheck": {
    post: {
      body: undefined;
      response: OrderRead;
    };
  };
  "/payments/webhooks/{provider_name}": {
    post: {
      body: PaymentWebhookPayload;
      response: MessageResponse;
    };
  };
  "/products": {
    get: {
      body: undefined;
      response: ProductRead[];
    };
    post: {
      body: ProductCreate;
      response: ProductRead;
    };
  };
  "/products/{product_id}": {
    delete: {
      body: undefined;
      response: MessageResponse;
    };
    get: {
      body: undefined;
      response: ProductRead;
    };
    put: {
      body: ProductUpdate;
      response: ProductRead;
    };
  };
  "/support/tickets/me": {
    get: {
      body: undefined;
      response: SupportTicketListResponse;
    };
  };
  "/support/tickets/me/{ticket_id}": {
    get: {
      body: undefined;
      response: SupportTicketRead;
    };
  };
  "/support/tickets": {
    get: {
      body: undefined;
      response: SupportTicketListResponse;
    };
  };
  "/support/tickets/admin/{ticket_id}": {
    get: {
      body: undefined;
      response: SupportTicketRead;
    };
  };
  "/support/tickets/{ticket_id}": {
    patch: {
      body: SupportTicketAdminUpdate;
      response: SupportTicketRead;
    };
  };
  "/support/tickets/{ticket_id}/admin-reply": {
    post: {
      body: SupportAdminReplyCreate;
      response: SupportTicketRead;
    };
  };
  "/users": {
    get: {
      body: undefined;
      response: UserRead[];
    };
  };
  "/users/login-audit": {
    get: {
      body: undefined;
      response: UserLoginAuditRead[];
    };
  };
  "/users/me": {
    get: {
      body: undefined;
      response: UserRead;
    };
    patch: {
      body: UserProfileUpdate;
      response: UserRead;
    };
  };
  "/users/me/avatar": {
    delete: {
      body: undefined;
      response: UserRead;
    };
    post: {
      body: FormData;
      response: UserRead;
    };
  };
  "/users/{user_id}/access": {
    patch: {
      body: UserAdminUpdate;
      response: UserRead;
    };
  };
};

export type ApiPath = keyof ApiPaths;
export type ApiMethod = "delete" | "get" | "patch" | "post" | "put";
export type ApiOperation<TPath extends ApiPath, TMethod extends ApiMethod> = TMethod extends keyof ApiPaths[TPath]
  ? ApiPaths[TPath][TMethod]
  : never;
export type ApiRequestBody<TPath extends ApiPath, TMethod extends ApiMethod> =
  ApiOperation<TPath, TMethod> extends { body: infer TBody } ? TBody : never;
export type ApiResponseBody<TPath extends ApiPath, TMethod extends ApiMethod> =
  ApiOperation<TPath, TMethod> extends { response: infer TResponse } ? TResponse : never;
