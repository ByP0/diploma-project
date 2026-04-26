import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import type { CartState } from "../model";
import { formatCartPrice } from "./cart-format";

export interface CartSummaryProps {
  cart: CartState;
  promoCode: string;
  onPromoCodeChange: (value: string) => void;
  onCheckout?: () => void;
  checkoutDisabled?: boolean;
  compact?: boolean;
}

export function CartSummary({
  cart,
  promoCode,
  onPromoCodeChange,
  onCheckout,
  checkoutDisabled,
  compact,
}: CartSummaryProps) {
  return (
    <Card className="p-4" variant="surface">
      <h2 className={compact ? "text-h4" : "text-h3"}>Итого</h2>

      <dl className="mt-4 grid gap-2 text-body-sm">
        <div className="flex items-center justify-between gap-3">
          <dt className="text-muted-foreground">Товары</dt>
          <dd className="font-bold text-foreground">{cart.totals.totalItems}</dd>
        </div>
        <div className="flex items-center justify-between gap-3">
          <dt className="text-muted-foreground">Сумма</dt>
          <dd className="font-bold text-foreground">{formatCartPrice(cart.totals.totalAmount)}</dd>
        </div>
        {cart.totals.totalDiscount > 0 ? (
          <div className="flex items-center justify-between gap-3">
            <dt className="text-muted-foreground">Выгода</dt>
            <dd className="font-bold text-success">{formatCartPrice(cart.totals.totalDiscount)}</dd>
          </div>
        ) : null}
      </dl>

      <div className="mt-4 rounded-md border border-dashed border-border-strong bg-surface-raised p-3">
        <label className="text-caption font-bold uppercase text-muted-foreground" htmlFor={compact ? "drawer-promo" : "cart-promo"}>
          Промокод
        </label>
        <div className="mt-2 grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
          <Input
            id={compact ? "drawer-promo" : "cart-promo"}
            onChange={(event) => onPromoCodeChange(event.target.value)}
            placeholder="Скоро"
            value={promoCode}
          />
          <Button disabled variant="secondary">
            Применить
          </Button>
        </div>
        <p className="mt-2 text-caption text-muted-foreground">Промокоды будут подключены на этапе checkout.</p>
      </div>

      <div className="mt-4 border-t border-border pt-4">
        <div className="flex items-end justify-between gap-3">
          <span className="text-body-sm font-bold text-muted-foreground">К оплате</span>
          <strong className="text-h2 text-foreground">{formatCartPrice(cart.totals.totalAmount)}</strong>
        </div>
        <Button className="mt-4" disabled={checkoutDisabled || cart.totals.totalItems === 0} fullWidth onClick={onCheckout} size="lg">
          Перейти к оформлению
        </Button>
      </div>
    </Card>
  );
}
