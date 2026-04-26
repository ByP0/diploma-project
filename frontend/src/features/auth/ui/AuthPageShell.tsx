import type * as React from "react";

import { resolveLinkComponent } from "../../../app/layouts/StorefrontLayout/link";
import type { StorefrontLinkComponent } from "../../../app/layouts";
import { cn } from "../../../shared/lib/cn";
import { Card } from "../../../shared/ui/Card";

export interface AuthPageShellProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  LinkComponent?: StorefrontLinkComponent;
  className?: string;
}

export function AuthPageShell({
  title,
  description,
  children,
  footer,
  LinkComponent,
  className,
}: AuthPageShellProps) {
  const Link = resolveLinkComponent(LinkComponent);

  return (
    <main className={cn("grid min-h-[calc(100vh-160px)] place-items-center bg-background px-4 py-10", className)}>
      <section className="w-full max-w-[480px]">
        <div className="mb-5 text-center">
          <Link className="inline-flex items-center gap-2 text-foreground hover:text-foreground" href="/">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-primary text-lg font-black text-primary-foreground">
              G
            </span>
            <span className="text-left">
              <span className="block font-display text-[20px] font-black">GreenMart</span>
              <span className="block text-caption font-semibold text-primary-active">premium grocery</span>
            </span>
          </Link>
        </div>

        <Card className="p-5 shadow-card" variant="surface">
          <header>
            <h1 className="text-h2 text-foreground">{title}</h1>
            {description ? <p className="mt-2 text-body-sm text-muted-foreground">{description}</p> : null}
          </header>
          <div className="mt-5">{children}</div>
          {footer ? <footer className="mt-5 border-t border-border pt-4 text-body-sm text-muted-foreground">{footer}</footer> : null}
        </Card>
      </section>
    </main>
  );
}

export function FormAlert({
  children,
  variant = "danger",
}: {
  children: React.ReactNode;
  variant?: "danger" | "success" | "warning";
}) {
  const className = {
    danger: "border-danger-border bg-danger-soft text-danger",
    success: "border-success-border bg-success-soft text-success",
    warning: "border-warning-border bg-warning-soft text-warning",
  }[variant];

  return (
    <p className={cn("rounded-md border px-3 py-2 text-body-sm font-semibold", className)} role="alert">
      {children}
    </p>
  );
}
