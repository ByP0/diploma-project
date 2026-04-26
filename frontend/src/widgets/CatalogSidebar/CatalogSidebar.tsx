import type { ReactNode } from "react";

import { Badge } from "../../shared/ui/Badge";
import { Card } from "../../shared/ui/Card";
import { cn } from "../../shared/lib/cn";
import { ChevronRightIcon, TagIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type { NavigationItem, StorefrontLinkComponent } from "../../app/layouts/StorefrontLayout/types";

export interface CatalogSidebarProps {
  categories: NavigationItem[];
  brands: NavigationItem[];
  farmerLinks: NavigationItem[];
  newLinks: NavigationItem[];
  LinkComponent?: StorefrontLinkComponent;
  sticky?: boolean;
  className?: string;
  onNavigate?: () => void;
}

export function CatalogSidebar({
  categories,
  brands,
  farmerLinks,
  newLinks,
  LinkComponent,
  sticky = false,
  className,
  onNavigate,
}: CatalogSidebarProps) {
  const Link = resolveLinkComponent(LinkComponent);

  return (
    <aside className={cn(sticky && "sticky top-[156px]", className)} aria-label="Каталог товаров">
      <Card className="overflow-hidden" variant="surface">
        <SidebarSection title="Каталог продуктов">
          <nav className="grid gap-1" aria-label="Продуктовые категории">
            {categories.map((item) => (
              <Link
                className={cn(
                  "group flex min-h-10 items-center justify-between gap-3 rounded-md px-3 text-body-sm font-semibold text-foreground transition hover:bg-primary-soft hover:text-primary-active",
                  item.active && "bg-primary-soft text-primary-active",
                )}
                href={item.href}
                key={item.href}
                onClick={onNavigate}
              >
                <span className="min-w-0 truncate">{item.label}</span>
                <span className="flex shrink-0 items-center gap-2 text-caption text-muted-foreground group-hover:text-primary-active">
                  {typeof item.count === "number" ? item.count : null}
                  <ChevronRightIcon className="h-4 w-4" />
                </span>
              </Link>
            ))}
          </nav>
        </SidebarSection>

        <SidebarSection title="Бренды">
          <CompactLinkList items={brands} Link={Link} onNavigate={onNavigate} />
        </SidebarSection>

        <SidebarSection title="Фермерские товары">
          <CompactLinkList items={farmerLinks} Link={Link} onNavigate={onNavigate} />
        </SidebarSection>

        <SidebarSection title="Новинки">
          <CompactLinkList items={newLinks} Link={Link} onNavigate={onNavigate} showBadges />
        </SidebarSection>

        <div className="border-t border-border bg-primary-soft p-4">
          <div className="flex items-start gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground">
              <TagIcon className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="text-body-sm font-bold text-foreground">Premium supermarket</p>
              <p className="mt-1 text-caption text-muted-foreground">
                Свежие поставки, проверенные фермеры и бережная доставка.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </aside>
  );
}

function SidebarSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-b border-border p-4 last:border-b-0">
      <h2 className="mb-3 text-caption font-black uppercase text-muted-foreground">{title}</h2>
      {children}
    </section>
  );
}

function CompactLinkList({
  items,
  Link,
  onNavigate,
  showBadges,
}: {
  items: NavigationItem[];
  Link: StorefrontLinkComponent;
  onNavigate?: () => void;
  showBadges?: boolean;
}) {
  return (
    <nav className="grid gap-1">
      {items.map((item) => (
        <Link
          className="flex min-h-9 items-center justify-between gap-2 rounded-md px-3 text-body-sm font-semibold text-foreground transition hover:bg-muted hover:text-primary-active"
          href={item.href}
          key={item.href}
          onClick={onNavigate}
        >
          <span className="min-w-0 truncate">{item.label}</span>
          {showBadges && item.badge ? (
            <Badge size="sm" variant={item.badge === "sale" ? "accent" : "primary"}>
              {item.badge}
            </Badge>
          ) : null}
        </Link>
      ))}
    </nav>
  );
}
