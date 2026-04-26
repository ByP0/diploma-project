import { formatCartPrice } from "../../cart";
import { cn } from "../../../shared/lib/cn";
import { Badge } from "../../../shared/ui/Badge";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Skeleton, SkeletonText } from "../../../shared/ui/Skeleton";
import type { CartState } from "../../cart";
import type { CheckoutPreviewRead } from "../model";

export interface CheckoutOrderSummaryProps {
  cart: CartState;
  preview?: CheckoutPreviewRead | null;
  loading?: boolean;
  submitting?: boolean;
  disabled?: boolean;
  actionLabel?: string;
  onSubmit?: () => void;
  className?: string;
}

export function CheckoutOrderSummary({
  cart,
  preview,
  loading,
  submitting,
  disabled,
  actionLabel = "Создать заказ",
  onSubmit,
  className,
}: CheckoutOrderSummaryProps) {
  const itemsTotal = toNumber(preview?.items_total_amount ?? cart.totals.totalAmount);
  const deliveryCost = toNumber(preview?.delivery_cost ?? 0);
  const total = toNumber(preview?.total_amount ?? cart.totals.totalAmount + deliveryCost);

  return (
    <Card className={cn("p-4", className)} variant="surface">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-h3 text-foreground">Итого заказа</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">{cart.totals.totalItems} товаров в корзине</p>
        </div>
        <Badge variant={preview ? "success" : "primary"}>{preview ? "Рассчитано" : "Черновик"}</Badge>
      </div>

      {loading ? (
        <div className="mt-5">
          <SkeletonText lines={4} />
          <Skeleton className="mt-5 h-12 w-full" />
        </div>
      ) : (
        <>
          <dl className="mt-5 grid gap-2 text-body-sm">
            <SummaryRow label="Товары" value={formatCartPrice(itemsTotal)} />
            <SummaryRow label="Доставка" value={deliveryCost > 0 ? formatCartPrice(deliveryCost) : "Бесплатно"} />
            {cart.totals.totalDiscount > 0 ? (
              <SummaryRow label="Выгода" tone="success" value={formatCartPrice(cart.totals.totalDiscount)} />
            ) : null}
          </dl>

          <div className="mt-5 border-t border-border pt-4">
            <div className="flex items-end justify-between gap-3">
              <span className="text-body-sm font-bold text-muted-foreground">К оплате</span>
              <strong className="text-h2 text-foreground">{formatCartPrice(total)}</strong>
            </div>
            <Button
              className="mt-4"
              disabled={disabled || cart.totals.totalItems === 0}
              fullWidth
              loading={submitting}
              onClick={onSubmit}
              size="lg"
            >
              {actionLabel}
            </Button>
          </div>
        </>
      )}
    </Card>
  );
}

function SummaryRow({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("font-bold text-foreground", tone === "success" && "text-success")}>{value}</dd>
    </div>
  );
}

function toNumber(value: number | string) {
  return typeof value === "number" ? value : Number(value);
}
