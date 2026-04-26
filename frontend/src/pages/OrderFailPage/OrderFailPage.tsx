import * as React from "react";

import { CartIcon, XIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../app/layouts";
import { cn } from "../../shared/lib/cn";
import { Badge } from "../../shared/ui/Badge";
import { Card } from "../../shared/ui/Card";

export interface OrderFailPageProps {
  reason?: string;
  checkoutHref?: string;
  cartHref?: string;
  supportHref?: string;
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function OrderFailPage({
  reason,
  checkoutHref = "/checkout",
  cartHref = "/cart",
  supportHref = "/support",
  LinkComponent,
  className,
}: OrderFailPageProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const reasonFromQuery = useQueryParam("reason");
  const resolvedReason = reason ?? reasonFromQuery ?? "Платёж или создание заказа не завершились.";

  return (
    <div className={cn("grid gap-6 pb-6", className)}>
      <section className="rounded-lg border border-danger-border bg-danger-soft p-6 shadow-sm">
        <Badge variant="danger" dot>
          Заказ не создан
        </Badge>
        <h1 className="mt-4 text-h1 text-foreground">Не удалось завершить оформление</h1>
        <p className="mt-2 max-w-3xl text-body text-muted-foreground">
          Корзина сохранена. Проверьте товары, способ оплаты или повторите оформление через несколько минут.
        </p>
        <div className="mt-5 rounded-md border border-danger-border bg-surface px-4 py-3">
          <p className="text-caption font-bold uppercase text-muted-foreground">Причина</p>
          <p className="mt-1 text-body-sm font-semibold text-danger">{resolvedReason}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <RecoveryCard
          description="Вернитесь в checkout, чтобы повторить price lock и создать заказ заново."
          href={checkoutHref}
          icon={<XIcon />}
          Link={Link}
          title="Повторить оформление"
        />
        <RecoveryCard
          description="Проверьте остатки, количество и товары с ограниченным наличием."
          href={cartHref}
          icon={<CartIcon />}
          Link={Link}
          title="Проверить корзину"
        />
        <Card className="p-5" variant="surface">
          <Badge variant="primary">Поддержка</Badge>
          <h2 className="mt-3 text-h4 text-foreground">Нужна помощь?</h2>
          <p className="mt-2 text-body-sm text-muted-foreground">Передайте оператору текст ошибки и время попытки оформления.</p>
          <Link
            className="focus-ring mt-4 inline-flex min-h-[var(--control-height-md)] items-center justify-center rounded-md border border-border-strong bg-surface px-4 text-button font-bold text-foreground shadow-sm transition hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
            href={supportHref}
          >
            Написать в поддержку
          </Link>
        </Card>
      </section>
    </div>
  );
}

function RecoveryCard({
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
      <span className="grid h-11 w-11 place-items-center rounded-md bg-danger-soft text-danger transition group-hover:bg-danger group-hover:text-danger-foreground">
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
