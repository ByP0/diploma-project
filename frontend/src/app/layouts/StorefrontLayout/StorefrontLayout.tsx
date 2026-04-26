import * as React from "react";

import { CatalogSidebar, SecondaryNavigation, StoreFooter, StoreHeader } from "../../../widgets";
import { cn } from "../../../shared/lib/cn";
import { Button } from "../../../shared/ui/Button";
import { mergeNavigationData } from "./navigation-data";
import { XIcon } from "./icons";
import type { StorefrontLayoutProps } from "./types";

export function StorefrontLayout({
  children,
  navigation: navigationOverrides,
  user,
  counters,
  searchQuery,
  defaultSearchQuery,
  onSearchQueryChange,
  onSearchSubmit,
  LinkComponent,
  className,
}: StorefrontLayoutProps) {
  const [catalogOpen, setCatalogOpen] = React.useState(false);
  const navigation = React.useMemo(() => mergeNavigationData(navigationOverrides), [navigationOverrides]);

  const closeCatalog = React.useCallback(() => setCatalogOpen(false), []);
  const toggleCatalog = React.useCallback(() => setCatalogOpen((open) => !open), []);

  return (
    <div className={cn("min-h-screen bg-background text-foreground", className)}>
      <a
        className="focus-ring sr-only fixed left-4 top-4 z-[var(--z-toast)] rounded-md bg-surface px-4 py-2 font-semibold text-foreground shadow-card focus:not-sr-only"
        href="#main-content"
      >
        Перейти к содержимому
      </a>

      <StoreHeader
        counters={counters}
        defaultSearchQuery={defaultSearchQuery}
        LinkComponent={LinkComponent}
        onCatalogToggle={toggleCatalog}
        onSearchQueryChange={onSearchQueryChange}
        onSearchSubmit={onSearchSubmit}
        searchQuery={searchQuery}
        user={user}
      />

      <SecondaryNavigation
        breadcrumbs={navigation.breadcrumbs}
        LinkComponent={LinkComponent}
        quickCategories={navigation.quickCategories}
      />

      <div className="store-container grid gap-6 py-6 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)]">
        <div className="hidden lg:block">
          <CatalogSidebar
            brands={navigation.brands}
            categories={navigation.catalogCategories}
            farmerLinks={navigation.farmerLinks}
            LinkComponent={LinkComponent}
            newLinks={navigation.newLinks}
            sticky
          />
        </div>

        <main className="min-w-0" id="main-content">
          {children}
        </main>
      </div>

      <StoreFooter
        columns={navigation.footerColumns}
        LinkComponent={LinkComponent}
        socialLinks={navigation.socialLinks}
      />

      <MobileCatalogDrawer
        LinkComponent={LinkComponent}
        navigation={navigation}
        onClose={closeCatalog}
        open={catalogOpen}
      />
    </div>
  );
}

interface MobileCatalogDrawerProps {
  open: boolean;
  onClose: () => void;
  navigation: ReturnType<typeof mergeNavigationData>;
  LinkComponent: StorefrontLayoutProps["LinkComponent"];
}

function MobileCatalogDrawer({ open, onClose, navigation, LinkComponent }: MobileCatalogDrawerProps) {
  React.useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[var(--z-modal)]" role="presentation">
      <button
        aria-label="Закрыть каталог"
        className="absolute inset-0 bg-foreground/[0.35] backdrop-blur-sm"
        onClick={onClose}
        type="button"
      />
      <section
        aria-labelledby="mobile-catalog-title"
        aria-modal="true"
        className="absolute inset-y-0 left-0 flex w-[min(380px,92vw)] flex-col overflow-hidden bg-surface shadow-modal animate-modal-in"
        role="dialog"
      >
        <header className="flex min-h-[64px] items-center justify-between border-b border-border px-4">
          <h2 className="text-h4" id="mobile-catalog-title">
            Каталог
          </h2>
          <Button aria-label="Закрыть каталог" onClick={onClose} size="iconMd" variant="ghost">
            <XIcon />
          </Button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto p-4 scrollbar-soft">
          <CatalogSidebar
            brands={navigation.brands}
            categories={navigation.catalogCategories}
            farmerLinks={navigation.farmerLinks}
            LinkComponent={LinkComponent}
            newLinks={navigation.newLinks}
            onNavigate={onClose}
          />
        </div>
      </section>
    </div>
  );
}
