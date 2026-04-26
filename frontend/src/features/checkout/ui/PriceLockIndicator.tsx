import { Badge } from "../../../shared/ui/Badge";
import { cn } from "../../../shared/lib/cn";

export interface PriceLockIndicatorProps {
  lockedAt?: string | null;
  expiresInMinutes?: number;
  loading?: boolean;
  className?: string;
}

export function PriceLockIndicator({
  lockedAt,
  expiresInMinutes = 15,
  loading,
  className,
}: PriceLockIndicatorProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-primary-border bg-primary-soft p-4 shadow-sm transition duration-200 ease-product",
        className,
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant={loading ? "neutral" : "success"} dot>
              {loading ? "Проверяем цены" : "Price lock"}
            </Badge>
            <span className="text-caption font-semibold text-muted-foreground">Финальная сумма под контролем</span>
          </div>
          <h2 className="mt-3 text-h4 text-foreground">Стоимость фиксируется перед созданием заказа</h2>
          <p className="mt-1 text-body-sm text-muted-foreground">
            После финального расчёта фиксируются актуальные цены, доставка и состав корзины.
          </p>
        </div>
        <div className="rounded-md border border-primary-border bg-surface px-3 py-2 text-right">
          <p className="text-caption font-bold uppercase text-muted-foreground">Окно фиксации</p>
          <p className="mt-1 text-body-sm font-black text-primary-active">{expiresInMinutes} минут</p>
          {lockedAt ? <p className="mt-1 text-caption text-muted-foreground">{formatLockTime(lockedAt)}</p> : null}
        </div>
      </div>
    </div>
  );
}

function formatLockTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
  }).format(new Date(value));
}
