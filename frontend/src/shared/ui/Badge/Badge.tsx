import * as React from "react";

import { cn } from "../../lib/cn";

const badgeVariantClass = {
  neutral: "border-border bg-muted text-foreground",
  primary: "border-primary-border bg-primary-soft text-primary-active",
  success: "border-success-border bg-success-soft text-success",
  warning: "border-warning-border bg-warning-soft text-warning",
  danger: "border-danger-border bg-danger-soft text-danger",
  info: "border-info-border bg-info-soft text-info",
  accent: "border-transparent bg-accent-soft text-accent-foreground",
  admin: "border-admin-accent/30 bg-admin-sidebar text-admin-foreground",
} as const;

const badgeSizeClass = {
  sm: "min-h-5 px-2 text-[11px]",
  md: "min-h-6 px-2.5 text-caption",
  lg: "min-h-7 px-3 text-body-sm",
} as const;

export type BadgeVariant = keyof typeof badgeVariantClass;
export type BadgeSize = keyof typeof badgeSizeClass;

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
}

export function Badge({ className, variant = "neutral", size = "md", dot = false, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-sm border font-semibold leading-none",
        badgeVariantClass[variant],
        badgeSizeClass[size],
        className,
      )}
      {...props}
    >
      {dot ? <span className="h-1.5 w-1.5 rounded-full bg-current" /> : null}
      {children}
    </span>
  );
}
