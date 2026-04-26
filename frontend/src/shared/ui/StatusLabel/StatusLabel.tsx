import { Badge, type BadgeVariant } from "../Badge";

export type StatusNamespace = "order" | "payment" | "support" | "inventory";

const orderLabels = {
  created: ["Создан", "info"],
  awaiting_payment: ["Ожидает оплаты", "warning"],
  paid: ["Оплачен", "success"],
  processing: ["В обработке", "info"],
  packed: ["Собран", "primary"],
  shipped: ["В доставке", "primary"],
  delivered: ["Доставлен", "success"],
  cancelled: ["Отменён", "danger"],
  refunded: ["Возврат", "accent"],
  failed: ["Ошибка", "danger"],
} as const;

const paymentLabels = {
  pending: ["Ожидает", "warning"],
  succeeded: ["Успешно", "success"],
  failed: ["Ошибка", "danger"],
  cancelled: ["Отменён", "neutral"],
  refunded: ["Возврат", "accent"],
  partially_refunded: ["Частичный возврат", "accent"],
} as const;

const supportLabels = {
  open: ["Открыто", "info"],
  in_progress: ["В работе", "primary"],
  waiting_customer: ["Ждёт клиента", "warning"],
  resolved: ["Решено", "success"],
  closed: ["Закрыто", "neutral"],
} as const;

const inventoryLabels = {
  in_stock: ["В наличии", "success"],
  low_stock: ["Заканчивается", "warning"],
  out_of_stock: ["Нет в наличии", "danger"],
  reserved: ["Зарезервировано", "info"],
} as const;

const namespaces = {
  order: orderLabels,
  payment: paymentLabels,
  support: supportLabels,
  inventory: inventoryLabels,
} satisfies Record<StatusNamespace, Record<string, readonly [string, BadgeVariant]>>;

export interface StatusLabelProps {
  namespace: StatusNamespace;
  status: string;
  dot?: boolean;
  className?: string;
}

export function StatusLabel({ namespace, status, dot = true, className }: StatusLabelProps) {
  const labels = namespaces[namespace] as Record<string, readonly [string, BadgeVariant]>;
  const config = labels[status];
  const label = config?.[0] ?? status;
  const variant = config?.[1] ?? "neutral";

  return (
    <Badge variant={variant} dot={dot} className={className}>
      {label}
    </Badge>
  );
}
