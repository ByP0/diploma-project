import * as React from "react";

import { CartIcon, XIcon } from "../../../app/layouts/StorefrontLayout/icons";
import { cn } from "../../../shared/lib/cn";
import { Badge } from "../../../shared/ui/Badge";
import { Button } from "../../../shared/ui/Button";
import { useCart } from "../model";
import { CartLineItem } from "./CartLineItem";
import { CartSummary } from "./CartSummary";
import { formatCartPrice } from "./cart-format";

export interface StickyCartDrawerProps {
  onCheckout?: () => void;
  className?: string;
}

export function StickyCartDrawer({ onCheckout, className }: StickyCartDrawerProps) {
  const {
    cart,
    drawerOpen,
    syncing,
    expirationLabel,
    isGuestCart,
    openDrawer,
    closeDrawer,
    updateItem,
    removeItem,
  } = useCart();
  const [promoCode, setPromoCode] = React.useState("");

  React.useEffect(() => {
    if (!drawerOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeDrawer();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [closeDrawer, drawerOpen]);

  return (
    <>
      <button
        aria-label="Открыть корзину"
        className={cn(
          "focus-ring fixed bottom-5 right-5 z-[var(--z-sticky-cart)] flex min-h-[64px] min-w-[220px] items-center justify-between gap-4 rounded-lg border border-primary-border bg-surface px-4 shadow-sticky-cart transition duration-200 ease-product hover:-translate-y-0.5 hover:bg-primary-soft",
          cart.totals.totalItems === 0 && "min-w-[64px] justify-center",
          className,
        )}
        onClick={openDrawer}
        type="button"
      >
        <span className="relative grid h-10 w-10 place-items-center rounded-md bg-primary text-primary-foreground">
          <CartIcon />
          {cart.totals.totalItems > 0 ? (
            <span className="absolute -right-2 -top-2 min-w-5 rounded-full bg-accent px-1 text-center text-[10px] font-black leading-5 text-accent-foreground">
              {cart.totals.totalItems > 99 ? "99+" : cart.totals.totalItems}
            </span>
          ) : null}
        </span>
        {cart.totals.totalItems > 0 ? (
          <span className="text-left">
            <span className="block text-caption font-bold uppercase text-muted-foreground">Корзина</span>
            <span className="block text-body-sm font-black text-foreground">{formatCartPrice(cart.totals.totalAmount)}</span>
          </span>
        ) : null}
      </button>

      <div
        className={cn(
          "fixed inset-0 z-[var(--z-modal)] transition duration-300",
          drawerOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
        )}
      >
        <button
          aria-label="Закрыть корзину"
          className="absolute inset-0 bg-foreground/[0.35] backdrop-blur-sm"
          onClick={closeDrawer}
          type="button"
        />
        <aside
          aria-label="Корзина"
          className={cn(
            "absolute inset-y-0 right-0 flex w-[min(460px,94vw)] flex-col bg-surface shadow-modal transition duration-300 ease-product",
            drawerOpen ? "translate-x-0" : "translate-x-full",
          )}
        >
          <header className="flex min-h-[72px] items-center justify-between gap-3 border-b border-border px-5">
            <div>
              <h2 className="text-h3 text-foreground">Корзина</h2>
              {isGuestCart && expirationLabel ? (
                <p className="mt-1 text-caption text-muted-foreground">Гостевая корзина хранится ещё {expirationLabel}</p>
              ) : null}
            </div>
            <Button aria-label="Закрыть корзину" onClick={closeDrawer} size="iconMd" variant="ghost">
              <XIcon />
            </Button>
          </header>

          <div className="min-h-0 flex-1 overflow-y-auto p-4 scrollbar-soft">
            {cart.totals.unavailableItems > 0 ? (
              <Badge className="mb-3" variant="warning">
                Есть товары с ограниченным остатком
              </Badge>
            ) : null}

            {cart.items.length ? (
              <div className="grid gap-3">
                {cart.items.map((item) => (
                  <CartLineItem
                    compact
                    disabled={syncing}
                    item={item}
                    key={item.productId}
                    onQuantityChange={updateItem}
                    onRemove={removeItem}
                  />
                ))}
              </div>
            ) : (
              <div className="grid min-h-[280px] place-items-center rounded-lg border border-dashed border-border bg-surface-raised p-6 text-center">
                <div>
                  <p className="text-h4 text-foreground">Корзина пустая</p>
                  <p className="mt-2 text-body-sm text-muted-foreground">Добавьте свежие продукты из каталога.</p>
                </div>
              </div>
            )}
          </div>

          <footer className="border-t border-border p-4">
            <CartSummary
              cart={cart}
              checkoutDisabled={syncing || cart.totals.unavailableItems > 0}
              compact
              onCheckout={onCheckout}
              onPromoCodeChange={setPromoCode}
              promoCode={promoCode}
            />
          </footer>
        </aside>
      </div>
    </>
  );
}
