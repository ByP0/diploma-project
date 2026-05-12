import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ordersApi, type OrderDocumentType } from "@features/orders/api/ordersApi";
import { useCart } from "@features/cart/model/useCart";
import { isApiError } from "@shared/api";
import type {
  DecimalString,
  DeliveryShipmentRead,
  OrderDocumentRead,
  OrderItemRead,
  OrderRead,
  OrderStatusHistoryRead,
  PaymentStatus,
  PaymentTransactionRead,
  UUID,
} from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, TextField, useToast } from "@shared/ui";
import "./OrdersPage.css";

const PAGE_SIZE = 10;

type OrderAction =
  | "cancel"
  | "document-invoice"
  | "document-receipt"
  | "recheck-payment"
  | "refund"
  | "repeat"
  | "retry-payment"
  | "sync-payment";

type RefundQuantities = Record<string, string>;

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

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Order request failed.";
}

function getLatestPayment(order: OrderRead) {
  return order.payment_transactions.at(-1) ?? null;
}

function canRetryPayment(order: OrderRead) {
  return order.payment_method === "card_online" && order.payment_status !== "succeeded";
}

function canCancelOrder(order: OrderRead) {
  return !["cancelled", "delivered", "failed", "refunded"].includes(order.status);
}

function canRefundOrder(order: OrderRead) {
  return ["succeeded", "partially_refunded"].includes(order.payment_status) && order.items.some(getRefundableQuantity);
}

function getRefundableQuantity(item: OrderItemRead) {
  return Math.max(0, item.quantity - item.returned_quantity);
}

function buildInitialRefundQuantities(order: OrderRead | null): RefundQuantities {
  if (!order) {
    return {};
  }

  return Object.fromEntries(order.items.map((item) => [item.id, "0"]));
}

function getStatusLabel(status: string) {
  return status.replace(/_/g, " ");
}

export function OrdersPage() {
  const navigate = useNavigate();
  const { reloadCart } = useCart();
  const { showToast } = useToast();
  const [action, setAction] = useState<OrderAction | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [document, setDocument] = useState<OrderDocumentRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isListLoading, setIsListLoading] = useState(true);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [page, setPage] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [refundQuantities, setRefundQuantities] = useState<RefundQuantities>({});
  const [refundReason, setRefundReason] = useState("");
  const [selectedOrderId, setSelectedOrderId] = useState<UUID | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    setIsListLoading(true);
    setError(null);
    ordersApi
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
          setError(getErrorMessage(caughtError));
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
    setError(null);

    ordersApi
      .getById(selectedOrderId, { signal: controller.signal })
      .then((payload) => {
        if (!controller.signal.aborted) {
          replaceOrder(payload);
          setRefundQuantities(buildInitialRefundQuantities(payload));
          setDocument(null);
        }
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [selectedOrderId]);

  const selectedOrder = useMemo(
    () => orders.find((order) => order.id === selectedOrderId) ?? null,
    [orders, selectedOrderId],
  );

  const summary = useMemo(
    () => ({
      active: orders.filter((order) => !["cancelled", "delivered", "failed", "refunded"].includes(order.status)).length,
      awaitingPayment: orders.filter((order) => order.payment_status === "pending").length,
      total: orders.length,
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

  async function runOrderAction(actionName: OrderAction, callback: () => Promise<OrderRead>) {
    setAction(actionName);
    setError(null);

    try {
      const order = await callback();
      replaceOrder(order);
      setRefundQuantities(buildInitialRefundQuantities(order));
      showToast({
        description: `Status: ${order.status}, payment: ${order.payment_status}`,
        title: "Order updated",
        variant: "success",
      });
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  }

  const handleSelectOrder = (orderId: UUID) => {
    setSelectedOrderId(orderId);
    setError(null);
    setDocument(null);
    setCancelReason("");
    setRefundReason("");
  };

  const handleCancel = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrder) {
      return;
    }

    await runOrderAction("cancel", () =>
      ordersApi.cancel(selectedOrder.id, {
        reason: cancelReason.trim() || null,
      }),
    );
  };

  const handleDocument = async (documentType: OrderDocumentType) => {
    if (!selectedOrder) {
      return;
    }

    const actionName: OrderAction = documentType === "invoice" ? "document-invoice" : "document-receipt";
    setAction(actionName);
    setError(null);

    try {
      const payload = await ordersApi.getDocument(selectedOrder.id, documentType);
      setDocument(payload);
      showToast({
        description: payload.document_number,
        title: `${documentType} loaded`,
        variant: "success",
      });
    } catch (caughtError) {
      setDocument(null);
      setError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const handlePaymentAction = async (actionName: Extract<OrderAction, "recheck-payment" | "retry-payment" | "sync-payment">) => {
    if (!selectedOrder) {
      return;
    }

    const callbacks = {
      "recheck-payment": () => ordersApi.recheckPayment(selectedOrder.id),
      "retry-payment": () => ordersApi.retryPayment(selectedOrder.id),
      "sync-payment": () => ordersApi.syncPayment(selectedOrder.id),
    };

    await runOrderAction(actionName, callbacks[actionName]);
  };

  const handleRepeat = async () => {
    if (!selectedOrder) {
      return;
    }

    setAction("repeat");
    setError(null);

    try {
      await ordersApi.repeat(selectedOrder.id);
      await reloadCart().catch(() => undefined);
      showToast({
        description: "Items were added back to your cart.",
        title: "Order repeated",
        variant: "success",
      });
      navigate(AppRoutes.cart);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setAction(null);
    }
  };

  const handleRefundQuantityChange = (itemId: UUID) => (event: ChangeEvent<HTMLInputElement>) => {
    setRefundQuantities((current) => ({
      ...current,
      [itemId]: event.target.value,
    }));
  };

  const handleRefund = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedOrder) {
      return;
    }

    const items = selectedOrder.items
      .map((item) => ({
        order_item_id: item.id,
        quantity: Math.min(
          getRefundableQuantity(item),
          Math.max(0, Math.trunc(Number(refundQuantities[item.id]) || 0)),
        ),
      }))
      .filter((item) => item.quantity > 0);

    if (!items.length) {
      setError("Select at least one item quantity to refund.");
      return;
    }

    await runOrderAction("refund", () =>
      ordersApi.refund(selectedOrder.id, {
        idempotency_key: `refund:${selectedOrder.id}:${Date.now()}`,
        items,
        reason: refundReason.trim() || null,
      }),
    );
  };

  const canGoNext = orders.length === PAGE_SIZE;
  const canGoPrevious = page > 0;

  return (
    <div className="orders-page page-stack">
      <PageHeader
        actions={
          <Button
            onClick={() => {
              setPage(0);
              setReloadKey((current) => current + 1);
            }}
            variant="secondary"
          >
            Refresh
          </Button>
        }
        description="Track your orders, payments, delivery shipments, documents, cancellations, repeats, and refunds."
        eyebrow="Orders"
        title="My orders"
      />

      <section className="orders-summary" aria-label="Orders summary">
        <article className="surface-card">
          <span>Loaded</span>
          <strong>{summary.total}</strong>
        </article>
        <article className="surface-card">
          <span>Active</span>
          <strong>{summary.active}</strong>
        </article>
        <article className="surface-card">
          <span>Awaiting payment</span>
          <strong>{summary.awaitingPayment}</strong>
        </article>
      </section>

      {error ? (
        <ErrorState
          action={
            <Button onClick={() => setError(null)} variant="secondary">
              Dismiss
            </Button>
          }
          description={error}
          title="Order action failed"
        />
      ) : null}

      <div className="orders-layout">
        <aside className="orders-list" aria-label="Order list">
          {isListLoading ? (
            <LoadingState description="Loading your order history." title="Loading orders" />
          ) : orders.length ? (
            <>
              <div className="orders-list__items">
                {orders.map((order) => (
                  <button
                    className={order.id === selectedOrderId ? "order-card is-active" : "order-card"}
                    key={order.id}
                    onClick={() => handleSelectOrder(order.id)}
                    type="button"
                  >
                    <span>{formatDate(order.created_at)}</span>
                    <strong>{formatPrice(order.total_amount, order.currency)}</strong>
                    <small>
                      {getStatusLabel(order.status)} / {getStatusLabel(order.payment_status)}
                    </small>
                  </button>
                ))}
              </div>
              <div className="orders-pagination">
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
            <EmptyState
              action={
                <Button onClick={() => navigate(AppRoutes.catalog)} variant="secondary">
                  Open catalog
                </Button>
              }
              description="Create an order from the cart and it will appear here."
              title="No orders yet"
            />
          )}
        </aside>

        <section className="orders-detail" aria-label="Order details">
          {isDetailLoading ? (
            <LoadingState description="Loading order details." title="Loading order" />
          ) : selectedOrder ? (
            <OrderDetail
              action={action}
              cancelReason={cancelReason}
              document={document}
              onCancel={handleCancel}
              onCancelReasonChange={(event) => setCancelReason(event.target.value)}
              onDocument={handleDocument}
              onPaymentAction={handlePaymentAction}
              onRefund={handleRefund}
              onRefundQuantityChange={handleRefundQuantityChange}
              onRefundReasonChange={(event) => setRefundReason(event.target.value)}
              onRepeat={handleRepeat}
              order={selectedOrder}
              refundQuantities={refundQuantities}
              refundReason={refundReason}
            />
          ) : (
            <EmptyState description="Select an order from the list." title="No order selected" />
          )}
        </section>
      </div>
    </div>
  );
}

type OrderDetailProps = {
  action: OrderAction | null;
  cancelReason: string;
  document: OrderDocumentRead | null;
  onCancel: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onCancelReasonChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onDocument: (documentType: OrderDocumentType) => Promise<void>;
  onPaymentAction: (actionName: Extract<OrderAction, "recheck-payment" | "retry-payment" | "sync-payment">) => Promise<void>;
  onRefund: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  onRefundQuantityChange: (itemId: UUID) => (event: ChangeEvent<HTMLInputElement>) => void;
  onRefundReasonChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onRepeat: () => Promise<void>;
  order: OrderRead;
  refundQuantities: RefundQuantities;
  refundReason: string;
};

function OrderDetail({
  action,
  cancelReason,
  document,
  onCancel,
  onCancelReasonChange,
  onDocument,
  onPaymentAction,
  onRefund,
  onRefundQuantityChange,
  onRefundReasonChange,
  onRepeat,
  order,
  refundQuantities,
  refundReason,
}: OrderDetailProps) {
  const latestPayment = getLatestPayment(order);
  const isBusy = Boolean(action);

  return (
    <div className="orders-detail-stack">
      <section className="order-hero">
        <div>
          <p>Order {order.id}</p>
          <h2>{formatPrice(order.total_amount, order.currency)}</h2>
          <span>{formatDate(order.created_at)}</span>
        </div>
        <div className="order-status-group">
          <StatusBadge label={order.status} />
          <StatusBadge label={order.payment_status} tone="payment" />
        </div>
      </section>

      <section className="order-action-bar" aria-label="Order actions">
        {latestPayment?.redirect_url ? (
          <a className="order-link-button" href={latestPayment.redirect_url} rel="noreferrer" target="_blank">
            Open payment
          </a>
        ) : null}
        <Button disabled={isBusy} isLoading={action === "sync-payment"} onClick={() => void onPaymentAction("sync-payment")} size="sm" variant="secondary">
          Sync payment
        </Button>
        <Button disabled={isBusy} isLoading={action === "recheck-payment"} onClick={() => void onPaymentAction("recheck-payment")} size="sm" variant="secondary">
          Recheck payment
        </Button>
        {canRetryPayment(order) ? (
          <Button disabled={isBusy} isLoading={action === "retry-payment"} onClick={() => void onPaymentAction("retry-payment")} size="sm">
            Retry payment
          </Button>
        ) : null}
        <Button disabled={isBusy} isLoading={action === "repeat"} onClick={() => void onRepeat()} size="sm" variant="ghost">
          Repeat order
        </Button>
      </section>

      <section className="order-panel">
        <h3>Items</h3>
        <DataTable
          columns={[
            { key: "name", title: "Product", render: (item) => item.product_name },
            { key: "quantity", title: "Qty", align: "right", render: (item) => item.quantity },
            {
              key: "returned",
              title: "Returned",
              align: "right",
              render: (item) => item.returned_quantity,
            },
            {
              key: "unit",
              title: "Unit price",
              align: "right",
              render: (item) => formatPrice(item.unit_price, order.currency),
            },
            {
              key: "total",
              title: "Line total",
              align: "right",
              render: (item) => formatPrice(item.line_total, order.currency),
            },
          ]}
          getRowKey={(item) => item.id}
          rows={order.items}
        />
      </section>

      <section className="order-panel">
        <h3>Delivery</h3>
        <div className="order-info-grid">
          <InfoItem label="Method" value={order.delivery_method} />
          <InfoItem label="Cost" value={formatPrice(order.delivery_cost, order.currency)} />
          <InfoItem label="Window start" value={formatDate(order.delivery_window_start)} />
          <InfoItem label="Window end" value={formatDate(order.delivery_window_end)} />
          <InfoItem label="Address" value={formatAddress(order)} wide />
        </div>
        <DeliveryTable shipments={order.delivery_shipments} />
      </section>

      <section className="order-panel">
        <h3>Payments</h3>
        <PaymentTable payments={order.payment_transactions} />
      </section>

      <section className="order-panel">
        <h3>Status history</h3>
        <StatusHistoryTable history={order.status_history} />
      </section>

      <section className="order-panel">
        <h3>Documents</h3>
        <div className="order-action-bar">
          <Button disabled={isBusy} isLoading={action === "document-invoice"} onClick={() => void onDocument("invoice")} size="sm" variant="secondary">
            Invoice
          </Button>
          <Button disabled={isBusy} isLoading={action === "document-receipt"} onClick={() => void onDocument("receipt")} size="sm" variant="secondary">
            Receipt
          </Button>
        </div>
        {document ? <DocumentPreview document={document} /> : <p className="orders-muted">Choose a document to load it from the API.</p>}
      </section>

      <section className="order-forms">
        <form className="order-panel" onSubmit={onCancel}>
          <h3>Cancel order</h3>
          <TextField
            disabled={!canCancelOrder(order) || isBusy}
            label="Reason"
            maxLength={1000}
            onChange={onCancelReasonChange}
            placeholder="Optional"
            value={cancelReason}
          />
          <Button disabled={!canCancelOrder(order) || isBusy} isLoading={action === "cancel"} type="submit" variant="danger">
            Cancel order
          </Button>
        </form>

        <form className="order-panel" onSubmit={onRefund}>
          <h3>Refund form</h3>
          <div className="refund-grid">
            {order.items.map((item) => (
              <TextField
                disabled={!canRefundOrder(order) || getRefundableQuantity(item) < 1 || isBusy}
                key={item.id}
                label={`${item.product_name} (max ${getRefundableQuantity(item)})`}
                max={getRefundableQuantity(item)}
                min="0"
                onChange={onRefundQuantityChange(item.id)}
                type="number"
                value={refundQuantities[item.id] ?? "0"}
              />
            ))}
          </div>
          <TextField
            disabled={!canRefundOrder(order) || isBusy}
            label="Reason"
            maxLength={1000}
            onChange={onRefundReasonChange}
            placeholder="Optional"
            value={refundReason}
          />
          <Button disabled={!canRefundOrder(order) || isBusy} isLoading={action === "refund"} type="submit" variant="secondary">
            Submit refund
          </Button>
        </form>
      </section>
    </div>
  );
}

type StatusBadgeProps = {
  label: PaymentStatus | string;
  tone?: "default" | "payment";
};

function StatusBadge({ label, tone = "default" }: StatusBadgeProps) {
  return <span className={tone === "payment" ? "order-badge order-badge--payment" : "order-badge"}>{getStatusLabel(label)}</span>;
}

type InfoItemProps = {
  label: string;
  value: string;
  wide?: boolean;
};

function InfoItem({ label, value, wide = false }: InfoItemProps) {
  return (
    <article className={wide ? "order-info-item is-wide" : "order-info-item"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
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

function PaymentTable({ payments }: { payments: PaymentTransactionRead[] }) {
  return (
    <DataTable
      columns={[
        { key: "created", title: "Created", render: (payment) => formatDate(payment.created_at) },
        { key: "provider", title: "Provider", render: (payment) => payment.provider_name },
        { key: "operation", title: "Operation", render: (payment) => payment.operation_type },
        { key: "status", title: "Status", render: (payment) => <StatusBadge label={payment.status} tone="payment" /> },
        {
          key: "amount",
          title: "Amount",
          align: "right",
          render: (payment) => formatPrice(payment.amount, payment.currency),
        },
        {
          key: "external",
          title: "External ID",
          render: (payment) => payment.external_payment_id || payment.id,
        },
      ]}
      empty={<EmptyState description="No payment transactions were created yet." title="No payments" />}
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
        { key: "status", title: "Status", render: (shipment) => shipment.status },
        { key: "tracking", title: "Tracking", render: (shipment) => shipment.tracking_number || "not assigned" },
        {
          key: "cost",
          title: "Quoted",
          align: "right",
          render: (shipment) => formatPrice(shipment.quoted_cost),
        },
      ]}
      empty={<EmptyState description="Shipment will appear after payment and processing." title="No deliveries" />}
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
      empty={<EmptyState description="Status changes will be listed here." title="No history" />}
      getRowKey={(item) => item.id}
      rows={history}
    />
  );
}

function DocumentPreview({ document }: { document: OrderDocumentRead }) {
  return (
    <div className="document-preview">
      <div>
        <span>{document.document_type}</span>
        <strong>{document.document_number}</strong>
      </div>
      <div>
        <span>Issued</span>
        <strong>{formatDate(document.issued_at)}</strong>
      </div>
      <div>
        <span>Amount</span>
        <strong>{formatPrice(document.amount, document.currency)}</strong>
      </div>
      <div className="is-wide">
        <span>Lines</span>
        <strong>{document.items.map((item) => `${item.product_name} x${item.quantity}`).join(", ")}</strong>
      </div>
    </div>
  );
}
