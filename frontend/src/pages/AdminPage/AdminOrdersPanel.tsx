import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminOrdersApi } from "@features/adminOrders/api/adminOrdersApi";
import { isApiError } from "@shared/api";
import type {
  DecimalString,
  DeliveryShipmentRead,
  OrderItemRead,
  OrderRead,
  OrderStatus,
  OrderStatusHistoryRead,
  PaymentStatus,
  PaymentTransactionRead,
  UUID,
} from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, SelectField, TextField, useToast } from "@shared/ui";

const PAGE_SIZE = 20;

const ORDER_STATUS_OPTIONS: Array<{ label: string; value: OrderStatus }> = [
  { label: "Created", value: "created" },
  { label: "Awaiting payment", value: "awaiting_payment" },
  { label: "Paid", value: "paid" },
  { label: "Processing", value: "processing" },
  { label: "Packed", value: "packed" },
  { label: "Shipped", value: "shipped" },
  { label: "Delivered", value: "delivered" },
  { label: "Cancelled", value: "cancelled" },
  { label: "Refunded", value: "refunded" },
  { label: "Failed", value: "failed" },
];

const PAYMENT_STATUS_OPTIONS: Array<{ label: string; value: PaymentStatus | "all" }> = [
  { label: "All payments", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Succeeded", value: "succeeded" },
  { label: "Failed", value: "failed" },
  { label: "Cancelled", value: "cancelled" },
  { label: "Refunded", value: "refunded" },
  { label: "Partially refunded", value: "partially_refunded" },
];

const ORDER_STATUS_FILTER_OPTIONS: Array<{ label: string; value: OrderStatus | "all" }> = [
  { label: "All order statuses", value: "all" },
  ...ORDER_STATUS_OPTIONS,
];

const ORDER_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  created: ["awaiting_payment", "paid", "processing", "cancelled", "failed"],
  awaiting_payment: ["paid", "cancelled", "failed"],
  paid: ["processing", "cancelled", "refunded"],
  processing: ["packed", "cancelled"],
  packed: ["shipped", "cancelled"],
  shipped: ["delivered", "cancelled"],
  delivered: ["refunded"],
  failed: ["awaiting_payment", "cancelled"],
  cancelled: [],
  refunded: [],
};

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Order request failed.";
}

function formatPrice(value: DecimalString, currency = "RUB") {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return String(value);
  }

  try {
    return new Intl.NumberFormat("ru-RU", {
      currency,
      maximumFractionDigits: 2,
      style: "currency",
    }).format(numberValue);
  } catch {
    return `${numberValue.toFixed(2)} ${currency}`;
  }
}

function formatDate(value: string | null) {
  if (!value) {
    return "not set";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getStatusLabel(status: string) {
  return status.replace(/_/g, " ");
}

function formatAddress(order: OrderRead) {
  return [
    order.delivery_address_line1,
    order.delivery_address_line2,
    order.delivery_city,
    order.delivery_region,
    order.delivery_postal_code,
    order.delivery_country,
  ]
    .filter(Boolean)
    .join(", ") || "pickup / no address";
}

function canAdminCancel(order: OrderRead) {
  return !["cancelled", "refunded"].includes(order.status);
}

type AdminOrderAction = "cancel" | "status" | null;

export function AdminOrdersPanel() {
  const { showToast } = useToast();
  const [action, setAction] = useState<AdminOrderAction>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailReloadKey, setDetailReloadKey] = useState(0);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isListLoading, setIsListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [page, setPage] = useState(0);
  const [paymentFilter, setPaymentFilter] = useState<PaymentStatus | "all">("all");
  const [query, setQuery] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedOrderId, setSelectedOrderId] = useState<UUID | null>(null);
  const [statusDraft, setStatusDraft] = useState<OrderStatus | "">("");
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "all">("all");
  const [statusReason, setStatusReason] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    setIsListLoading(true);
    setListError(null);
    adminOrdersApi
      .list({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        signal: controller.signal,
      })
      .then((payload) => {
        if (controller.signal.aborted) {
          return;
        }

        setOrders(payload);
        setSelectedOrderId((current) => (payload.some((order) => order.id === current) ? current : payload[0]?.id ?? null));
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setListError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsListLoading(false);
        }
      });

    return () => controller.abort();
  }, [page, reloadKey]);

  useEffect(() => {
    if (!selectedOrderId) {
      return undefined;
    }

    const controller = new AbortController();

    setIsDetailLoading(true);
    setDetailError(null);
    adminOrdersApi
      .getById(selectedOrderId, { signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          replaceOrder(payload);
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setDetailError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [detailReloadKey, selectedOrderId]);

  const selectedOrder = useMemo(
    () => orders.find((order) => order.id === selectedOrderId) ?? null,
    [orders, selectedOrderId],
  );

  const allowedStatuses = selectedOrder ? ORDER_TRANSITIONS[selectedOrder.status] : [];
  const statusOptions = allowedStatuses.map((status) => ({
    label: getStatusLabel(status),
    value: status,
  }));

  useEffect(() => {
    setStatusDraft(allowedStatuses[0] ?? "");
    setStatusReason("");
    setCancelReason("");
  }, [selectedOrder?.id, selectedOrder?.status]);

  const filteredOrders = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return orders.filter((order) => {
      const matchesStatus = statusFilter === "all" || order.status === statusFilter;
      const matchesPayment = paymentFilter === "all" || order.payment_status === paymentFilter;
      const matchesQuery =
        !normalizedQuery ||
        [
          order.id,
          order.customer_email ?? "",
          order.customer_name ?? "",
          order.customer_phone ?? "",
          order.status,
          order.payment_status,
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return matchesStatus && matchesPayment && matchesQuery;
    });
  }, [orders, paymentFilter, query, statusFilter]);

  const summary = useMemo(
    () => ({
      active: orders.filter((order) => !["cancelled", "delivered", "failed", "refunded"].includes(order.status)).length,
      awaitingPayment: orders.filter((order) => order.payment_status === "pending").length,
      loaded: orders.length,
      problem: orders.filter((order) => ["cancelled", "failed", "refunded"].includes(order.status)).length,
    }),
    [orders],
  );

  function replaceOrder(order: OrderRead) {
    setOrders((current) => {
      if (current.some((item) => item.id === order.id)) {
        return current.map((item) => (item.id === order.id ? order : item));
      }

      return [order, ...current];
    });
    setSelectedOrderId(order.id);
  }

  const refreshOrders = () => setReloadKey((current) => current + 1);
  const refreshSelectedOrder = () => setDetailReloadKey((current) => current + 1);

  const handleSelectOrder = (orderId: UUID) => {
    setSelectedOrderId(orderId);
    setDetailReloadKey((current) => current + 1);
    setDetailError(null);
  };

  const handleStatusSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedOrder) {
      return;
    }

    const nextStatus = statusDraft || ORDER_TRANSITIONS[selectedOrder.status][0];
    if (!nextStatus) {
      return;
    }

    setAction("status");
    setDetailError(null);

    try {
      const order = await adminOrdersApi.updateStatus(selectedOrder.id, {
        reason: statusReason.trim() || null,
        status: nextStatus,
      });
      replaceOrder(order);
      showToast({
        description: `${getStatusLabel(order.status)} / ${getStatusLabel(order.payment_status)}`,
        title: "Order status updated",
        variant: "success",
      });
    } catch (caughtError) {
      setDetailError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const handleCancelSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedOrder) {
      return;
    }

    setAction("cancel");
    setDetailError(null);

    try {
      const order = await adminOrdersApi.cancel(selectedOrder.id, {
        reason: cancelReason.trim() || "admin_cancelled",
      });
      replaceOrder(order);
      showToast({
        description: order.cancellation_reason || "Cancelled by administrator.",
        title: "Order cancelled",
        variant: "success",
      });
    } catch (caughtError) {
      setDetailError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const canGoNext = orders.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

  return (
    <section className="admin-orders" aria-label="Order management">
      <section className="admin-orders-summary" aria-label="Order summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.loaded}</strong>
        </article>
        <article className="surface-card">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </article>
        <article className="surface-card">
          <span>Awaiting payment</span>
          <strong>{summary.awaitingPayment}</strong>
        </article>
        <article className="surface-card">
          <span>Problem states</span>
          <strong>{summary.problem}</strong>
        </article>
      </section>

      <div className="admin-toolbar admin-orders-toolbar">
        <TextField
          label="Search"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Order ID, customer, phone"
          value={query}
        />
        <SelectField
          label="Order status"
          onChange={(event) => setStatusFilter(event.target.value as OrderStatus | "all")}
          options={ORDER_STATUS_FILTER_OPTIONS}
          value={statusFilter}
        />
        <SelectField
          label="Payment"
          onChange={(event) => setPaymentFilter(event.target.value as PaymentStatus | "all")}
          options={PAYMENT_STATUS_OPTIONS}
          value={paymentFilter}
        />
        <Button onClick={refreshOrders} variant="secondary">
          Refresh
        </Button>
      </div>

      {listError ? (
        <ErrorState
          action={
            <Button onClick={refreshOrders} variant="secondary">
              Retry
            </Button>
          }
          description={listError}
          title="Unable to load orders"
        />
      ) : null}

      <div className="admin-orders-layout">
        <aside className="admin-orders-list" aria-label="Admin order list">
          {isListLoading ? (
            <LoadingState description="Loading order queue." title="Loading orders" />
          ) : filteredOrders.length ? (
            <>
              <div className="admin-orders-list__items">
                {filteredOrders.map((order) => (
                  <button
                    className={order.id === selectedOrderId ? "admin-order-card is-active" : "admin-order-card"}
                    key={order.id}
                    onClick={() => handleSelectOrder(order.id)}
                    type="button"
                  >
                    <span>{formatDate(order.created_at)}</span>
                    <strong>{formatPrice(order.total_amount, order.currency)}</strong>
                    <small>{order.customer_email || order.customer_name || order.id}</small>
                    <span className="admin-order-card__badges">
                      <StatusBadge label={order.status} />
                      <StatusBadge label={order.payment_status} tone="payment" />
                    </span>
                  </button>
                ))}
              </div>
              <div className="admin-orders-pagination">
                <Button disabled={!canGoPrevious || isListLoading} onClick={() => setPage((current) => Math.max(0, current - 1))} size="sm" variant="secondary">
                  Previous
                </Button>
                <span>Page {page + 1}</span>
                <Button disabled={!canGoNext || isListLoading} onClick={() => setPage((current) => current + 1)} size="sm" variant="secondary">
                  Next
                </Button>
              </div>
            </>
          ) : (
            <EmptyState description="No orders match the current filters." title="No orders" />
          )}
        </aside>

        <section className="admin-orders-detail" aria-label="Admin order details">
          {isDetailLoading ? (
            <LoadingState description="Loading selected order details." title="Loading order" />
          ) : detailError ? (
            <ErrorState
              action={
                <Button onClick={refreshSelectedOrder} variant="secondary">
                  Retry
                </Button>
              }
              description={detailError}
              title="Order action failed"
            />
          ) : selectedOrder ? (
            <OrderDetail
              action={action}
              allowedStatuses={allowedStatuses}
              cancelReason={cancelReason}
              onCancelReasonChange={setCancelReason}
              onCancelSubmit={handleCancelSubmit}
              onStatusReasonChange={setStatusReason}
              onStatusSubmit={handleStatusSubmit}
              onStatusValueChange={(value) => setStatusDraft(value)}
              order={selectedOrder}
              statusDraft={statusDraft}
              statusOptions={statusOptions}
              statusReason={statusReason}
            />
          ) : (
            <EmptyState description="Select an order from the list." title="No order selected" />
          )}
        </section>
      </div>
    </section>
  );
}

type OrderDetailProps = {
  action: AdminOrderAction;
  allowedStatuses: OrderStatus[];
  cancelReason: string;
  onCancelReasonChange: (value: string) => void;
  onCancelSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onStatusReasonChange: (value: string) => void;
  onStatusSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onStatusValueChange: (value: OrderStatus) => void;
  order: OrderRead;
  statusDraft: OrderStatus | "";
  statusOptions: Array<{ label: string; value: OrderStatus }>;
  statusReason: string;
};

function OrderDetail({
  action,
  allowedStatuses,
  cancelReason,
  onCancelReasonChange,
  onCancelSubmit,
  onStatusReasonChange,
  onStatusSubmit,
  onStatusValueChange,
  order,
  statusDraft,
  statusOptions,
  statusReason,
}: OrderDetailProps) {
  const isBusy = Boolean(action);

  return (
    <div className="admin-orders-detail-stack">
      <section className="admin-order-hero">
        <div>
          <p>Order {order.id}</p>
          <h2>{formatPrice(order.total_amount, order.currency)}</h2>
          <span>{formatDate(order.created_at)}</span>
        </div>
        <div className="admin-order-status-group">
          <StatusBadge label={order.status} />
          <StatusBadge label={order.payment_status} tone="payment" />
        </div>
      </section>

      <section className="admin-order-actions-grid">
        <form className="admin-order-panel" onSubmit={onStatusSubmit}>
          <h3>Lifecycle status</h3>
          {allowedStatuses.length ? (
            <>
              <SelectField
                disabled={isBusy}
                label="Next status"
                onChange={(event) => onStatusValueChange(event.target.value as OrderStatus)}
                options={statusOptions}
                value={statusDraft || allowedStatuses[0]}
              />
              <TextField
                disabled={isBusy}
                label="Reason"
                maxLength={1000}
                onChange={(event) => onStatusReasonChange(event.target.value)}
                placeholder="Optional"
                value={statusReason}
              />
              <Button disabled={isBusy || !allowedStatuses.length} isLoading={action === "status"} type="submit">
                Apply status
              </Button>
            </>
          ) : (
            <p className="admin-order-muted">This order has no allowed next lifecycle status.</p>
          )}
        </form>

        <form className="admin-order-panel" onSubmit={onCancelSubmit}>
          <h3>Admin cancellation</h3>
          <TextField
            disabled={!canAdminCancel(order) || isBusy}
            label="Reason"
            maxLength={1000}
            onChange={(event) => onCancelReasonChange(event.target.value)}
            placeholder="admin_cancelled"
            value={cancelReason}
          />
          <Button disabled={!canAdminCancel(order) || isBusy} isLoading={action === "cancel"} type="submit" variant="danger">
            Cancel order
          </Button>
        </form>
      </section>

      <section className="admin-order-panel">
        <h3>Customer and delivery</h3>
        <div className="admin-order-info-grid">
          <InfoItem label="Customer" value={order.customer_name || "not set"} />
          <InfoItem label="Email" value={order.customer_email || "not set"} />
          <InfoItem label="Phone" value={order.customer_phone || "not set"} />
          <InfoItem label="Payment method" value={getStatusLabel(order.payment_method)} />
          <InfoItem label="Delivery method" value={getStatusLabel(order.delivery_method)} />
          <InfoItem label="Delivery cost" value={formatPrice(order.delivery_cost, order.currency)} />
          <InfoItem label="Window start" value={formatDate(order.delivery_window_start)} />
          <InfoItem label="Window end" value={formatDate(order.delivery_window_end)} />
          <InfoItem label="Address" value={formatAddress(order)} wide />
          {order.customer_comment ? <InfoItem label="Comment" value={order.customer_comment} wide /> : null}
          {order.cancellation_reason ? <InfoItem label="Cancellation reason" value={order.cancellation_reason} wide /> : null}
        </div>
      </section>

      <section className="admin-order-panel">
        <h3>Items</h3>
        <OrderItemsTable currency={order.currency} items={order.items} />
      </section>

      <section className="admin-order-panel">
        <h3>Payments</h3>
        <PaymentsTable currency={order.currency} payments={order.payment_transactions} />
      </section>

      <section className="admin-order-panel">
        <h3>Delivery history</h3>
        <DeliveryTable shipments={order.delivery_shipments} />
      </section>

      <section className="admin-order-panel">
        <h3>Status history</h3>
        <StatusHistoryTable history={order.status_history} />
      </section>
    </div>
  );
}

type StatusBadgeProps = {
  label: string;
  tone?: "default" | "payment";
};

function StatusBadge({ label, tone = "default" }: StatusBadgeProps) {
  return (
    <span className={tone === "payment" ? "admin-order-badge admin-order-badge--payment" : "admin-order-badge"}>
      {getStatusLabel(label)}
    </span>
  );
}

type InfoItemProps = {
  label: string;
  value: string;
  wide?: boolean;
};

function InfoItem({ label, value, wide = false }: InfoItemProps) {
  return (
    <article className={wide ? "admin-order-info-item is-wide" : "admin-order-info-item"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function OrderItemsTable({ currency, items }: { currency: string; items: OrderItemRead[] }) {
  return (
    <DataTable
      columns={[
        { key: "name", title: "Product", render: (item) => item.product_name },
        { align: "right", key: "quantity", title: "Qty", render: (item) => item.quantity },
        { align: "right", key: "returned", title: "Returned", render: (item) => item.returned_quantity },
        {
          align: "right",
          key: "unit",
          title: "Unit price",
          render: (item) => formatPrice(item.unit_price, currency),
        },
        {
          align: "right",
          key: "total",
          title: "Line total",
          render: (item) => formatPrice(item.line_total, currency),
        },
      ]}
      empty={<EmptyState description="Order contains no line items." title="No items" />}
      getRowKey={(item) => item.id}
      rows={items}
    />
  );
}

function PaymentsTable({ currency, payments }: { currency: string; payments: PaymentTransactionRead[] }) {
  return (
    <DataTable
      columns={[
        { key: "created", title: "Created", render: (payment) => formatDate(payment.created_at) },
        { key: "provider", title: "Provider", render: (payment) => payment.provider_name },
        { key: "operation", title: "Operation", render: (payment) => payment.operation_type },
        { key: "method", title: "Method", render: (payment) => getStatusLabel(payment.payment_method) },
        { key: "status", title: "Status", render: (payment) => <StatusBadge label={payment.status} tone="payment" /> },
        {
          align: "right",
          key: "amount",
          title: "Amount",
          render: (payment) => formatPrice(payment.amount, payment.currency || currency),
        },
        {
          key: "external",
          title: "External ID",
          render: (payment) => payment.external_payment_id || payment.id,
        },
        {
          key: "failure",
          title: "Failure",
          render: (payment) => payment.failure_reason || payment.failure_code || "none",
        },
      ]}
      empty={<EmptyState description="No payment transactions were recorded." title="No payments" />}
      getRowKey={(payment) => payment.id}
      rows={payments}
    />
  );
}

function DeliveryTable({ shipments }: { shipments: DeliveryShipmentRead[] }) {
  return (
    <DataTable
      columns={[
        { key: "created", title: "Created", render: (shipment) => formatDate(shipment.created_at) },
        { key: "provider", title: "Provider", render: (shipment) => shipment.provider_name },
        { key: "method", title: "Method", render: (shipment) => getStatusLabel(shipment.delivery_method) },
        { key: "status", title: "Status", render: (shipment) => shipment.status },
        { key: "tracking", title: "Tracking", render: (shipment) => shipment.tracking_number || "not assigned" },
        { key: "shipped", title: "Shipped", render: (shipment) => formatDate(shipment.shipped_at) },
        { key: "delivered", title: "Delivered", render: (shipment) => formatDate(shipment.delivered_at) },
      ]}
      empty={<EmptyState description="No delivery shipments were recorded." title="No delivery history" />}
      getRowKey={(shipment) => shipment.id}
      rows={shipments}
    />
  );
}

function StatusHistoryTable({ history }: { history: OrderStatusHistoryRead[] }) {
  return (
    <DataTable
      columns={[
        { key: "created", title: "Created", render: (item) => formatDate(item.created_at) },
        { key: "from", title: "From", render: (item) => item.from_status || "start" },
        { key: "to", title: "To", render: (item) => item.to_status },
        { key: "actor", title: "Actor", render: (item) => item.actor_role || item.actor_user_id || "system" },
        { key: "reason", title: "Reason", render: (item) => item.reason || "none" },
      ]}
      empty={<EmptyState description="Lifecycle changes will appear here." title="No status history" />}
      getRowKey={(item) => item.id}
      rows={history}
    />
  );
}
