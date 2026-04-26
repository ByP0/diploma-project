import * as React from "react";

import { CartIcon, PackageIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { cn } from "../../shared/lib/cn";
import { Badge } from "../../shared/ui/Badge";
import { Card } from "../../shared/ui/Card";

export interface OrderSuccessPageProps {
  orderId?: string;
  ordersHref?: string;
  catalogHref?: string;
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function OrderSuccessPage({
  orderId,
  ordersHref = "/profile/orders",
  catalogHref = "/catalog",
  LinkComponent,
  className,
}: OrderSuccessPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const orderIdFromQuery = useQueryParam("orderId");
  const resolvedOrderId = orderId ?? orderIdFromQuery;

  return (
    <div className={cn("grid gap-6 pb-6", className)}>
      <section className="rounded-lg border border-success-border bg-success-soft p-6 shadow-sm">
        <Badge variant="success" dot>
          Заказ создан
        </Badge>
        <h1 className="mt-4 text-h1 text-foreground">Спасибо, заказ принят в работу</h1>
        <p className="mt-2 max-w-3xl text-body text-muted-foreground">
          Мы зафиксировали цены, состав корзины и способ доставки. Следите за статусом в личном кабинете.
        </p>
        {resolvedOrderId ? (
          <div className="mt-5 inline-flex rounded-md border border-success-border bg-surface px-4 py-3">
            <span className="text-body-sm font-bold text-muted-foreground">Номер заказа:&nbsp;</span>
            <span className="text-body-sm font-black text-foreground">{resolvedOrderId}</span>
          </div>
        ) : null}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <NextStepCard
          description="Проверяйте сборку, оплату и доставку в одном месте."
          href={ordersHref}
          icon={<PackageIcon />}
          Link={Link}
          title="Перейти к заказам"
        />
        <NextStepCard
          description="Добавьте регулярные продукты для следующей доставки."
          href={catalogHref}
          icon={<CartIcon />}
          Link={Link}
          title="Вернуться в каталог"
        />
        <Card className="p-5" variant="surface">
          <Badge variant="primary">Price lock</Badge>
          <h2 className="mt-3 text-h4 text-foreground">Цена зафиксирована</h2>
          <p className="mt-2 text-body-sm text-muted-foreground">
            Если онлайн-оплата требует подтверждения, платёжный экран откроется отдельным шагом.
          </p>
        </Card>
      </section>
    </div>
  );
}

function NextStepCard({
  title,
  description,
  href,
  icon,
  Link,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
  Link: StorefrontLinkComponent;
}) {
  return (
    <Link
      className="group rounded-lg border border-border bg-surface p-5 shadow-sm transition duration-200 ease-product hover:-translate-y-0.5 hover:border-primary-border hover:bg-primary-soft hover:shadow-card-hover"
      href={href}
    >
      <span className="grid h-11 w-11 place-items-center rounded-md bg-primary-soft text-primary-active transition group-hover:bg-primary group-hover:text-primary-foreground">
        {icon}
      </span>
      <h2 className="mt-4 text-h4 text-foreground">{title}</h2>
      <p className="mt-2 text-body-sm text-muted-foreground">{description}</p>
    </Link>
  );
}

function useQueryParam(name: string) {
  const [value, setValue] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    setValue(new URLSearchParams(window.location.search).get(name));
  }, [name]);

  return value;
}
