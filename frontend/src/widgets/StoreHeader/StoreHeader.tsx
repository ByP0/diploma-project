import * as React from "react";

import { Button } from "../../shared/ui/Button";
import { Input } from "../../shared/ui/Input";
import { cn } from "../../shared/lib/cn";
import {
  CartIcon,
  HeartIcon,
  MenuIcon,
  PackageIcon,
  SearchIcon,
  TagIcon,
  UserIcon,
} from "../../app/layouts/StorefrontLayout/icons";
import { resolveLinkComponent } from "../../app/layouts/StorefrontLayout/link";
import type {
  StorefrontCounters,
  StorefrontLinkComponent,
  StorefrontUserSummary,
} from "../../app/layouts/StorefrontLayout/types";

export interface StoreHeaderProps {
  user?: StorefrontUserSummary;
  counters?: StorefrontCounters;
  searchQuery?: string;
  defaultSearchQuery?: string;
  onSearchQueryChange?: (query: string) => void;
  onSearchSubmit?: (query: string) => void;
  onCatalogToggle: () => void;
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function StoreHeader({
  user,
  counters,
  searchQuery,
  defaultSearchQuery = "",
  onSearchQueryChange,
  onSearchSubmit,
  onCatalogToggle,
  LinkComponent,
  className,
}: StoreHeaderProps) {
  const Link = resolveLinkComponent(LinkComponent);
  const [internalQuery, setInternalQuery] = React.useState(defaultSearchQuery);
  const query = searchQuery ?? internalQuery;
  const isAuthenticated = Boolean(user?.isAuthenticated);
  const profileLabel = isAuthenticated ? user?.name || user?.email || "Профиль" : "Войти";

  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextQuery = event.target.value;
    if (searchQuery === undefined) {
      setInternalQuery(nextQuery);
    }
    onSearchQueryChange?.(nextQuery);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    if (!onSearchSubmit) {
      return;
    }

    event.preventDefault();
    onSearchSubmit(query.trim());
  };

  return (
    <header className={cn("store-header", className)}>
      <div className="border-b border-border bg-surface-raised">
        <div className="store-container flex min-h-9 items-center justify-between gap-4 text-caption text-muted-foreground">
          <span className="hidden md:inline">Доставка свежих продуктов сегодня и завтра</span>
          <nav aria-label="Сервисная навигация" className="flex min-w-0 items-center gap-4 overflow-x-auto scrollbar-soft">
            <Link className="whitespace-nowrap text-muted-foreground hover:text-primary-active" href="/delivery">
              Доставка
            </Link>
            <Link className="whitespace-nowrap text-muted-foreground hover:text-primary-active" href="/payment">
              Оплата
            </Link>
            <Link className="whitespace-nowrap text-muted-foreground hover:text-primary-active" href="/support">
              Поддержка
            </Link>
            <a className="whitespace-nowrap text-muted-foreground hover:text-primary-active" href="tel:+78002501010">
              +7 800 250-10-10
            </a>
          </nav>
        </div>
      </div>

      <div className="store-header-row">
        <button
          type="button"
          aria-label="Открыть каталог"
          className="focus-ring inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-border bg-surface text-foreground lg:hidden"
          onClick={onCatalogToggle}
        >
          <MenuIcon />
        </button>

        <Link className="group flex min-w-[148px] shrink-0 items-center gap-2 text-foreground hover:text-foreground" href="/">
          <span className="grid h-11 w-11 place-items-center rounded-lg bg-primary text-lg font-black text-primary-foreground">
            G
          </span>
          <span className="hidden leading-tight sm:block">
            <span className="block font-display text-[20px] font-black text-foreground">GreenMart</span>
            <span className="block text-caption font-semibold text-primary-active">premium grocery</span>
          </span>
        </Link>

        <Button
          className="hidden shrink-0 lg:inline-flex"
          leftIcon={<MenuIcon />}
          onClick={onCatalogToggle}
          size="lg"
          variant="primary"
        >
          Каталог
        </Button>

        <form
          action="/catalog"
          className="hidden min-w-0 flex-1 md:block"
          method="get"
          onSubmit={handleSubmit}
          role="search"
        >
          <div className="store-search-shell">
            <Input
              aria-label="Поиск товаров"
              className="border-0 bg-transparent px-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
              inputSize="lg"
              leftSlot={<SearchIcon className="h-5 w-5" />}
              name="search"
              onChange={handleQueryChange}
              placeholder="Поиск продуктов, брендов и категорий"
              type="search"
              value={query}
              variant="search"
            />
            <Button className="ml-3 shrink-0" size="md" type="submit">
              Найти
            </Button>
          </div>
        </form>

        <nav aria-label="Основные действия" className="ml-auto flex shrink-0 items-center gap-1">
          <HeaderAction href="/promotions" icon={<TagIcon />} label="Акции" Link={Link} />
          <HeaderAction
            count={counters?.favoriteItems}
            href="/favorites"
            icon={<HeartIcon />}
            label="Избранное"
            Link={Link}
          />
          <HeaderAction
            count={counters?.orderItems}
            href="/account/orders"
            icon={<PackageIcon />}
            label="Заказы"
            Link={Link}
          />
          <HeaderAction
            href={isAuthenticated ? "/account" : "/login"}
            icon={<UserIcon />}
            label={profileLabel}
            Link={Link}
            mobileVisible
          />
          <HeaderAction
            accent
            count={counters?.cartItems}
            href="/cart"
            icon={<CartIcon />}
            label={counters?.cartTotal || "Корзина"}
            Link={Link}
            mobileVisible
          />
        </nav>
      </div>

      <div className="store-container pb-3 md:hidden">
        <form action="/catalog" method="get" onSubmit={handleSubmit} role="search">
          <Input
            aria-label="Поиск товаров"
            inputSize="lg"
            leftSlot={<SearchIcon className="h-5 w-5" />}
            name="search"
            onChange={handleQueryChange}
            placeholder="Поиск продуктов"
            type="search"
            value={query}
            variant="search"
          />
        </form>
      </div>
    </header>
  );
}

interface HeaderActionProps {
  href: string;
  label: string;
  icon: React.ReactNode;
  Link: StorefrontLinkComponent;
  count?: number;
  accent?: boolean;
  mobileVisible?: boolean;
}

function HeaderAction({ href, label, icon, Link, count, accent, mobileVisible }: HeaderActionProps) {
  return (
    <Link
      aria-label={count ? `${label}, ${count}` : label}
      className={cn(
        "focus-ring relative min-h-[48px] flex-col items-center justify-center gap-1 rounded-md px-2 text-caption font-bold text-foreground transition hover:bg-primary-soft hover:text-primary-active",
        mobileVisible ? "inline-flex min-w-[48px] sm:min-w-[62px]" : "hidden min-w-[62px] sm:inline-flex",
        accent && "bg-primary-soft text-primary-active",
      )}
      href={href}
    >
      <span className="relative">
        {icon}
        {count ? (
          <span className="absolute -right-2 -top-2 min-w-5 rounded-full bg-accent px-1 text-center text-[10px] font-black leading-5 text-accent-foreground">
            {count > 99 ? "99+" : count}
          </span>
        ) : null}
      </span>
      <span className="hidden max-w-[74px] truncate sm:block">{label}</span>
    </Link>
  );
}
