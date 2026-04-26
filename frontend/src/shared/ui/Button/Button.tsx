import * as React from "react";

import { cn } from "../../lib/cn";

const variantClass = {
  primary:
    "bg-primary text-primary-foreground shadow-sm hover:bg-primary-hover active:bg-primary-active disabled:bg-primary/[0.55]",
  secondary:
    "border border-border-strong bg-surface text-foreground shadow-sm hover:border-primary-border hover:bg-primary-soft hover:text-primary-active",
  outline:
    "border border-border-strong bg-transparent text-foreground hover:border-primary hover:bg-primary-soft hover:text-primary-active",
  ghost: "bg-transparent text-foreground hover:bg-muted hover:text-primary-active",
  soft: "bg-primary-soft text-primary-active hover:bg-primary-border/40",
  danger: "bg-danger text-danger-foreground shadow-sm hover:bg-danger/90",
  admin: "bg-admin-sidebar text-admin-foreground shadow-sm hover:bg-admin-sidebar/[0.92]",
  link: "h-auto min-h-0 bg-transparent px-0 py-0 text-primary underline-offset-4 hover:text-primary-hover hover:underline",
} as const;

const sizeClass = {
  sm: "min-h-[var(--control-height-sm)] px-3 text-button-sm",
  md: "min-h-[var(--control-height-md)] px-4 text-button",
  lg: "min-h-[var(--control-height-lg)] px-5 text-button-lg",
  iconSm: "h-[var(--control-height-sm)] w-[var(--control-height-sm)] p-0",
  iconMd: "h-[var(--control-height-md)] w-[var(--control-height-md)] p-0",
  iconLg: "h-[var(--control-height-lg)] w-[var(--control-height-lg)] p-0",
} as const;

export type ButtonVariant = keyof typeof variantClass;
export type ButtonSize = keyof typeof sizeClass;

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      children,
      variant = "primary",
      size = "md",
      fullWidth = false,
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      type = "button",
      ...props
    },
    ref,
  ) => (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        "focus-ring inline-flex items-center justify-center gap-2 rounded-md font-semibold transition duration-150 ease-product",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-70",
        variantClass[variant],
        sizeClass[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    >
      {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" /> : leftIcon}
      {children}
      {!loading && rightIcon}
    </button>
  ),
);

Button.displayName = "Button";
