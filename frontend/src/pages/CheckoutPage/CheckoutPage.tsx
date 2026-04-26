import * as React from "react";

import { ChevronRightIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { useAuth } from "../../features/auth";
import {
  buildCheckoutPayload,
  buildDeliveryWindows,
  checkoutApi,
  deliveryOptions,
  getFirstInvalidStep,
  hasCheckoutErrors,
  initialCheckoutForm,
  paymentOptions,
  paymentProviderOptions,
  validateCheckoutForm,
  validateCheckoutStep,
  type CheckoutField,
  type CheckoutFieldErrors,
  type CheckoutFormState,
  type CheckoutPreviewRead,
  type CheckoutStepId,
  type DeliveryMethod,
  type PaymentMethod,
  type PaymentProviderId,
} from "../../features/checkout";
import { CheckoutOrderSummary, CheckoutStepper, PriceLockIndicator } from "../../features/checkout";
import { CartLineItem, formatCartPrice, transformBackendCart, useCart } from "../../features/cart";
import { cn } from "../../shared/lib/cn";
import { Badge } from "../../shared/ui/Badge";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Field, FieldError, FieldHint, FieldLabel, Input, Textarea } from "../../shared/ui/Input";
import { Skeleton, SkeletonText } from "../../shared/ui/Skeleton";
import { useToast } from "../../shared/ui/Toast";

export interface CheckoutPageProps {
  LinkComponent?: StorefrontLinkComponent;
  cartHref?: string;
  loginHref?: string;
  successHref?: string;
  failHref?: string;
  onOrderCreated?: (orderId: string) => void;
  className?: string;
}

const stepOrder: CheckoutStepId[] = ["items", "address", "delivery", "payment", "summary"];

export function CheckoutPage({
  LinkComponent,
  cartHref = "/cart",
  loginHref = "/login",
  successHref = "/checkout/success",
  failHref = "/checkout/fail",
  onOrderCreated,
  className,
}: CheckoutPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const auth = useAuth();
  const { toast } = useToast();
  const { cart, loading: cartLoading, syncing: cartSyncing, reload, updateItem, removeItem } = useCart();
  const deliveryWindows = React.useMemo(() => buildDeliveryWindows(), []);
  const [activeStep, setActiveStep] = React.useState<CheckoutStepId>("items");
  const [form, setForm] = React.useState<CheckoutFormState>(initialCheckoutForm);
  const [errors, setErrors] = React.useState<CheckoutFieldErrors>({});
  const [preview, setPreview] = React.useState<CheckoutPreviewRead | null>(null);
  const [previewLoading, setPreviewLoading] = React.useState(false);
  const [stockChecking, setStockChecking] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!auth.user) {
      return;
    }

    setForm((currentForm) => ({
      ...currentForm,
      customerName: currentForm.customerName || auth.user?.name || "",
    }));
  }, [auth.user]);

  const completedSteps = React.useMemo(() => {
    const activeIndex = stepOrder.indexOf(activeStep);
    return stepOrder.slice(0, activeIndex);
  }, [activeStep]);

  const updateField = React.useCallback(
    <FieldName extends CheckoutField>(field: FieldName, value: CheckoutFormState[FieldName]) => {
      setForm((currentForm) => ({ ...currentForm, [field]: value }));
      setPreview(null);
      setSubmitError(null);
      setErrors((currentErrors) => {
        if (!currentErrors[field]) {
          return currentErrors;
        }
        const nextErrors = { ...currentErrors };
        delete nextErrors[field];
        return nextErrors;
      });
    },
    [],
  );

  const goToStep = React.useCallback((step: CheckoutStepId) => {
    setActiveStep(step);
    setSubmitError(null);
  }, []);

  const validateCurrentStep = React.useCallback(() => {
    const nextErrors: CheckoutFieldErrors = validateCheckoutStep(activeStep, form, deliveryWindows);

    if (activeStep === "items") {
      if (!cart.items.length) {
        nextErrors.cart = "Корзина пуста.";
      } else if (cart.totals.unavailableItems > 0) {
        nextErrors.cart = "В корзине есть товары с недоступным остатком.";
      } else if (!auth.isAuthenticated) {
        nextErrors.cart = "Для оформления заказа нужно войти в аккаунт.";
      }
    }

    setErrors(nextErrors);
    return nextErrors;
  }, [activeStep, auth.isAuthenticated, cart.items.length, cart.totals.unavailableItems, deliveryWindows, form]);

  const refreshPreview = React.useCallback(async () => {
    const payload = buildCheckoutPayload(form, deliveryWindows);
    setPreviewLoading(true);
    try {
      const nextPreview = await checkoutApi.preview(payload);
      setPreview(nextPreview);
      return nextPreview;
    } finally {
      setPreviewLoading(false);
    }
  }, [deliveryWindows, form]);

  const goNext = React.useCallback(async () => {
    const nextErrors = validateCurrentStep();
    if (hasCheckoutErrors(nextErrors)) {
      return;
    }

    const currentIndex = stepOrder.indexOf(activeStep);
    const nextStep = stepOrder[Math.min(currentIndex + 1, stepOrder.length - 1)];

    if (nextStep === "summary") {
      const finalErrors = validateCheckoutForm(form, deliveryWindows);
      if (hasCheckoutErrors(finalErrors)) {
        setErrors(finalErrors);
        setActiveStep(getFirstInvalidStep(finalErrors));
        return;
      }

      try {
        await refreshPreview();
      } catch (error) {
        const message = error instanceof Error ? error.message : "Не удалось рассчитать заказ.";
        setSubmitError(message);
        toast({ title: "Расчёт заказа не выполнен", description: message, variant: "danger" });
        return;
      }
    }

    setActiveStep(nextStep);
  }, [activeStep, deliveryWindows, form, refreshPreview, toast, validateCurrentStep]);

  const goBack = React.useCallback(() => {
    const currentIndex = stepOrder.indexOf(activeStep);
    setActiveStep(stepOrder[Math.max(currentIndex - 1, 0)]);
    setSubmitError(null);
  }, [activeStep]);

  const submitOrder = React.useCallback(async () => {
    const finalErrors = validateCheckoutForm(form, deliveryWindows);
    if (!cart.items.length) {
      finalErrors.cart = "Корзина пуста.";
    }
    if (!auth.isAuthenticated) {
      finalErrors.cart = "Для оформления заказа нужно войти в аккаунт.";
    }

    if (hasCheckoutErrors(finalErrors)) {
      setErrors(finalErrors);
      setActiveStep(getFirstInvalidStep(finalErrors));
      return;
    }

    const payload = buildCheckoutPayload(form, deliveryWindows);
    setStockChecking(true);
    setSubmitting(true);
    setSubmitError(null);

    try {
      const backendCart = await checkoutApi.revalidateCart();
      const checkedCart = transformBackendCart(backendCart);
      if (!checkedCart.items.length || checkedCart.totals.unavailableItems > 0) {
        await reload();
        setErrors({ cart: "Остатки изменились. Проверьте корзину перед оформлением." });
        setActiveStep("items");
        toast({
          title: "Нужна проверка корзины",
          description: "Некоторые товары закончились или доступны в меньшем количестве.",
          variant: "warning",
        });
        return;
      }

      setStockChecking(false);
      const lockedPreview = await checkoutApi.preview(payload);
      setPreview(lockedPreview);
      const order = await checkoutApi.createOrder(payload);
      await reload();
      const failedPayment = order.payment_transactions.find((transaction) => transaction.status === "failed");
      if (order.status === "failed" || order.payment_status === "failed") {
        const reason = failedPayment?.failure_reason ?? "Оплата не прошла. Попробуйте другой способ.";
        toast({ title: "Оплата не прошла", description: reason, variant: "danger" });
        if (typeof window !== "undefined") {
          window.location.assign(`${failHref}?reason=${encodeURIComponent(reason)}`);
        }
        return;
      }

      toast({
        title: "Заказ создан",
        description: `Номер заказа: ${order.id}`,
        variant: "success",
      });

      if (onOrderCreated) {
        onOrderCreated(order.id);
        return;
      }

      if (typeof window !== "undefined") {
        window.location.assign(`${successHref}?orderId=${encodeURIComponent(order.id)}`);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Заказ не создан. Попробуйте ещё раз.";
      setSubmitError(message);
      toast({ title: "Заказ не создан", description: message, variant: "danger" });
    } finally {
      setStockChecking(false);
      setSubmitting(false);
    }
  }, [auth.isAuthenticated, cart.items.length, deliveryWindows, failHref, form, onOrderCreated, reload, successHref, toast]);

  const actionDisabled =
    cartLoading ||
    cartSyncing ||
    previewLoading ||
    stockChecking ||
    submitting ||
    (activeStep === "items" && (!cart.items.length || cart.totals.unavailableItems > 0 || !auth.isAuthenticated));

  return (
    <div className={cn("grid gap-6 pb-6", className)}>
      <header className="grid gap-4 rounded-lg border border-primary-border bg-primary-soft p-5 shadow-sm lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="primary">Checkout</Badge>
            <Badge variant={auth.isAuthenticated ? "success" : "warning"} dot>
              {auth.isAuthenticated ? "Профиль подтверждён" : "Требуется вход"}
            </Badge>
          </div>
          <h1 className="mt-3 text-h1 text-foreground">Оформление заказа</h1>
          <p className="mt-2 max-w-3xl text-body text-muted-foreground">
            Проверьте свежие продукты, выберите удобную доставку и зафиксируйте итоговую стоимость.
          </p>
        </div>
        <PriceLockIndicator loading={previewLoading || stockChecking} lockedAt={preview?.calculated_at ?? null} />
      </header>

      <CheckoutStepper activeStep={activeStep} completedSteps={completedSteps} onStepSelect={goToStep} />

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] xl:items-start">
        <div className="grid gap-4">
          {submitError ? (
            <Card className="border-danger-border bg-danger-soft p-4" variant="surface">
              <h2 className="text-h4 text-danger">Не удалось продолжить checkout</h2>
              <p className="mt-1 text-body-sm text-muted-foreground">{submitError}</p>
              <Link
                className="focus-ring mt-3 inline-flex min-h-[var(--control-height-md)] items-center justify-center rounded-md border border-danger-border bg-surface px-4 text-button font-bold text-danger transition hover:bg-danger-soft"
                href={`${failHref}?reason=${encodeURIComponent(submitError)}`}
              >
                Открыть страницу ошибки
              </Link>
            </Card>
          ) : null}

          {activeStep === "items" ? (
            <ItemsStep
              Link={Link}
              authReady={auth.status !== "checking"}
              cartHref={cartHref}
              cartLoading={cartLoading}
              cartSyncing={cartSyncing}
              error={errors.cart}
              isAuthenticated={auth.isAuthenticated}
              items={cart.items}
              loginHref={loginHref}
              onQuantityChange={updateItem}
              onRemove={removeItem}
            />
          ) : null}

          {activeStep === "address" ? <AddressStep errors={errors} form={form} onChange={updateField} /> : null}

          {activeStep === "delivery" ? (
            <DeliveryStep
              errors={errors}
              form={form}
              onChange={updateField}
              windows={deliveryWindows}
            />
          ) : null}

          {activeStep === "payment" ? <PaymentStep errors={errors} form={form} onChange={updateField} /> : null}

          {activeStep === "summary" ? (
            <SummaryStep
              form={form}
              onRefreshPreview={refreshPreview}
              preview={preview}
              previewLoading={previewLoading}
              windows={deliveryWindows}
            />
          ) : null}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Button disabled={activeStep === "items" || submitting} onClick={goBack} variant="secondary">
              Назад
            </Button>
            {activeStep === "summary" ? (
              <Button disabled={actionDisabled} loading={submitting || stockChecking} onClick={submitOrder} size="lg">
                {stockChecking ? "Проверяем остатки" : "Создать заказ"}
              </Button>
            ) : (
              <Button disabled={actionDisabled} loading={previewLoading} onClick={goNext} rightIcon={<ChevronRightIcon />}>
                Продолжить
              </Button>
            )}
          </div>
        </div>

        <aside className="xl:sticky xl:top-4">
          <CheckoutOrderSummary
            actionLabel={activeStep === "summary" ? "Создать заказ" : "Перейти к итогу"}
            cart={cart}
            disabled={actionDisabled}
            loading={previewLoading}
            onSubmit={activeStep === "summary" ? submitOrder : goNext}
            preview={preview}
            submitting={submitting || stockChecking}
          />
        </aside>
      </section>
    </div>
  );
}

function ItemsStep({
  items,
  cartLoading,
  cartSyncing,
  isAuthenticated,
  authReady,
  error,
  Link,
  loginHref,
  cartHref,
  onQuantityChange,
  onRemove,
}: {
  items: ReturnType<typeof useCart>["cart"]["items"];
  cartLoading: boolean;
  cartSyncing: boolean;
  isAuthenticated: boolean;
  authReady: boolean;
  error?: string;
  Link: StorefrontLinkComponent;
  loginHref: string;
  cartHref: string;
  onQuantityChange: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
}) {
  return (
    <Card className="p-5" variant="surface">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-h2 text-foreground">1. Подтверждение товаров</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">
            Проверьте состав продуктовой корзины. Остатки будут перепроверены перед созданием заказа.
          </p>
        </div>
        <Link
          className="focus-ring inline-flex min-h-[var(--control-height-md)] items-center justify-center rounded-md border border-border-strong bg-surface px-4 text-button font-bold text-foreground shadow-sm transition hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
          href={cartHref}
        >
          Открыть корзину
        </Link>
      </div>

      {!isAuthenticated && authReady ? (
        <div className="mt-4 rounded-md border border-warning-border bg-warning-soft p-4">
          <p className="text-body-sm font-black text-warning">Checkout доступен после входа</p>
          <p className="mt-1 text-body-sm text-muted-foreground">
            Гостевая корзина перенесётся в профиль автоматически после авторизации.
          </p>
          <Link
            className="focus-ring mt-3 inline-flex min-h-[var(--control-height-md)] items-center justify-center rounded-md bg-primary px-4 text-button font-bold text-primary-foreground shadow-sm transition hover:bg-primary-hover"
            href={loginHref}
          >
            Войти в аккаунт
          </Link>
        </div>
      ) : null}

      {error ? <p className="mt-4 rounded-md border border-danger-border bg-danger-soft px-3 py-2 text-body-sm font-semibold text-danger">{error}</p> : null}

      <div className="mt-5 grid gap-3">
        {cartLoading ? (
          <CartListSkeleton />
        ) : items.length ? (
          items.map((item) => (
            <CartLineItem
              disabled={cartSyncing}
              item={item}
              key={item.productId}
              onQuantityChange={onQuantityChange}
              onRemove={onRemove}
            />
          ))
        ) : (
          <div className="rounded-lg border border-dashed border-border bg-surface-raised p-6 text-center">
            <h3 className="text-h4 text-foreground">Корзина пустая</h3>
            <p className="mt-1 text-body-sm text-muted-foreground">Добавьте продукты перед оформлением заказа.</p>
          </div>
        )}
      </div>
    </Card>
  );
}

function AddressStep({
  form,
  errors,
  onChange,
}: {
  form: CheckoutFormState;
  errors: CheckoutFieldErrors;
  onChange: <FieldName extends CheckoutField>(field: FieldName, value: CheckoutFormState[FieldName]) => void;
}) {
  const isPickup = form.deliveryMethod === "pickup";

  return (
    <Card className="p-5" variant="surface">
      <h2 className="text-h2 text-foreground">2. Адрес и контакты</h2>
      <p className="mt-1 text-body-sm text-muted-foreground">Эти данные нужны для быстрой связи и аккуратной доставки заказа.</p>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <TextField
          error={errors.customerName}
          label="Получатель"
          onChange={(value) => onChange("customerName", value)}
          placeholder="Имя и фамилия"
          value={form.customerName}
        />
        <TextField
          error={errors.customerPhone}
          label="Телефон"
          onChange={(value) => onChange("customerPhone", value)}
          placeholder="+7 900 000-00-00"
          value={form.customerPhone}
        />
      </div>

      <Field className="mt-4">
        <FieldLabel htmlFor="customer-comment">Комментарий к заказу</FieldLabel>
        <Textarea
          id="customer-comment"
          onChange={(event) => onChange("customerComment", event.target.value)}
          placeholder="Например: позвонить перед заменой товара"
          value={form.customerComment}
        />
        <FieldHint>Комментарий увидит оператор заказа.</FieldHint>
      </Field>

      {isPickup ? (
        <div className="mt-5 rounded-lg border border-primary-border bg-primary-soft p-4">
          <Badge variant="primary">Самовывоз</Badge>
          <h3 className="mt-3 text-h4 text-foreground">Пункт выдачи GreenMart Premium</h3>
          <p className="mt-1 text-body-sm text-muted-foreground">
            Адрес доставки не требуется. Точный пункт выдачи закрепляется при сборке заказа.
          </p>
        </div>
      ) : (
        <div className="mt-5 grid gap-4">
          <TextField
            error={errors.deliveryAddressLine1}
            label="Улица, дом, корпус"
            onChange={(value) => onChange("deliveryAddressLine1", value)}
            placeholder="Ленинский проспект, 12"
            value={form.deliveryAddressLine1}
          />
          <TextField
            label="Комментарий к адресу"
            onChange={(value) => onChange("deliveryAddressLine2", value)}
            placeholder="Ориентир, название ЖК"
            value={form.deliveryAddressLine2}
          />
          <div className="grid gap-4 md:grid-cols-3">
            <TextField
              error={errors.deliveryCity}
              label="Город"
              onChange={(value) => onChange("deliveryCity", value)}
              value={form.deliveryCity}
            />
            <TextField
              label="Регион"
              onChange={(value) => onChange("deliveryRegion", value)}
              value={form.deliveryRegion}
            />
            <TextField
              error={errors.deliveryCountry}
              label="Страна"
              maxLength={2}
              onChange={(value) => onChange("deliveryCountry", value.toUpperCase())}
              value={form.deliveryCountry}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-5">
            <TextField label="Квартира" onChange={(value) => onChange("deliveryApartment", value)} value={form.deliveryApartment} />
            <TextField label="Этаж" onChange={(value) => onChange("deliveryFloor", value)} value={form.deliveryFloor} />
            <TextField label="Подъезд" onChange={(value) => onChange("deliveryEntrance", value)} value={form.deliveryEntrance} />
            <TextField label="Домофон" onChange={(value) => onChange("deliveryIntercom", value)} value={form.deliveryIntercom} />
            <TextField label="Индекс" onChange={(value) => onChange("deliveryPostalCode", value)} value={form.deliveryPostalCode} />
          </div>
        </div>
      )}

      <Field className="mt-4">
        <FieldLabel htmlFor="delivery-instructions">Инструкции для сборщика и курьера</FieldLabel>
        <Textarea
          id="delivery-instructions"
          onChange={(event) => onChange("deliveryInstructions", event.target.value)}
          placeholder="Например: не звонить в домофон, заменить зелёные бананы на спелые"
          value={form.deliveryInstructions}
        />
        <FieldHint>До 1000 символов. Можно оставить пустым.</FieldHint>
      </Field>
    </Card>
  );
}

function DeliveryStep({
  form,
  errors,
  windows,
  onChange,
}: {
  form: CheckoutFormState;
  errors: CheckoutFieldErrors;
  windows: ReturnType<typeof buildDeliveryWindows>;
  onChange: <FieldName extends CheckoutField>(field: FieldName, value: CheckoutFormState[FieldName]) => void;
}) {
  return (
    <Card className="p-5" variant="surface">
      <h2 className="text-h2 text-foreground">3. Способ доставки</h2>
      <p className="mt-1 text-body-sm text-muted-foreground">Стоимость доставки появится в финальном расчёте перед созданием заказа.</p>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {deliveryOptions.map((option) => (
          <SelectableCard
            active={form.deliveryMethod === option.id}
            badge={option.badge}
            description={`${option.description} ${option.priceHint}.`}
            key={option.id}
            meta={option.eta}
            onClick={() => onChange("deliveryMethod", option.id as DeliveryMethod)}
            title={option.title}
          />
        ))}
      </div>

      <div className="mt-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-h3 text-foreground">Интервал</h3>
          {errors.deliveryWindowId ? <FieldError>{errors.deliveryWindowId}</FieldError> : null}
        </div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {windows.map((windowOption) => (
            <SelectableCard
              active={form.deliveryWindowId === windowOption.id}
              description={windowOption.description}
              key={windowOption.id}
              onClick={() => onChange("deliveryWindowId", windowOption.id)}
              title={windowOption.title}
            />
          ))}
        </div>
      </div>
    </Card>
  );
}

function PaymentStep({
  form,
  errors,
  onChange,
}: {
  form: CheckoutFormState;
  errors: CheckoutFieldErrors;
  onChange: <FieldName extends CheckoutField>(field: FieldName, value: CheckoutFormState[FieldName]) => void;
}) {
  return (
    <Card className="p-5" variant="surface">
      <h2 className="text-h2 text-foreground">4. Оплата</h2>
      <p className="mt-1 text-body-sm text-muted-foreground">Выберите удобный способ оплаты. Онлайн-оплата поддерживает два демонстрационных провайдера.</p>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {paymentOptions.map((option) => (
          <SelectableCard
            active={form.paymentMethod === option.id}
            badge={option.badge}
            description={option.description}
            key={option.id}
            onClick={() => onChange("paymentMethod", option.id as PaymentMethod)}
            title={option.title}
          />
        ))}
      </div>
      {errors.paymentMethod ? <FieldError className="mt-3">{errors.paymentMethod}</FieldError> : null}

      {form.paymentMethod === "card_online" ? (
        <div className="mt-6 rounded-lg border border-border bg-surface-raised p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-h3 text-foreground">Платёжный провайдер</h3>
              <p className="mt-1 text-body-sm text-muted-foreground">Доступны два тестовых платёжных маршрута.</p>
            </div>
            {errors.paymentProvider ? <FieldError>{errors.paymentProvider}</FieldError> : null}
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {paymentProviderOptions.map((provider) => (
              <SelectableCard
                active={form.paymentProvider === provider.id}
                description={provider.description}
                key={provider.id}
                meta={provider.commissionLabel}
                onClick={() => onChange("paymentProvider", provider.id as PaymentProviderId)}
                title={provider.title}
              />
            ))}
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function SummaryStep({
  form,
  windows,
  preview,
  previewLoading,
  onRefreshPreview,
}: {
  form: CheckoutFormState;
  windows: ReturnType<typeof buildDeliveryWindows>;
  preview: CheckoutPreviewRead | null;
  previewLoading: boolean;
  onRefreshPreview: () => Promise<CheckoutPreviewRead>;
}) {
  const windowOption = windows.find((item) => item.id === form.deliveryWindowId);

  return (
    <Card className="p-5" variant="surface">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-h2 text-foreground">5. Summary заказа</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">
            Финальный расчёт фиксирует товары, доставку и итоговую сумму.
          </p>
        </div>
        <Button loading={previewLoading} onClick={onRefreshPreview} variant="secondary">
          Обновить расчёт
        </Button>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <SummaryBlock title="Получатель">
          <p>{form.customerName}</p>
          <p>{form.customerPhone}</p>
        </SummaryBlock>
        <SummaryBlock title="Доставка">
          <p>{deliveryOptions.find((option) => option.id === form.deliveryMethod)?.title}</p>
          <p>{windowOption ? `${windowOption.title}, ${windowOption.description}` : "Интервал не выбран"}</p>
          {form.deliveryMethod !== "pickup" ? <p>{[form.deliveryCity, form.deliveryAddressLine1].filter(Boolean).join(", ")}</p> : null}
        </SummaryBlock>
        <SummaryBlock title="Оплата">
          <p>{paymentOptions.find((option) => option.id === form.paymentMethod)?.title}</p>
          {form.paymentMethod === "card_online" ? <p>{paymentProviderOptions.find((provider) => provider.id === form.paymentProvider)?.title}</p> : null}
        </SummaryBlock>
        <SummaryBlock title="Price lock">
          {preview ? (
            <>
              <p>Расчёт: {formatCheckoutDate(preview.calculated_at)}</p>
              <p>Итого: {formatCartPrice(toNumber(preview.total_amount))}</p>
            </>
          ) : (
            <p>Расчёт ещё не выполнен</p>
          )}
        </SummaryBlock>
      </div>

      <div className="mt-5 rounded-lg border border-border bg-surface-raised p-4">
        <h3 className="text-h3 text-foreground">Линии заказа</h3>
        {previewLoading ? (
          <SkeletonText className="mt-3" lines={4} />
        ) : preview?.items.length ? (
          <div className="mt-3 grid gap-2">
            {preview.items.map((item) => (
              <div className="flex items-center justify-between gap-3 border-b border-border py-2 last:border-b-0" key={item.product_id}>
                <div className="min-w-0">
                  <p className="truncate text-body-sm font-bold text-foreground">{item.product_name}</p>
                  <p className="text-caption text-muted-foreground">
                    {item.quantity} x {formatCartPrice(toNumber(item.unit_price))}
                  </p>
                </div>
                <p className="text-body-sm font-black text-foreground">{formatCartPrice(toNumber(item.line_total))}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-body-sm text-muted-foreground">Финальный расчёт появится перед созданием заказа.</p>
        )}
      </div>
    </Card>
  );
}

function TextField({
  label,
  value,
  error,
  onChange,
  placeholder,
  maxLength,
}: {
  label: string;
  value: string;
  error?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
}) {
  const id = React.useId();
  return (
    <Field invalid={Boolean(error)}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        aria-invalid={Boolean(error) || undefined}
        id={id}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        value={value}
      />
      {error ? <FieldError>{error}</FieldError> : null}
    </Field>
  );
}

function SelectableCard({
  active,
  title,
  description,
  meta,
  badge,
  onClick,
}: {
  active: boolean;
  title: string;
  description: string;
  meta?: string;
  badge?: string;
  onClick: () => void;
}) {
  return (
    <button
      className={cn(
        "focus-ring grid min-h-[132px] gap-3 rounded-lg border p-4 text-left transition duration-200 ease-product hover:-translate-y-0.5",
        active ? "border-primary bg-primary-soft shadow-card-hover" : "border-border bg-surface hover:border-primary-border hover:bg-primary-soft",
      )}
      onClick={onClick}
      type="button"
    >
      <span className="flex items-start justify-between gap-3">
        <span className="text-body-sm font-black text-foreground">{title}</span>
        {badge ? <Badge variant={active ? "success" : "primary"}>{badge}</Badge> : null}
      </span>
      <span className="text-body-sm text-muted-foreground">{description}</span>
      {meta ? <span className="text-caption font-bold text-primary-active">{meta}</span> : null}
    </button>
  );
}

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-border bg-surface-raised p-4">
      <h3 className="text-caption font-bold uppercase text-muted-foreground">{title}</h3>
      <div className="mt-2 grid gap-1 text-body-sm font-semibold text-foreground">{children}</div>
    </div>
  );
}

function CartListSkeleton() {
  return (
    <>
      {Array.from({ length: 3 }).map((_, index) => (
        <div className="grid gap-4 rounded-lg border border-border bg-surface p-4 sm:grid-cols-[96px_minmax(0,1fr)_120px]" key={index}>
          <Skeleton className="aspect-square w-full" />
          <SkeletonText lines={3} />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
    </>
  );
}

function formatCheckoutDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
  }).format(new Date(value));
}

function toNumber(value: number | string) {
  return typeof value === "number" ? value : Number(value);
}
