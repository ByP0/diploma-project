import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { checkoutApi } from "@features/checkout/api/checkoutApi";
import { useAuth } from "@features/auth/model/useAuth";
import { useCart } from "@features/cart/model/useCart";
import { isApiError } from "@shared/api";
import type {
  CheckoutPreviewRead,
  CartItemRead,
  DecimalString,
  DeliveryMethod,
  DeliveryQuoteRequest,
  DeliveryQuoteRead,
  OrderCheckoutCreate,
  OrderRead,
  PaymentMethod,
  PaymentTransactionRead,
} from "@shared/api";
import { AppRoutes } from "@shared/config/routes";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, SelectField, TextField, useToast } from "@shared/ui";
import "./CheckoutPage.css";

const DELIVERY_METHOD_OPTIONS: Array<{ label: string; value: DeliveryMethod }> = [
  { label: "Курьер", value: "courier" },
  { label: "Экспресс", value: "express" },
  { label: "Самовывоз", value: "pickup" },
];

const PAYMENT_METHOD_OPTIONS: Array<{ label: string; value: PaymentMethod }> = [
  { label: "Картой онлайн", value: "card_online" },
  { label: "Наличными при получении", value: "cash_on_delivery" },
  { label: "Картой при получении", value: "card_on_delivery" },
];

const PAYMENT_PROVIDER_OPTIONS = [
  { label: "Тестовый провайдер с переходом", value: "stub_redirect" },
  { label: "Тестовый провайдер авто", value: "stub" },
];

const PAYMENT_METHOD_LABELS = new Map(PAYMENT_METHOD_OPTIONS.map((option) => [option.value, option.label]));
const DELIVERY_METHOD_LABELS = new Map(DELIVERY_METHOD_OPTIONS.map((option) => [option.value, option.label]));

const ORDER_STATUS_LABELS: Record<string, string> = {
  awaiting_payment: "ожидает оплаты",
  cancelled: "отменен",
  created: "создан",
  delivered: "доставлен",
  failed: "ошибка",
  packed: "собран",
  paid: "оплачен",
  processing: "в обработке",
  refunded: "возврат",
  shipped: "в доставке",
};

const PAYMENT_STATUS_LABELS: Record<string, string> = {
  cancelled: "отменен",
  failed: "ошибка",
  partially_refunded: "частичный возврат",
  pending: "ожидает",
  refunded: "возврат",
  succeeded: "успешно",
};

type CheckoutForm = {
  currency: string;
  customerComment: string;
  customerName: string;
  customerPhone: string;
  deliveryAddressLine1: string;
  deliveryAddressLine2: string;
  deliveryApartment: string;
  deliveryCity: string;
  deliveryCountry: string;
  deliveryEntrance: string;
  deliveryFloor: string;
  deliveryInstructions: string;
  deliveryIntercom: string;
  deliveryMethod: DeliveryMethod;
  deliveryPostalCode: string;
  deliveryRegion: string;
  deliveryWindowEnd: string;
  deliveryWindowStart: string;
  paymentMethod: PaymentMethod;
  paymentProvider: string;
};

const initialForm: CheckoutForm = {
  currency: "RUB",
  customerComment: "",
  customerName: "",
  customerPhone: "",
  deliveryAddressLine1: "",
  deliveryAddressLine2: "",
  deliveryApartment: "",
  deliveryCity: "Калининград",
  deliveryCountry: "RU",
  deliveryEntrance: "",
  deliveryFloor: "",
  deliveryInstructions: "",
  deliveryIntercom: "",
  deliveryMethod: "courier",
  deliveryPostalCode: "",
  deliveryRegion: "Калининградская область",
  deliveryWindowEnd: "",
  deliveryWindowStart: "",
  paymentMethod: "card_online",
  paymentProvider: "stub_redirect",
};

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

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос оформления заказа.";
}

function optionalText(value: string) {
  const normalized = value.trim();
  return normalized || null;
}

function normalizeCode(value: string, fallback: string) {
  const normalized = value.trim().toUpperCase();
  return normalized || fallback;
}

function toIsoDateTime(value: string) {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function isDeliveryRequired(deliveryMethod: DeliveryMethod) {
  return deliveryMethod !== "pickup";
}

function buildCheckoutPayload(form: CheckoutForm): OrderCheckoutCreate {
  const requiresAddress = isDeliveryRequired(form.deliveryMethod);

  return {
    currency: normalizeCode(form.currency, "RUB"),
    customer_comment: optionalText(form.customerComment),
    customer_name: form.customerName.trim(),
    customer_phone: form.customerPhone.trim(),
    delivery_address_line1: requiresAddress ? optionalText(form.deliveryAddressLine1) : null,
    delivery_address_line2: requiresAddress ? optionalText(form.deliveryAddressLine2) : null,
    delivery_apartment: requiresAddress ? optionalText(form.deliveryApartment) : null,
    delivery_city: requiresAddress ? optionalText(form.deliveryCity) : null,
    delivery_country: normalizeCode(form.deliveryCountry, "RU"),
    delivery_entrance: requiresAddress ? optionalText(form.deliveryEntrance) : null,
    delivery_floor: requiresAddress ? optionalText(form.deliveryFloor) : null,
    delivery_instructions: requiresAddress ? optionalText(form.deliveryInstructions) : null,
    delivery_intercom: requiresAddress ? optionalText(form.deliveryIntercom) : null,
    delivery_method: form.deliveryMethod,
    delivery_postal_code: requiresAddress ? optionalText(form.deliveryPostalCode) : null,
    delivery_region: requiresAddress ? optionalText(form.deliveryRegion) : null,
    delivery_window_end: toIsoDateTime(form.deliveryWindowEnd),
    delivery_window_start: toIsoDateTime(form.deliveryWindowStart),
    payment_method: form.paymentMethod,
    payment_provider: form.paymentMethod === "card_online" ? optionalText(form.paymentProvider) : null,
  };
}

function validateCheckoutForm(form: CheckoutForm, totalItems: number) {
  if (totalItems < 1) {
    return "Корзина пуста.";
  }

  if (form.customerName.trim().length < 2) {
    return "Имя должно содержать минимум 2 символа.";
  }

  if (!/^[0-9+()\-\s]{7,32}$/.test(form.customerPhone.trim())) {
    return "Телефон должен содержать от 7 до 32 допустимых символов.";
  }

  if (normalizeCode(form.deliveryCountry, "RU").length !== 2) {
    return "Страна доставки должна быть двухбуквенным кодом.";
  }

  if (normalizeCode(form.currency, "RUB").length !== 3) {
    return "Валюта должна быть трехбуквенным кодом.";
  }

  if (isDeliveryRequired(form.deliveryMethod) && (!form.deliveryAddressLine1.trim() || !form.deliveryCity.trim())) {
    return "Для доставки нужно указать адрес и город.";
  }

  if (Boolean(form.deliveryWindowStart) !== Boolean(form.deliveryWindowEnd)) {
    return "Укажите оба значения: когда можно начать доставку и до какого времени ее нужно завершить.";
  }

  if (form.deliveryWindowStart && form.deliveryWindowEnd) {
    const start = new Date(form.deliveryWindowStart);
    const end = new Date(form.deliveryWindowEnd);

    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
      return "Время \"Доставить до\" должно быть позже времени \"Доставить с\".";
    }

    if (end.getTime() - start.getTime() > 24 * 60 * 60 * 1000) {
      return "Интервал доставки не должен превышать 24 часа.";
    }
  }

  return null;
}

function getLatestPayment(order: OrderRead): PaymentTransactionRead | null {
  return order.payment_transactions.at(-1) ?? null;
}

function getOrderStatusLabel(value: string) {
  return ORDER_STATUS_LABELS[value] ?? value.replace(/_/g, " ");
}

function getPaymentStatusLabel(value: string) {
  return PAYMENT_STATUS_LABELS[value] ?? value.replace(/_/g, " ");
}

function getPaymentMethodLabel(value: PaymentMethod) {
  return PAYMENT_METHOD_LABELS.get(value) ?? value.replace(/_/g, " ");
}

function getDeliveryMethodLabel(value: DeliveryMethod) {
  return DELIVERY_METHOD_LABELS.get(value) ?? value.replace(/_/g, " ");
}

function formatDays(value: number) {
  const suffix =
    value % 10 === 1 && value % 100 !== 11
      ? "день"
      : [2, 3, 4].includes(value % 10) && ![12, 13, 14].includes(value % 100)
        ? "дня"
        : "дней";
  return `${value} ${suffix}`;
}

export function CheckoutPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cart, isLoading: isCartLoading, isMerging, reloadCart, totalAmount, totalItems } = useCart();
  const { showToast } = useToast();
  const [createdOrder, setCreatedOrder] = useState<OrderRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<CheckoutForm>(initialForm);
  const [isPaymentChecking, setIsPaymentChecking] = useState(false);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isQuoteLoading, setIsQuoteLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [preview, setPreview] = useState<CheckoutPreviewRead | null>(null);
  const [quote, setQuote] = useState<DeliveryQuoteRead | null>(null);
  const [quoteError, setQuoteError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      return;
    }

    setForm((current) => ({
      ...current,
      customerName: current.customerName || user.name || "",
    }));
  }, [user]);

  const quoteRequest = useMemo<DeliveryQuoteRequest>(
    () => ({
      city: isDeliveryRequired(form.deliveryMethod) ? optionalText(form.deliveryCity) : null,
      country: normalizeCode(form.deliveryCountry, "RU"),
      delivery_method: form.deliveryMethod,
      order_amount: totalAmount,
      region: isDeliveryRequired(form.deliveryMethod) ? optionalText(form.deliveryRegion) : null,
    }),
    [form.deliveryCity, form.deliveryCountry, form.deliveryMethod, form.deliveryRegion, totalAmount],
  );

  useEffect(() => {
    if (totalItems < 1) {
      setQuote(null);
      setQuoteError(null);
      setIsQuoteLoading(false);
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      setIsQuoteLoading(true);
      checkoutApi
        .getDeliveryQuote(quoteRequest, { signal: controller.signal })
        .then((payload) => {
          if (!controller.signal.aborted) {
            setQuote(payload);
            setQuoteError(null);
          }
        })
        .catch((caughtError) => {
          if (!controller.signal.aborted) {
            setQuote(null);
            setQuoteError(getErrorMessage(caughtError));
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsQuoteLoading(false);
          }
        });
    }, 320);

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [quoteRequest, totalItems]);

  const handleTextChange =
    (field: keyof CheckoutForm) => (event: ChangeEvent<HTMLInputElement>) => {
      setForm((current) => ({
        ...current,
        [field]: event.target.value,
      }));
      setPreview(null);
      setError(null);
    };

  const handleDeliveryMethodChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setForm((current) => ({
      ...current,
      deliveryMethod: event.target.value as DeliveryMethod,
    }));
    setPreview(null);
    setError(null);
  };

  const handlePaymentMethodChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setForm((current) => ({
      ...current,
      paymentMethod: event.target.value as PaymentMethod,
    }));
    setPreview(null);
    setError(null);
  };

  const handlePaymentProviderChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setForm((current) => ({
      ...current,
      paymentProvider: event.target.value,
    }));
    setPreview(null);
    setError(null);
  };

  const updatePreview = async () => {
    const validationError = validateCheckoutForm(form, totalItems);
    if (validationError) {
      setError(validationError);
      return null;
    }

    setIsPreviewLoading(true);
    setError(null);

    try {
      const payload = await checkoutApi.previewCheckout(buildCheckoutPayload(form));
      setPreview(payload);
      return payload;
    } catch (caughtError) {
      setPreview(null);
      setError(getErrorMessage(caughtError));
      return null;
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validationError = validateCheckoutForm(form, totalItems);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const order = await checkoutApi.createOrderFromCart(buildCheckoutPayload(form));
      setCreatedOrder(order);
      setPreview(null);
      await reloadCart().catch(() => undefined);
      showToast({
        description: `Статус оплаты: ${getPaymentStatusLabel(order.payment_status)}`,
        title: "Заказ создан",
        variant: "success",
      });
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsSubmitting(false);
    }
  };

  const syncPayment = async () => {
    if (!createdOrder) {
      return;
    }

    setIsPaymentChecking(true);
    setError(null);

    try {
      const order = await checkoutApi.syncPayment(createdOrder.id);
      setCreatedOrder(order);
      showToast({
        description: `Статус оплаты: ${getPaymentStatusLabel(order.payment_status)}`,
        title: "Статус оплаты обновлен",
        variant: order.payment_status === "failed" ? "warning" : "success",
      });
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsPaymentChecking(false);
    }
  };

  const retryPayment = async () => {
    if (!createdOrder) {
      return;
    }

    setIsPaymentChecking(true);
    setError(null);

    try {
      const order = await checkoutApi.retryPayment(createdOrder.id);
      setCreatedOrder(order);
      showToast({
        description: `Статус оплаты: ${getPaymentStatusLabel(order.payment_status)}`,
        title: "Повторная оплата запущена",
        variant: "success",
      });
    } catch (caughtError) {
      setError(getErrorMessage(caughtError));
    } finally {
      setIsPaymentChecking(false);
    }
  };

  const isBusy = isSubmitting || isPreviewLoading;
  const requiresAddress = isDeliveryRequired(form.deliveryMethod);

  return (
    <div className="checkout-page page-stack">
      <PageHeader
        actions={
          <Button onClick={() => navigate(AppRoutes.cart)} variant="secondary">
            Вернуться в корзину
          </Button>
        }
        description="Проверьте данные доставки и оплаты перед созданием заказа из текущей корзины."
        eyebrow="Оформление"
        title="Оформление заказа"
      />

      {createdOrder ? (
        <OrderResult
          error={error}
          isPaymentChecking={isPaymentChecking}
          onRetryPayment={retryPayment}
          onSyncPayment={syncPayment}
          order={createdOrder}
        />
      ) : isCartLoading || isMerging ? (
        <LoadingState
          description={isMerging ? "Гостевая корзина переносится в ваш аккаунт." : "Загружаем корзину."}
          title={isMerging ? "Готовим оформление" : "Загружаем оформление"}
        />
      ) : totalItems < 1 ? (
        <EmptyState
          action={
            <Button onClick={() => navigate(AppRoutes.catalog)} variant="secondary">
              Открыть каталог
            </Button>
          }
          description="Добавьте товары в корзину перед оформлением заказа."
          title="Корзина пуста"
        />
      ) : (
        <div className="checkout-layout">
          <form className="checkout-form" onSubmit={handleSubmit}>
            {error ? (
              <ErrorState
                action={
                  <Button onClick={() => setError(null)} variant="secondary">
                    Закрыть
                  </Button>
                }
                description={error}
                title="Проверьте данные оформления"
              />
            ) : null}

            <section className="checkout-panel">
              <h2>Покупатель</h2>
              <div className="checkout-field-grid">
                <TextField
                  autoComplete="name"
                  label="Имя"
                  minLength={2}
                  onChange={handleTextChange("customerName")}
                  required
                  value={form.customerName}
                />
                <TextField
                  autoComplete="tel"
                  label="Телефон"
                  onChange={handleTextChange("customerPhone")}
                  pattern="^[0-9+()\-\s]+$"
                  required
                  value={form.customerPhone}
                />
              </div>
              <TextField
                label="Комментарий"
                maxLength={1000}
                onChange={handleTextChange("customerComment")}
                placeholder="Необязательно"
                value={form.customerComment}
              />
            </section>

            <section className="checkout-panel">
              <h2>Доставка</h2>
              <div className="checkout-field-grid">
                <SelectField
                  label="Способ"
                  onChange={handleDeliveryMethodChange}
                  options={DELIVERY_METHOD_OPTIONS}
                  value={form.deliveryMethod}
                />
                <TextField
                  label="Страна"
                  maxLength={2}
                  onChange={handleTextChange("deliveryCountry")}
                  required
                  value={form.deliveryCountry}
                />
              </div>

              {requiresAddress ? (
                <>
                  <div className="checkout-field-grid checkout-field-grid--wide">
                    <TextField
                      autoComplete="address-line1"
                      label="Адрес"
                      onChange={handleTextChange("deliveryAddressLine1")}
                      required
                      value={form.deliveryAddressLine1}
                    />
                    <TextField
                      autoComplete="address-line2"
                      label="Адрес, строка 2"
                      onChange={handleTextChange("deliveryAddressLine2")}
                      value={form.deliveryAddressLine2}
                    />
                    <TextField
                      autoComplete="address-level2"
                      label="Город"
                      onChange={handleTextChange("deliveryCity")}
                      required
                      value={form.deliveryCity}
                    />
                    <TextField
                      autoComplete="address-level1"
                      label="Регион"
                      onChange={handleTextChange("deliveryRegion")}
                      value={form.deliveryRegion}
                    />
                    <TextField
                      autoComplete="postal-code"
                      label="Индекс"
                      onChange={handleTextChange("deliveryPostalCode")}
                      value={form.deliveryPostalCode}
                    />
                    <TextField
                      label="Квартира"
                      onChange={handleTextChange("deliveryApartment")}
                      value={form.deliveryApartment}
                    />
                    <TextField label="Этаж" onChange={handleTextChange("deliveryFloor")} value={form.deliveryFloor} />
                    <TextField
                      label="Подъезд"
                      onChange={handleTextChange("deliveryEntrance")}
                      value={form.deliveryEntrance}
                    />
                    <TextField
                      label="Домофон"
                      onChange={handleTextChange("deliveryIntercom")}
                      value={form.deliveryIntercom}
                    />
                    <TextField
                      label="Инструкции"
                      maxLength={1000}
                      onChange={handleTextChange("deliveryInstructions")}
                      value={form.deliveryInstructions}
                    />
                  </div>
                </>
              ) : null}

              <div className="checkout-field-grid">
                <TextField
                  label="Доставить с"
                  onChange={handleTextChange("deliveryWindowStart")}
                  type="datetime-local"
                  value={form.deliveryWindowStart}
                />
                <TextField
                  label="Доставить до"
                  onChange={handleTextChange("deliveryWindowEnd")}
                  type="datetime-local"
                  value={form.deliveryWindowEnd}
                />
              </div>
            </section>

            <section className="checkout-panel">
              <h2>Оплата</h2>
              <div className="checkout-field-grid">
                <SelectField
                  label="Способ"
                  onChange={handlePaymentMethodChange}
                  options={PAYMENT_METHOD_OPTIONS}
                  value={form.paymentMethod}
                />
                {form.paymentMethod === "card_online" ? (
                  <SelectField
                    label="Провайдер"
                    onChange={handlePaymentProviderChange}
                    options={PAYMENT_PROVIDER_OPTIONS}
                    value={form.paymentProvider}
                  />
                ) : (
                  <TextField
                    disabled
                    label="Провайдер"
                    onChange={handleTextChange("paymentProvider")}
                    value="подтверждение при получении"
                  />
                )}
                <TextField label="Валюта" maxLength={3} onChange={handleTextChange("currency")} value={form.currency} />
              </div>
            </section>

            <div className="checkout-actions">
              <Button disabled={isBusy} isLoading={isPreviewLoading} onClick={() => void updatePreview()} variant="secondary">
                Обновить расчет
              </Button>
              <Button disabled={isBusy || totalItems < 1} isLoading={isSubmitting} type="submit">
                Создать заказ
              </Button>
            </div>
          </form>

          <aside className="checkout-side" aria-label="Итог оформления">
            <CartSummary amount={totalAmount} currency={form.currency} items={cart.items} totalItems={totalItems} />
            <QuoteSummary error={quoteError} isLoading={isQuoteLoading} quote={quote} />
            <PreviewSummary isLoading={isPreviewLoading} preview={preview} />
          </aside>
        </div>
      )}
    </div>
  );
}

type CartSummaryProps = {
  amount: number;
  currency: string;
  items: CartItemRead[];
  totalItems: number;
};

function CartSummary({ amount, currency, items, totalItems }: CartSummaryProps) {
  return (
    <section className="checkout-panel checkout-panel--summary">
      <h2>Корзина</h2>
      <div className="checkout-lines">
        {items.map((item) => (
          <div className="checkout-line" key={item.id}>
            <span>{item.product.name}</span>
            <strong>x{item.quantity}</strong>
          </div>
        ))}
      </div>
      <div className="checkout-total-row">
        <span>Товары</span>
        <strong>{totalItems}</strong>
      </div>
      <div className="checkout-total-row">
        <span>Сумма товаров</span>
        <strong>{formatPrice(amount, normalizeCode(currency, "RUB"))}</strong>
      </div>
    </section>
  );
}

type QuoteSummaryProps = {
  error: string | null;
  isLoading: boolean;
  quote: DeliveryQuoteRead | null;
};

function QuoteSummary({ error, isLoading, quote }: QuoteSummaryProps) {
  return (
    <section className="checkout-panel checkout-panel--summary">
      <h2>Расчет доставки</h2>
      {isLoading ? (
        <p className="checkout-muted">Считаем...</p>
      ) : error ? (
        <p className="checkout-error">{error}</p>
      ) : quote ? (
        <>
          <div className="checkout-total-row">
            <span>Служба</span>
            <strong>{quote.provider_name}</strong>
          </div>
          <div className="checkout-total-row">
            <span>Стоимость</span>
            <strong>{formatPrice(quote.cost, quote.currency)}</strong>
          </div>
          <div className="checkout-total-row">
            <span>Срок</span>
            <strong>{formatDays(quote.estimated_days)}</strong>
          </div>
        </>
      ) : (
        <p className="checkout-muted">Расчет еще не выполнен.</p>
      )}
    </section>
  );
}

type PreviewSummaryProps = {
  isLoading: boolean;
  preview: CheckoutPreviewRead | null;
};

function PreviewSummary({ isLoading, preview }: PreviewSummaryProps) {
  return (
    <section className="checkout-panel checkout-panel--summary">
      <h2>Предварительный итог</h2>
      {isLoading ? (
        <p className="checkout-muted">Обновляем...</p>
      ) : preview ? (
        <>
          <div className="checkout-lines">
            {preview.items.map((item) => (
              <div className="checkout-line" key={item.product_id}>
                <span>{item.product_name}</span>
                <strong>{formatPrice(item.line_total, preview.currency)}</strong>
              </div>
            ))}
          </div>
          <div className="checkout-total-row">
            <span>Товары</span>
            <strong>{formatPrice(preview.items_total_amount, preview.currency)}</strong>
          </div>
          <div className="checkout-total-row">
            <span>Доставка</span>
            <strong>{formatPrice(preview.delivery_cost, preview.currency)}</strong>
          </div>
          <div className="checkout-total-row checkout-total-row--grand">
            <span>Итого</span>
            <strong>{formatPrice(preview.total_amount, preview.currency)}</strong>
          </div>
        </>
      ) : (
        <p className="checkout-muted">Предварительный итог еще не рассчитан.</p>
      )}
    </section>
  );
}

type OrderResultProps = {
  error: string | null;
  isPaymentChecking: boolean;
  onRetryPayment: () => Promise<void>;
  onSyncPayment: () => Promise<void>;
  order: OrderRead;
};

function OrderResult({ error, isPaymentChecking, onRetryPayment, onSyncPayment, order }: OrderResultProps) {
  const latestPayment = getLatestPayment(order);
  const redirectUrl = latestPayment?.redirect_url || null;
  const canRetry = order.payment_method === "card_online" && order.payment_status !== "succeeded";

  return (
    <section className="checkout-result">
      <div className="checkout-result__header">
        <div>
          <p className="checkout-result__eyebrow">Заказ {order.id}</p>
          <h2>{formatPrice(order.total_amount, order.currency)}</h2>
        </div>
        <div className="checkout-status-stack">
          <span className="checkout-status">{getOrderStatusLabel(order.status)}</span>
          <span className="checkout-status checkout-status--payment">{getPaymentStatusLabel(order.payment_status)}</span>
        </div>
      </div>

      {error ? <p className="checkout-error">{error}</p> : null}

      <div className="checkout-result-grid">
        <article>
          <span>Способ оплаты</span>
          <strong>{getPaymentMethodLabel(order.payment_method)}</strong>
        </article>
        <article>
          <span>Способ доставки</span>
          <strong>{getDeliveryMethodLabel(order.delivery_method)}</strong>
        </article>
        <article>
          <span>Товары</span>
          <strong>{order.items.length}</strong>
        </article>
        <article>
          <span>Стоимость доставки</span>
          <strong>{formatPrice(order.delivery_cost, order.currency)}</strong>
        </article>
      </div>

      {latestPayment ? (
        <div className="checkout-payment-box">
          <div>
            <span>Провайдер</span>
            <strong>{latestPayment.provider_name}</strong>
          </div>
          <div>
            <span>Транзакция</span>
            <strong>{latestPayment.external_payment_id || latestPayment.id}</strong>
          </div>
          {latestPayment.failure_reason ? <p className="checkout-error">{latestPayment.failure_reason}</p> : null}
        </div>
      ) : null}

      <div className="checkout-actions">
        {redirectUrl ? (
          <a className="checkout-link-button" href={redirectUrl} rel="noreferrer" target="_blank">
            Перейти к оплате
          </a>
        ) : null}
        <Button isLoading={isPaymentChecking} onClick={() => void onSyncPayment()} variant="secondary">
          Проверить оплату
        </Button>
        {canRetry ? (
          <Button disabled={isPaymentChecking} onClick={() => void onRetryPayment()} variant="ghost">
            Повторить оплату
          </Button>
        ) : null}
      </div>
    </section>
  );
}
