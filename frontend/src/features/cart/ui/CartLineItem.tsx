import { XIcon } from "../../../app/layouts/StorefrontLayout/icons";
import { cn } from "../../../shared/lib/cn";
import { Badge } from "../../../shared/ui/Badge";
import { Button } from "../../../shared/ui/Button";
import { getAvailableStock } from "../model";
import type { CartItem } from "../model";
import { CartQuantityStepper } from "./CartQuantityStepper";
import { formatCartPrice } from "./cart-format";

export interface CartLineItemProps {
  item: CartItem;
  compact?: boolean;
  disabled?: boolean;
  onQuantityChange: (productId: string, quantity: number) => void;
  onRemove: (productId: string) => void;
}

export function CartLineItem({
  item,
  compact = false,
  disabled,
  onQuantityChange,
  onRemove,
}: CartLineItemProps) {
  const availableStock = getAvailableStock(item.product);
  const hasStockIssue = availableStock <= 0 || item.quantity > availableStock;

  return (
    <article
      className={cn(
        "grid gap-3 rounded-lg border border-border bg-surface p-3 transition duration-200 ease-product hover:border-primary-border",
        compact ? "grid-cols-[72px_minmax(0,1fr)]" : "sm:grid-cols-[96px_minmax(0,1fr)_auto]",
        hasStockIssue && "border-warning-border bg-warning-soft",
      )}
    >
      <a className="block overflow-hidden rounded-md bg-muted" href={item.product.href ?? `/products/${item.productId}`}>
        {item.product.imageUrl ? (
          <img alt={item.product.name} className="aspect-square h-full w-full object-cover" loading="lazy" src={item.product.imageUrl} />
        ) : (
          <span className="grid aspect-square place-items-center text-caption text-muted-foreground">Нет фото</span>
        )}
      </a>

      <div className="min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <a
              className="block max-h-[42px] overflow-hidden text-body-sm font-black text-foreground hover:text-primary-active"
              href={item.product.href ?? `/products/${item.productId}`}
            >
              {item.product.name}
            </a>
            <p className="mt-1 text-caption text-muted-foreground">
              {item.product.brand ? `${item.product.brand} · ` : null}
              {item.product.unit}
            </p>
          </div>

          {compact ? (
            <Button aria-label="Удалить товар" onClick={() => onRemove(item.productId)} size="iconSm" variant="ghost">
              <XIcon className="h-4 w-4" />
            </Button>
          ) : null}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <CartQuantityStepper
            disabled={disabled || availableStock <= 0}
            max={Math.max(availableStock, 1)}
            onChange={(quantity) => onQuantityChange(item.productId, quantity)}
            value={item.quantity}
          />
          {hasStockIssue ? (
            <Badge variant="warning">Доступно {availableStock}</Badge>
          ) : availableStock <= 5 ? (
            <Badge variant="warning">Осталось {availableStock}</Badge>
          ) : null}
        </div>
      </div>

      <div className={cn("flex items-end justify-between gap-3 sm:flex-col sm:items-end", compact && "col-span-2 flex-row")}>
        <div className="text-right">
          <p className="text-body-sm font-black text-foreground">{formatCartPrice(item.subtotal)}</p>
          <p className="text-caption text-muted-foreground">{formatCartPrice(item.unitPrice)} / {item.product.unit}</p>
        </div>
        {!compact ? (
          <Button aria-label="Удалить товар" onClick={() => onRemove(item.productId)} size="iconSm" variant="ghost">
            <XIcon className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </article>
  );
}
