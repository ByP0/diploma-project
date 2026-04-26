import { ChevronRightIcon } from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type {
  BreadcrumbItem,
  NavigationItem,
  StorefrontLinkComponent,
} from "../../app/layouts/StorefrontLayout/types";
import { cn } from "../../shared/lib/cn";

export interface SecondaryNavigationProps {
  breadcrumbs: BreadcrumbItem[];
  quickCategories: NavigationItem[];
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function SecondaryNavigation({
  breadcrumbs,
  quickCategories,
  LinkComponent,
  className,
}: SecondaryNavigationProps) {
  const Link = resolveLinkComponent(LinkComponent);

  return (
    <section className={cn("category-menu", className)}>
      <div className="store-container grid gap-2 py-2">
        <nav aria-label="Хлебные крошки" className="flex min-w-0 items-center gap-1 overflow-x-auto text-caption scrollbar-soft">
          {breadcrumbs.map((item, index) => {
            const isLast = index === breadcrumbs.length - 1;
            return (
              <span className="flex shrink-0 items-center gap-1" key={`${item.label}-${index}`}>
                {item.href && !isLast ? (
                  <Link className="text-muted-foreground hover:text-primary-active" href={item.href}>
                    {item.label}
                  </Link>
                ) : (
                  <span aria-current={isLast ? "page" : undefined} className="font-semibold text-foreground">
                    {item.label}
                  </span>
                )}
                {!isLast ? <ChevronRightIcon className="h-3.5 w-3.5 text-muted-foreground" /> : null}
              </span>
            );
          })}
        </nav>

        <nav
          aria-label="Быстрые категории"
          className="flex min-h-[44px] min-w-0 items-center gap-2 overflow-x-auto scrollbar-soft"
        >
          {quickCategories.map((item) => (
            <Link
              className={cn("category-menu-item", item.active && "bg-primary-soft text-primary-active")}
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </section>
  );
}
