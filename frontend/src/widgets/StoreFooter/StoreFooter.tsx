import { cn } from "../../shared/lib/cn";
import { Button } from "../../shared/ui/Button";
import { Input } from "../../shared/ui/Input";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { FooterColumn, SocialLink, StorefrontLinkComponent } from "../../app/layouts/StorefrontLayout/types";

export interface StoreFooterProps {
  columns: FooterColumn[];
  socialLinks: SocialLink[];
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function StoreFooter({ columns, socialLinks, LinkComponent, className }: StoreFooterProps) {
  const Link = resolveLinkComponent(LinkComponent);

  return (
    <footer className={cn("border-t border-border bg-surface-raised", className)}>
      <div className="store-container grid gap-8 py-10 lg:grid-cols-[minmax(280px,360px)_minmax(0,1fr)]">
        <section className="min-w-0">
          <Link className="inline-flex items-center gap-2 text-foreground hover:text-foreground" href="/">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-primary text-lg font-black text-primary-foreground">
              G
            </span>
            <span>
              <span className="block font-display text-[20px] font-black">GreenMart</span>
              <span className="block text-caption font-semibold text-primary-active">premium grocery marketplace</span>
            </span>
          </Link>
          <p className="mt-4 max-w-sm text-body-sm text-muted-foreground">
            Онлайн-магазин свежих продуктов с аккуратной доставкой, прозрачной оплатой и поддержкой покупателей.
          </p>

          <form className="mt-5 flex max-w-sm gap-2" action="/subscribe" method="post">
            <Input aria-label="Email для подписки" name="email" placeholder="Email для акций" type="email" />
            <Button type="submit" variant="primary">
              Подписаться
            </Button>
          </form>
        </section>

        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {columns.map((column) => (
            <section key={column.title}>
              <h2 className="mb-3 text-body-sm font-black text-foreground">{column.title}</h2>
              <nav className="grid gap-2" aria-label={column.title}>
                {column.links.map((link) => (
                  <Link
                    className="text-body-sm font-medium text-muted-foreground hover:text-primary-active"
                    href={link.href}
                    key={link.href}
                  >
                    {link.label}
                  </Link>
                ))}
              </nav>
            </section>
          ))}
        </div>
      </div>

      <div className="border-t border-border">
        <div className="store-container flex flex-col gap-4 py-5 text-body-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
          <p>© 2026 GreenMart. Все права защищены.</p>
          <nav aria-label="Социальные сети" className="flex flex-wrap items-center gap-3">
            {socialLinks.map((link) => (
              <Link
                className="rounded-md border border-border bg-surface px-3 py-1.5 font-semibold text-foreground hover:border-primary-border hover:bg-primary-soft hover:text-primary-active"
                href={link.href}
                key={link.href}
                rel="noreferrer"
                target="_blank"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}
