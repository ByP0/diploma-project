import * as React from "react";

import { CartIcon, ChevronRightIcon, TagIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { cn } from "../../shared/lib/cn";
import { Badge } from "../../shared/ui/Badge";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { Skeleton, SkeletonText } from "../../shared/ui/Skeleton";
import { CartLineItem, CartSummary, formatCartPrice, useCart } from "../../features/cart";

export interface CartPageProps {
  LinkComponent?: StorefrontLinkComponent;
  checkoutHref?: string;
  catalogHref?: string;
  onCheckout?: () => void;
  className?: string;
}

export function CartPage({
  LinkComponent,
  checkoutHref = "/checkout",
  catalogHref = "/catalog",
  onCheckout,
  className,
}: CartPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const { cart, loading, syncing, isGuestCart, expirationLabel, updateItem, removeItem, clearCart } = useCart();
  const [promoCode, setPromoCode] = React.useState("");

  const hasItems = cart.items.length > 0;
  const hasStockIssues = cart.totals.unavailableItems > 0;
  const checkoutDisabled = loading || syncing || !hasItems || hasStockIssues;

  const handleCheckout = React.useCallback(() => {
    if (checkoutDisabled) {
      return;
    }

    if (onCheckout) {
      onCheckout();
      return;
    }

    if (typeof window !== "undefined") {
      window.location.assign(checkoutHref);
    }
  }, [checkoutDisabled, checkoutHref, onCheckout]);

  if (loading) {
    return <CartPageSkeleton className={className} />;
  }

  return (
    <div className={cn("grid gap-6 pb-6", className)}>
      <header className="grid gap-4 rounded-lg border border-primary-border bg-primary-soft p-5 shadow-sm md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="primary">Корзина</Badge>
            {isGuestCart && expirationLabel ? (
              <Badge variant="warning">Хранится ещё {expirationLabel}</Badge>
            ) : null}
            {hasStockIssues ? <Badge variant="danger">Проверьте остатки</Badge> : null}
          </div>
          <h1 className="mt-3 text-h1 text-foreground">Ваша корзина</h1>
          <p className="mt-2 max-w-3xl text-body text-muted-foreground">
            Проверьте количество, наличие и итоговую сумму перед оформлением заказа.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 md:justify-end">
          <Link
            className="focus-ring inline-flex min-h-[var(--control-height-md)] items-center justify-center gap-2 rounded-md border border-border-strong bg-surface px-4 text-button font-bold text-foreground shadow-sm transition hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
            href={catalogHref}
          >
            Продолжить покупки
            <ChevronRightIcon className="h-4 w-4" />
          </Link>
          {hasItems ? (
            <Button disabled={syncing} onClick={clearCart} variant="ghost">
              Очистить корзину
            </Button>
          ) : null}
        </div>
      </header>

      {hasItems ? (
        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] xl:items-start">
          <div className="grid gap-4">
            <CartStatusPanel
              hasStockIssues={hasStockIssues}
              isGuestCart={isGuestCart}
              expirationLabel={expirationLabel}
              totalAmount={cart.totals.totalAmount}
              totalItems={cart.totals.totalItems}
            />

            <div className="grid gap-3">
              {cart.items.map((item) => (
                <CartLineItem
                  disabled={syncing}
                  item={item}
                  key={item.productId}
                  onQuantityChange={updateItem}
                  onRemove={removeItem}
                />
              ))}
            </div>
          </div>

          <aside className="xl:sticky xl:top-4">
            <CartSummary
              cart={cart}
              checkoutDisabled={checkoutDisabled}
              onCheckout={handleCheckout}
              onPromoCodeChange={setPromoCode}
              promoCode={promoCode}
            />

            <Card className="mt-4 p-4" variant="muted">
              <div className="flex items-start gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-primary-soft text-primary-active">
                  <TagIcon />
                </span>
                <div>
                  <h2 className="text-h4 text-foreground">Промокоды и бонусы</h2>
                  <p className="mt-1 text-body-sm text-muted-foreground">
                    Поле промокода подготовлено в summary. Интеграция с checkout и loyalty API подключается отдельно.
                  </p>
                </div>
              </div>
            </Card>
          </aside>
        </section>
      ) : (
        <CartEmptyState Link={Link} catalogHref={catalogHref} />
      )}
    </div>
  );
}

function CartStatusPanel({
  hasStockIssues,
  isGuestCart,
  expirationLabel,
  totalItems,
  totalAmount,
}: {
  hasStockIssues: boolean;
  isGuestCart: boolean;
  expirationLabel: string | null;
  totalItems: number;
  totalAmount: number;
}) {
  return (
    <Card className="grid gap-3 p-4 sm:grid-cols-3" variant="surface">
      <StatusMetric label="Товаров" value={String(totalItems)} />
      <StatusMetric label="Сумма" value={formatCartPrice(totalAmount)} />
      <div
        className={cn(
          "rounded-md border px-3 py-2 transition duration-200",
          hasStockIssues ? "border-warning-border bg-warning-soft" : "border-success-border bg-success-soft",
        )}
      >
        <p className="text-caption font-bold uppercase text-muted-foreground">Наличие</p>
        <p className={cn("mt-1 text-body-sm font-black", hasStockIssues ? "text-warning" : "text-success")}>
          {hasStockIssues ? "Есть ограничения" : "Готово к заказу"}
        </p>
        {isGuestCart && expirationLabel ? (
          <p className="mt-1 text-caption text-muted-foreground">Гостевая корзина: {expirationLabel}</p>
        ) : null}
      </div>
    </Card>
  );
}

function StatusMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-surface-raised px-3 py-2">
      <p className="text-caption font-bold uppercase text-muted-foreground">{label}</p>
      <p className="mt-1 text-body-sm font-black text-foreground">{value}</p>
    </div>
  );
}

function CartEmptyState({
  Link,
  catalogHref,
}: {
  Link: StorefrontLinkComponent;
  catalogHref: string;
}) {
  return (
    <Card className="grid min-h-[420px] place-items-center p-6 text-center" variant="surface">
      <div className="max-w-md">
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-lg bg-primary-soft text-primary-active">
          <CartIcon className="h-8 w-8" />
        </span>
        <h2 className="mt-5 text-h2 text-foreground">Корзина пустая</h2>
        <p className="mt-2 text-body text-muted-foreground">
          Добавьте продукты из каталога, а мы сохраним гостевую корзину на 10 дней и перенесём её в профиль после входа.
        </p>
        <Link
          className="focus-ring mt-6 inline-flex min-h-[var(--control-height-lg)] items-center justify-center rounded-md bg-primary px-5 text-button-lg font-bold text-primary-foreground shadow-sm transition hover:bg-primary-hover"
          href={catalogHref}
        >
          Перейти в каталог
        </Link>
      </div>
    </Card>
  );
}

function CartPageSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("grid gap-6 pb-6", className)}>
      <Card className="p-5" variant="surface">
        <Skeleton className="h-6 w-36" />
        <Skeleton className="mt-4 h-10 w-64" />
        <Skeleton className="mt-3 h-5 w-2/3" />
      </Card>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] xl:items-start">
        <div className="grid gap-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Card className="grid gap-4 p-4 sm:grid-cols-[96px_minmax(0,1fr)_120px]" key={index} variant="surface">
              <Skeleton className="aspect-square w-full" />
              <SkeletonText lines={3} />
              <div className="grid content-between gap-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-9 w-full" />
              </div>
            </Card>
          ))}
        </div>
        <Card className="p-4" variant="surface">
          <Skeleton className="h-8 w-32" />
          <SkeletonText className="mt-4" lines={5} />
          <Skeleton className="mt-5 h-12 w-full" />
        </Card>
      </section>
    </div>
  );
}
